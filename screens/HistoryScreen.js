/**
 * HistoryScreen.js
 * Chronological log of all triggered alerts.
 */

import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { colors } from "../theme";
import { getAlertHistory } from "../services/api";

export default function HistoryScreen() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await getAlertHistory();
      setHistory(data);
    } catch (e) {
      Alert.alert("Error", "Could not load history. Is the backend running?");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primaryLight} />
      </View>
    );
  }

  // Group alerts by date
  const grouped = groupByDate(history);

  return (
    <View style={styles.container}>
      <FlatList
        data={grouped}
        keyExtractor={(item) => item.date}
        renderItem={({ item }) => (
          <View>
            <Text style={styles.dateHeader}>{item.date}</Text>
            {item.alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} />
            ))}
          </View>
        )}
        contentContainerStyle={
          grouped.length === 0 ? styles.emptyContainer : styles.listContent
        }
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={colors.primaryLight}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>◷</Text>
            <Text style={styles.emptyTitle}>No alerts yet</Text>
            <Text style={styles.emptySubtitle}>
              Triggered alerts will appear here
            </Text>
          </View>
        }
      />
    </View>
  );
}

function AlertRow({ alert }) {
  const time = new Date(alert.triggered_at).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <View style={styles.alertRow}>
      {/* Left accent line */}
      <View style={styles.accentLine} />

      <View style={styles.alertContent}>
        <View style={styles.alertHeader}>
          <Text style={styles.alertInstrument}>{alert.instrument}</Text>
          <Text style={styles.alertTime}>{time}</Text>
        </View>
        <Text style={styles.alertDescription}>{alert.description}</Text>
        <Text style={styles.alertPrice}>
          Triggered at ₹{Number(alert.trigger_price).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </Text>
      </View>
    </View>
  );
}

function groupByDate(alerts) {
  const map = {};
  for (const alert of alerts) {
    const date = new Date(alert.triggered_at).toLocaleDateString("en-IN", {
      weekday: "long",
      day: "numeric",
      month: "short",
      year: "numeric",
    });
    if (!map[date]) map[date] = [];
    map[date].push(alert);
  }
  return Object.entries(map).map(([date, alerts]) => ({ date, alerts }));
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  centered:  { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },

  listContent:    { padding: 16, paddingBottom: 32 },
  emptyContainer: { flex: 1 },
  emptyState: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 40,
    marginTop: 80,
  },
  emptyIcon:     { fontSize: 36, color: colors.textFaint, marginBottom: 12 },
  emptyTitle:    { color: colors.text, fontSize: 18, fontWeight: "600", marginBottom: 6 },
  emptySubtitle: { color: colors.textMuted, fontSize: 14, textAlign: "center" },

  dateHeader: {
    color: colors.textFaint,
    fontSize: 11,
    letterSpacing: 1.5,
    marginTop: 16,
    marginBottom: 8,
    textTransform: "uppercase",
  },

  alertRow: {
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    marginBottom: 8,
    overflow: "hidden",
  },
  accentLine: {
    width: 3,
    backgroundColor: colors.warning,
  },
  alertContent: { flex: 1, padding: 14 },

  alertHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  alertInstrument: { color: colors.primaryLight, fontSize: 13, fontWeight: "600" },
  alertTime:       { color: colors.textFaint, fontSize: 12 },
  alertDescription:{ color: colors.text, fontSize: 14, marginBottom: 4, lineHeight: 20 },
  alertPrice:      { color: colors.warning, fontSize: 12 },
});
