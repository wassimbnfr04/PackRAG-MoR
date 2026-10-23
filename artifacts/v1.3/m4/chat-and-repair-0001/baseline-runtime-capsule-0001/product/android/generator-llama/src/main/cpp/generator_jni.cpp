#include <jni.h>
#include <llama.h>
#include <atomic>
#include <chrono>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Clock = std::chrono::steady_clock;
static double ms(Clock::time_point from, Clock::time_point to) {
    return std::chrono::duration<double, std::milli>(to - from).count();
}
struct Session {
    llama_model * model = nullptr;
    llama_context * context = nullptr;
    std::mutex mutex;
    std::atomic<bool> cancelled{false};
    ~Session() { if (context) llama_free(context); if (model) llama_model_free(model); }
};
static std::mutex handles_mutex;
static std::unordered_map<jlong, std::shared_ptr<Session>> handles;
static std::atomic<jlong> next_handle{1};
static std::once_flag backend_once;
static std::shared_ptr<Session> session(jlong handle) {
    std::lock_guard<std::mutex> lock(handles_mutex);
    auto found = handles.find(handle);
    if (found == handles.end()) throw std::runtime_error("Generator is closed");
    return found->second;
}
static void error(JNIEnv * env, const std::exception & failure) {
    env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), failure.what());
}
static std::string bytes(JNIEnv * env, jbyteArray array) {
    auto size = env->GetArrayLength(array);
    if (size > 1024 * 1024) throw std::runtime_error("Input exceeds native byte bound");
    std::string value(size, '\0');
    env->GetByteArrayRegion(array, 0, size, reinterpret_cast<jbyte *>(value.data()));
    return value;
}
static jbyteArray byte_array(JNIEnv * env, const std::string & value) {
    auto result = env->NewByteArray(value.size());
    env->SetByteArrayRegion(result, 0, value.size(), reinterpret_cast<const jbyte *>(value.data()));
    return result;
}
static jintArray int_array(JNIEnv * env, const std::vector<llama_token> & ids) {
    auto result = env->NewIntArray(ids.size());
    env->SetIntArrayRegion(result, 0, ids.size(), ids.data());
    return result;
}
static bool aborted(void * data) { return static_cast<Session *>(data)->cancelled.load(); }
static std::string metadata(llama_model * model, const char * key) {
    std::vector<char> buffer(256);
    auto length = llama_model_meta_val_str(model, key, buffer.data(), buffer.size());
    if (length < 0 || length >= static_cast<int>(buffer.size())) throw std::runtime_error("Invalid required GGUF metadata");
    return std::string(buffer.data(), length);
}

extern "C" JNIEXPORT jlong JNICALL
Java_org_packrag_generator_LlamaNative_load(JNIEnv * env, jobject, jbyteArray file, jboolean vocabulary_only, jint threads) {
    try {
        if (threads < 1 || threads > 8) throw std::runtime_error("Invalid CPU thread count");
        std::call_once(backend_once, [] {
            llama_log_set([](ggml_log_level, const char *, void *) {}, nullptr);
            llama_backend_init();
        });
        auto state = std::make_shared<Session>();
        auto path = bytes(env, file);
        if (path.find('\0') != std::string::npos) throw std::runtime_error("Invalid model path");
        auto params = llama_model_default_params();
        params.n_gpu_layers = 0; params.vocab_only = vocabulary_only;
        params.load_mode = LLAMA_LOAD_MODE_MMAP; params.lazy_mode = LLAMA_LAZY_MODE_OFF;
        state->model = llama_model_load_from_file(path.c_str(), params);
        if (!state->model) throw std::runtime_error("Pinned LFM model load failed");
        if (metadata(state->model, "general.architecture") != "lfm2" || metadata(state->model, "general.file_type") != "2")
            throw std::runtime_error("Unexpected GGUF architecture or quantization");
        if (!vocabulary_only) {
            if (llama_model_n_params(state->model) != 2697198592ULL) throw std::runtime_error("Unexpected parameter count");
            auto context = llama_context_default_params();
            context.n_ctx = 2048; context.n_seq_max = 1; context.n_batch = 256; context.n_ubatch = 128;
            context.n_threads = threads; context.n_threads_batch = threads;
            context.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_DISABLED;
            context.offload_kqv = false; context.op_offload = false;
            context.abort_callback = aborted; context.abort_callback_data = state.get();
            state->context = llama_init_from_model(state->model, context);
            if (!state->context || llama_n_ctx(state->context) != 2048) throw std::runtime_error("LFM context creation failed");
        }
        std::lock_guard<std::mutex> lock(handles_mutex);
        auto handle = next_handle.fetch_add(1); handles.emplace(handle, state); return handle;
    } catch (const std::exception & failure) { error(env, failure); return 0; }
}

extern "C" JNIEXPORT jintArray JNICALL
Java_org_packrag_generator_LlamaNative_tokenize(JNIEnv * env, jobject, jlong handle, jbyteArray text, jboolean special) {
    try {
        auto state = session(handle); std::lock_guard<std::mutex> lock(state->mutex);
        auto input = bytes(env, text); auto vocab = llama_model_get_vocab(state->model);
        auto count = llama_tokenize(vocab, input.data(), input.size(), nullptr, 0, special, true);
        if (count == INT32_MIN) throw std::runtime_error("Tokenizer size overflow");
        if (count > 0) throw std::runtime_error("Unexpected tokenizer sizing result");
        std::vector<llama_token> ids(-count);
        auto result = llama_tokenize(vocab, input.data(), input.size(), ids.data(), ids.size(), special, true);
        if (result < 0 || result != static_cast<int>(ids.size())) throw std::runtime_error("Tokenizer result mismatch");
        return int_array(env, ids);
    } catch (const std::exception & failure) { error(env, failure); return nullptr; }
}

