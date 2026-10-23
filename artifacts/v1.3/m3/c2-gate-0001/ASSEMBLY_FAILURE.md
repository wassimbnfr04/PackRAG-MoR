# Evidence-summary assembly failure

The one-off summary script asserted that the APK contained libpackrag_llama.so. The real JNI library is libpackrag_jni.so, so this summary attempt stopped before writing gate.json. This is a filename error in assembling evidence, not a failed product/device gate. All prior raw test results remain unchanged. Corrected assembly uses a new c2-gate-0002 output location and checks the actual packaged library.
