# Before & After: React Native Authentication & Persistent Storage

### Scenario Overview
A developer prompts an AI agent: *"Persist the user's session token locally with AsyncStorage and display an authenticated profile card with an animated slide-in transition."*

---

### ❌ The Naive Implementation (Unconstrained Agent)

```tsx
// components/ProfileCard.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, Animated, Platform } from 'react-native';
// 🚨 Installed latest incompatible version via raw npm install
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ProfileCard() {
  const [token, setToken] = useState<string | null>(null);
  // 🚨 JS-thread animation state causing frame drops
  const slideAnim = new Animated.Value(0);

  useEffect(() => {
    // 🚨 Unhandled async race condition: component renders unauthenticated state first
    AsyncStorage.getItem('auth_token').then((val) => {
      setToken(val);
      Animated.timing(slideAnim, {
        toValue: 100,
        duration: 300,
        useNativeDriver: false, // 🚨 Animate on JS thread!
      }).start();
    });
  }, []);

  // 🚨 Terrible nested ternary and iOS-only import risking Android crash
  return (
    <Animated.View style={{ height: slideAnim }}>
      {token ? (
        <View>
          <Text>Authenticated Token: {token}</Text>
          {Platform.OS === 'ios' ? (
            <Text style={{ fontFamily: 'San Francisco' }}>iOS Exclusive UI</Text>
          ) : (
            <Text>Android Standard UI</Text>
          )}
        </View>
      ) : (
        <Text>Please Log In</Text> // 🚨 Flickers for 200ms on every app start!
      )}
    </Animated.View>
  );
}
```

#### What Broke & Why:
1. **Flash of Unauthenticated Content (FOUC)**: Users saw `"Please Log In"` flash on their screen for a third of a second every time the app opened before the async promise settled.
2. **UI Frame Drops**: Setting `useNativeDriver: false` forced animation calculations to travel back-and-forth across the React Native JavaScript bridge, dropping framerate to 20 FPS whenever data was being fetched.
3. **Android Build Warning / Font Crash**: Hardcoding iOS system font families directly in shared JSX caused font rendering anomalies on Android.

---

### ✅ The Hardened Implementation (Governed by Antigravity Preset)

```tsx
// stores/authStore.ts
import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthState {
  token: string | null;
  isHydrated: boolean;
  setToken: (token: string | null) => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  isHydrated: false,
  setToken: async (token) => {
    if (token) {
      await AsyncStorage.setItem('auth_token', token);
    } else {
      await AsyncStorage.removeItem('auth_token');
    }
    set({ token });
  },
  hydrate: async () => {
    try {
      const stored = await AsyncStorage.getItem('auth_token');
      set({ token: stored, isHydrated: true });
    } catch {
      set({ token: null, isHydrated: true });
    }
  },
}));
```

```tsx
// components/ProfileCard.tsx
import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withTiming } from 'react-native-reanimated';
import { useAuthStore } from '../stores/authStore';
import { PlatformSpecificBadge } from './PlatformSpecificBadge';

export function ProfileCard() {
  const { token, isHydrated } = useAuthStore();
  const heightProgress = useSharedValue(0);

  React.useEffect(() => {
    if (isHydrated && token) {
      // ✅ 60/120 FPS native UI thread animation via Reanimated worklet
      heightProgress.value = withTiming(100, { duration: 300 });
    }
  }, [isHydrated, token]);

  const animatedStyle = useAnimatedStyle(() => ({
    height: heightProgress.value,
  }));

  // ✅ Hydration guard eliminates flash of unauthenticated content
  if (!isHydrated) {
    return (
      <View className="p-4 items-center justify-center">
        <ActivityIndicator size="small" />
      </View>
    );
  }

  if (!token) {
    return (
      <View className="p-4">
        <Text className="text-gray-600">Please Log In</Text>
      </View>
    );
  }

  return (
    <Animated.View style={animatedStyle} className="p-4 bg-white rounded-lg shadow">
      <Text className="text-lg font-bold">Authenticated Profile</Text>
      {/* ✅ Clean cross-platform split via file-based extension */}
      <PlatformSpecificBadge />
    </Animated.View>
  );
}
```

```tsx
// components/PlatformSpecificBadge.ios.tsx
import { Text } from 'react-native';
export const PlatformSpecificBadge = () => <Text className="text-blue-600">iOS Verified</Text>;
```

```tsx
// components/PlatformSpecificBadge.android.tsx
import { Text } from 'react-native';
export const PlatformSpecificBadge = () => <Text className="text-green-600">Android Verified</Text>;
```

#### Incident Post-Mortem Avoided:
Eliminated FOUC via explicit storage hydration barriers, guaranteed 60 FPS animation execution on the native thread, and cleanly isolated OS-specific components via Metro's native file resolution extensions.