extern "C" JNIEXPORT void JNICALL
Java_org_packrag_generator_LlamaNative_begin(JNIEnv * env, jobject, jlong handle) {
    try { auto state = session(handle); std::lock_guard<std::mutex> lock(state->mutex); state->cancelled.store(false); }
    catch (const std::exception & failure) { error(env, failure); }
}
extern "C" JNIEXPORT void JNICALL
Java_org_packrag_generator_LlamaNative_cancel(JNIEnv *, jobject, jlong handle) {
    std::lock_guard<std::mutex> lock(handles_mutex);
    auto found = handles.find(handle); if (found != handles.end()) found->second->cancelled.store(true);
}
extern "C" JNIEXPORT void JNICALL
Java_org_packrag_generator_LlamaNative_close(JNIEnv *, jobject, jlong handle) {
    std::lock_guard<std::mutex> lock(handles_mutex);
    auto found = handles.find(handle);
    if (found != handles.end()) { found->second->cancelled.store(true); handles.erase(found); }
}

struct Batch {
    llama_batch value;
    explicit Batch(int size) : value(llama_batch_init(size, 0, 1)) {}
    ~Batch() { llama_batch_free(value); }
};
extern "C" JNIEXPORT jobject JNICALL
Java_org_packrag_generator_LlamaNative_generate(JNIEnv * env, jobject, jlong handle, jintArray prompt, jint maximum) {
    try {
        auto state = session(handle); std::lock_guard<std::mutex> lock(state->mutex);
        auto size = env->GetArrayLength(prompt);
        if (!state->context || size < 1 || size > 1536 || maximum < 1 || maximum > 512 || size + maximum > 2048)
            throw std::runtime_error("Invalid generation context/budget");
        std::vector<llama_token> input(size); env->GetIntArrayRegion(prompt, 0, size, input.data());
        auto vocab = llama_model_get_vocab(state->model);
        for (auto id : input) if (id < 0 || id >= llama_vocab_n_tokens(vocab)) throw std::runtime_error("Invalid prompt token");
        llama_memory_clear(llama_get_memory(state->context), true);
        const auto started = Clock::now(); auto prefilled = started; auto first = started;
        bool has_first = false; int stop = 1;
        Batch batch(256);
        for (int offset = 0; offset < size && !state->cancelled.load(); offset += 256) {
            batch.value.n_tokens = std::min(256, size - offset);
            for (int i = 0; i < batch.value.n_tokens; ++i) {
                batch.value.token[i] = input[offset + i]; batch.value.pos[i] = offset + i;
                batch.value.n_seq_id[i] = 1; batch.value.seq_id[i][0] = 0;
                batch.value.logits[i] = offset + i == size - 1;
            }
            auto result = llama_decode(state->context, batch.value);
            if (result != 0 && !state->cancelled.load()) throw std::runtime_error("LFM prefill decode failed");
        }
        prefilled = Clock::now();
        std::unique_ptr<llama_sampler, decltype(&llama_sampler_free)> sampler(llama_sampler_init_greedy(), llama_sampler_free);
        std::vector<llama_token> emitted; std::string output;
        for (int i = 0; i < maximum && !state->cancelled.load(); ++i) {
            auto token = llama_sampler_sample(sampler.get(), state->context, -1);
            if (!has_first) { first = Clock::now(); has_first = true; }
            emitted.push_back(token);
            if (llama_vocab_is_eog(vocab, token)) { stop = 0; break; }
            std::vector<char> piece(256);
            auto length = llama_token_to_piece(vocab, token, piece.data(), piece.size(), 0, true);
            if (length < 0) { piece.resize(-length); length = llama_token_to_piece(vocab, token, piece.data(), piece.size(), 0, true); }
            if (length < 0) throw std::runtime_error("Token piece conversion failed");
            output.append(piece.data(), length);
            // The final token need not be decoded when the generated cap is reached.
            if (i + 1 == maximum) break;
            batch.value.n_tokens = 1; batch.value.token[0] = token; batch.value.pos[0] = size + i;
            batch.value.n_seq_id[0] = 1; batch.value.seq_id[0][0] = 0; batch.value.logits[0] = true;
            auto result = llama_decode(state->context, batch.value);
            if (result != 0 && !state->cancelled.load()) throw std::runtime_error("LFM token decode failed");
        }
        if (state->cancelled.load()) stop = 2;
        const auto finished = Clock::now();
        auto result_class = env->FindClass("org/packrag/generator/NativeEmission");
        auto constructor = env->GetMethodID(result_class, "<init>", "([B[IIDDDD)V");
        return env->NewObject(result_class, constructor, byte_array(env, output), int_array(env, emitted), stop,
            ms(started, prefilled), ms(prefilled, finished), has_first ? ms(started, first) : -1.0, ms(started, finished));
    } catch (const std::exception & failure) { error(env, failure); return nullptr; }
}
