# Rationale: React Native / Expo Preset

This document explains **why** each rule in `GEMINI.md` exists and the specific cross-platform mobile failures, build breakages, and performance bottlenecks it prevents.

---

### 1. The `npx expo install` vs `npm install` Mandate
- **Failure Prevented: Native SDK Incompatibility & Crash on Launch**
- **The Problem**: In Expo and React Native, native libraries (e.g. `react-native-screens`, `react-native-reanimated`, `expo-camera`) require precise C++ / Java / Objective-C bindings tied to the specific React Native runtime version. When an AI agent runs `npm install react-native-reanimated`, npm installs the latest major release (e.g. v3.16), which may be incompatible with the current project's Expo SDK (e.g. SDK 50 expecting v3.6). This results in catastrophic native build crashes (`Undefined symbol` / `NoSuchMethodError`) or immediate crash-on-launch on physical devices.
- **The Hardened Fix**: Mandatory use of `npx expo install`. Expo CLI queries its curated compatibility matrix and installs the exact compatible version for the active SDK.

---

### 2. Platform Extensions (`.ios.tsx` / `.android.tsx`) vs JSX Ternary Hell
- **Failure Prevented: Dead Code Bloat & Native Component Crashes**
- **The Problem**: When code relies on complex ternary logic inside components (e.g., `<View>{Platform.OS === 'ios' ? <IosOnlyPicker /> : <AndroidPicker />}</View>`), Metro bundler is forced to package *both* native modules into both platforms. If one platform imports a library with native symbols unavailable on the other (e.g., iOS Apple Pay or Android Jetpack Compose widgets), the application crashes at runtime on the opposing OS.
- **The Hardened Fix**: File-based platform extensions (`Component.ios.tsx` and `Component.android.tsx`). Metro bundles *only* the matching file for the target platform during compilation, keeping bundles lean and eliminating cross-platform crash vectors.

---

### 3. Asynchronous Storage Hydration Guardrails
- **Failure Prevented: Flash of Unauthenticated Content (FOUC) & Token Desync**
- **The Problem**: Unlike web `localStorage` (which is synchronous), React Native's `AsyncStorage` is an asynchronous bridge to SQLite or file storage. Naive agents read auth tokens in an unmemoized `useEffect` and immediately render public/login screens while waiting for the promise to resolve. Users experience a jarring screen flicker, and race conditions trigger accidental sign-out redirects.
- **The Hardened Fix**: Mandatory hydration guards (`isHydrated` state flag) and centralized store hydration. Render tree mounting is blocked until local storage deserialization completes cleanly.

---

### 4. UI Thread Worklets vs JS Thread Animations
- **Failure Prevented: 15 FPS Jitter and Frame Drops during Touch Gestures**
- **The Problem**: Animating layout dimensions (`height`, `width`, `padding`) or handling high-frequency pan gestures on the JavaScript thread causes extreme frame drops whenever the JS bridge is busy processing network requests or business logic.
- **The Hardened Fix**: Enforcing `react-native-reanimated` worklets that execute directly on the native UI thread at 60/120 FPS without bridge serialization.
