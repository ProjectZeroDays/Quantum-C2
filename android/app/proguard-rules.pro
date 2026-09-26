# QUANTUM-CLI Android — ProGuard/R8 rules

# NanoHTTPD (reflection-free, but keep server entry points under optimization)
-keep class fi.iki.elonen.** { *; }

# MediaPipe GenAI LLM Inference loads its native pipeline via JNI
-keep class com.google.mediapipe.** { *; }
-keep class com.google.mediapipe.tasks.genai.** { *; }

# org.json ships with the platform; Tink is used by security-crypto
-keep class com.google.crypto.tink.** { *; }

# Kotlin coroutines debug metadata
-dontwarn kotlinx.coroutines.debug.**

# Strip noisy MediaPipe/Tink logging from release builds
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
}
