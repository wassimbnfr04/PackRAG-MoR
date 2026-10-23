# Failed inspection harness, preserved

The read-only inspection successfully captured the APK entry list, packaged
manifest and permissions and checked no INTERNET/public-store equality. It
then raised KeyError because the harness guessed the native entry name
lib/arm64-v8a/libpackrag_llama.so, which does not exist. This is a harness path
error, not evidence of a missing native runtime. No aggregate PASS is recorded.
Use the entry name actually observed in entry-list.txt in a new versioned
inspection. The original files and failed command output remain unchanged.
