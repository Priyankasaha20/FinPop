/**
 * notifications.js
 * Registers for Expo push notifications and wires up foreground handlers.
 *
 * Flow:
 *  1. App starts → registerForPushNotifications() called from App.js
 *  2. Token is sent to backend via registerPushToken()
 *  3. Backend uses the token to push alerts via Expo's push service
 *  4. Foreground handler shows an in-app banner when the app is open
 */

import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import Constants from "expo-constants";
import { Platform, Alert } from "react-native";
import { registerPushToken } from "./api";

// How to handle notifications when the app is in the foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * SDK 54+: Remote push notifications require a Development Build.
 * Expo Go no longer supports them. Run:
 *   npx expo install expo-dev-client
 *   eas build --profile development --platform android
 * Then open the dev build APK instead of Expo Go.
 *
 * This function safely skips push registration when running in Expo Go,
 * so the rest of the app still works during development.
 */
export async function registerForPushNotifications() {
  if (!Device.isDevice) {
    console.warn("Push notifications require a physical device.");
    return null;
  }

  // Detect if running inside Expo Go (not a dev build)
  const isExpoGo = Constants.appOwnership === "expo";
  if (isExpoGo) {
    console.warn(
      "⚠️  Push notifications are not supported in Expo Go (SDK 53+).\n" +
        "Build a development build with: npx expo run:android\n" +
        "or: eas build --profile development --platform android",
    );
    // Return null gracefully — app still works, just no push
    return null;
  }

  // --- From here on: only runs in a real dev/production build ---

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    Alert.alert(
      "Notifications disabled",
      "Enable notifications in Settings to receive trade alerts.",
    );
    return null;
  }

  // Android notification channel
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("trade-alerts", {
      name: "Trade Alerts",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#1d4ed8",
      sound: "default",
    });
  }

  // Get the Expo push token
  // projectId comes from your EAS project — find it at expo.dev or in eas.json
  const projectId =
    Constants.expoConfig?.extra?.eas?.projectId ?? "YOUR_EAS_PROJECT_ID"; // fallback: paste from expo.dev

  const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
  const token = tokenData.data;
  console.log("Expo push token:", token);

  try {
    await registerPushToken(token);
  } catch (e) {
    console.warn("Could not register push token with backend:", e.message);
  }

  return token;
}

/**
 * Subscribe to foreground notification events.
 * Returns a cleanup function — call it in useEffect return.
 *
 * Usage in App.js:
 *   useEffect(() => {
 *     return subscribeToNotifications((n) => console.log(n));
 *   }, []);
 */
export function subscribeToNotifications(onReceive, onResponse) {
  const receiveSub = Notifications.addNotificationReceivedListener(
    (notification) => {
      onReceive?.(notification);
    },
  );

  // Fired when user taps the notification
  const responseSub = Notifications.addNotificationResponseReceivedListener(
    (response) => {
      onResponse?.(response);
    },
  );

  return () => {
    receiveSub.remove();
    responseSub.remove();
  };
}
