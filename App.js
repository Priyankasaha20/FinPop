/**
 * App.js — Root entry point
 * Sets up:
 *  - Bottom tab navigation (Rules · Add Rule · History)
 *  - Push notification registration on first launch
 *  - Foreground notification listener
 */

import React, { useEffect } from "react";
import { StatusBar, Alert } from "react-native";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import RulesScreen   from "./screens/RulesScreen";
import AddRuleScreen from "./screens/AddRuleScreen";
import HistoryScreen from "./screens/HistoryScreen";

import {
  registerForPushNotifications,
  subscribeToNotifications,
} from "./services/notifications";
import { colors } from "./theme";

const Tab = createBottomTabNavigator();

// Custom nav theme — keeps our dark background throughout
const NavTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background:  colors.bg,
    card:        colors.surface,
    border:      colors.border,
    text:        colors.text,
    primary:     colors.primaryLight,
  },
};

export default function App() {
  useEffect(() => {
    // Register for push notifications on mount
    registerForPushNotifications().catch(console.warn);

    // Listen for notifications while app is open
    const unsub = subscribeToNotifications(
      (notification) => {
        // Foreground notification received — show an in-app alert
        const { title, body } = notification.request.content;
        Alert.alert(title ?? "🚨 Alert", body ?? "");
      },
      (response) => {
        // User tapped a notification — could navigate to History tab here
        console.log("Notification tapped:", response.notification.request.identifier);
      }
    );

    return unsub;
  }, []);

  return (
    <NavigationContainer theme={NavTheme}>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarStyle: {
            backgroundColor: colors.surface,
            borderTopColor:  colors.border,
            paddingBottom:   6,
            height:          58,
          },
          tabBarActiveTintColor:   colors.primaryLight,
          tabBarInactiveTintColor: colors.textFaint,
          tabBarLabelStyle: { fontSize: 11, letterSpacing: 0.5 },
          headerStyle:       { backgroundColor: colors.surface },
          headerTintColor:   colors.text,
          headerTitleStyle:  { fontSize: 14, letterSpacing: 1 },
          tabBarIcon: ({ color, size }) => {
            const icons = {
              Rules:     "◈",
              "Add Rule":"＋",
              History:   "◷",
            };
            return (
              <TabIcon icon={icons[route.name] ?? "·"} color={color} />
            );
          },
        })}
      >
        <Tab.Screen
          name="Rules"
          component={RulesScreen}
          options={{ title: "ACTIVE RULES" }}
        />
        <Tab.Screen
          name="Add Rule"
          component={AddRuleScreen}
          options={{ title: "ADD RULE" }}
        />
        <Tab.Screen
          name="History"
          component={HistoryScreen}
          options={{ title: "ALERT HISTORY" }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

function TabIcon({ icon, color }) {
  const { Text } = require("react-native");
  return <Text style={{ fontSize: 18, color }}>{icon}</Text>;
}
