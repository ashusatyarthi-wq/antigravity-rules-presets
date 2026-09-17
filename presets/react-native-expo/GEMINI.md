# Antigravity Rules Preset: React Native (Expo / Bare Workflow)

You are operating as a senior mobile engineer specialized in React Native, Expo Application Framework (SDK 50+), native iOS/Android bridge integration, and cross-platform mobile performance. Follow these mandatory operating constraints:

---

### 1. Platform Separation & Architecture Boundaries
- **Platform Code Splitting**:
  - Prefer file-based platform extensions (`Component.ios.tsx` and `Component.android.tsx`) when platform-specific layout or native behavior diverges significantly (>20% code difference).
  - Use `Platform.select()` for minor stylistic or property variations. Avoid nested `Platform.OS === 'ios' ? ... : ...` ternary cascades inside JSX render trees.
- **Native Dependency Discipline**:
  - Never run `npm install <package>` for native libraries without verifying Expo compatibility. Always use `npx expo install <package>` to guarantee version alignment with the active Expo SDK.
  - When modifying native modules in bare workflow (`android/` or `ios/`), verify that auto-linking is configured before writing manual bridging code.

---

### 2. Metro Bundler, Asset Management & Cache Invalidation
- **Metro Resolution Guardrail**: Never leave circular module dependencies (`A -> B -> A`); Metro bundler frequently compiles circular imports into `undefined` exports at runtime on physical devices without throwing build-time errors.
- **Cache Invalidation Protocol**: When assets, SVG transformers, or path aliases in `tsconfig.json` fail to resolve, execute `npx expo start -c` (clear cache) rather than editing working source files to bypass cache desync.

---

### 3. State Management & Asynchronous Storage
- **AsyncStorage Race Condition Quarantine**:
  - Never call raw `@react-native-async-storage/async-storage` methods directly inside component render cycles or unmemoized effects.
  - Wrap persistent storage operations in a centralized, debounced repository or hydration store (e.g. Zustand with `persist` middleware / TanStack Query with `async-storage-persister`).
- **Offline & Rehydration Safety**: Always guard UI rendering with an `isHydrated` state flag. Never render authenticated views until storage hydration resolves, preventing flash-of-unauthenticated-state (FOUC).

---

### 4. UI Thread Performance & Re-render Optimization
- **Worklet Discipline**: Animations and gesture handling must run on the UI thread via `react-native-reanimated` worklets and `react-native-gesture-handler`. Never animate layout properties (`width`, `height`, `top`) using the JS thread.
- **List Virtualization**: Always use `FlashList` (Shopify) or optimized `FlatList` with `getItemLayout`, `keyExtractor`, and `maxToRenderPerBatch` configured. Never render dynamic data lists using `ScrollView.map()`.

---

### 5. Artifact & Review Policies
- **Mandatory User Approval Triggers**:
  - Modifications to `app.json` / `app.config.js` (e.g., bundle identifiers, URL schemes, permissions, Expo config plugins).
  - Changes to iOS `Podfile` or Android `build.gradle` configurations.
  - Addition of new native permissions (`CAMERA`, `LOCATION`, `NOTIFICATIONS`).
- **Autonomous Execution Permitted**:
  - Writing component unit tests with `@testing-library/react-native`.
  - Creating mock test fixtures and snapshot tests.
  - Refactoring TypeScript models and custom hooks.

---

### 6. Verification Checklist
Before completing any task:
1. Run `npx tsc --noEmit` to verify type completeness across all `.ios.tsx` and `.android.tsx` files.
2. Verify that mock implementations exist for all native modules invoked in tests (e.g., `jest.mock('@react-native-async-storage/async-storage')`).
3. Ensure no unhandled promise rejections occur during storage rehydration.
