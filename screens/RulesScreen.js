/**
 * RulesScreen.js
 * Lists all saved rules with status badges.
 * Swipe left to delete. Tap "Reset" on triggered rules to re-arm.
 */

import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { colors, STATUS, CONDITIONS, TIMEFRAMES } from "../theme";
import { getRules, deleteRule, resetRule, testRule } from "../services/api";

export default function RulesScreen({ navigation }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await getRules();
      setRules(data);
    } catch (e) {
      Alert.alert("Error", "Could not load rules. Is the backend running?");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Reload whenever this tab is focused
  useFocusEffect(useCallback(() => { load(); }, []));

  const handleDelete = (rule) => {
    Alert.alert(
      "Delete rule?",
      rule.description,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await deleteRule(rule.rule_id);
              setRules((r) => r.filter((x) => x.rule_id !== rule.rule_id));
            } catch (e) {
              Alert.alert("Error", e.message);
            }
          },
        },
      ]
    );
  };

  const handleReset = async (rule) => {
    try {
      await resetRule(rule.rule_id);
      setRules((r) =>
        r.map((x) =>
          x.rule_id === rule.rule_id
            ? { ...x, status: "active", triggered_at: null }
            : x
        )
      );
    } catch (e) {
      Alert.alert("Error", e.message);
    }
  };

  const handleTest = async (rule) => {
    try {
      const result = await testRule(rule.rule_id);
      Alert.alert(
        result.would_trigger ? "🚨 Would trigger!" : "✓ Would NOT trigger",
        `Current price: ₹${result.current_price?.toLocaleString("en-IN")}\n` +
        `Reference price: ₹${result.reference_price?.toLocaleString("en-IN")}`
      );
    } catch (e) {
      Alert.alert("Test failed", e.message);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primaryLight} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header stats */}
      <View style={styles.statsRow}>
        <StatBadge
          label="Active"
          value={rules.filter((r) => r.status === "active").length}
          color={colors.success}
        />
        <StatBadge
          label="Triggered"
          value={rules.filter((r) => r.status === "triggered").length}
          color={colors.warning}
        />
        <StatBadge label="Total" value={rules.length} color={colors.primaryLight} />
      </View>

      <FlatList
        data={rules}
        keyExtractor={(item) => String(item.rule_id)}
        renderItem={({ item }) => (
          <RuleCard
            rule={item}
            onDelete={() => handleDelete(item)}
            onReset={() => handleReset(item)}
            onTest={() => handleTest(item)}
          />
        )}
        contentContainerStyle={rules.length === 0 ? styles.emptyContainer : styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={colors.primaryLight}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>◈</Text>
            <Text style={styles.emptyTitle}>No rules yet</Text>
            <Text style={styles.emptySubtitle}>Tap Add Rule to create your first alert</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => navigation.navigate("Add Rule")}
              activeOpacity={0.8}
            >
              <Text style={styles.addButtonText}>+ Add Rule</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
  );
}

function RuleCard({ rule, onDelete, onReset, onTest }) {
  const sc = STATUS[rule.status] ?? STATUS.active;
  const condLabel = CONDITIONS[rule.condition] ?? rule.condition;
  const tfLabel   = TIMEFRAMES[rule.timeframe] ?? rule.timeframe;
  const isPct     = rule.condition?.includes("pct");

  return (
    <View style={styles.card}>
      {/* Top row: instrument + status */}
      <View style={styles.cardHeader}>
        <Text style={styles.instrument}>{rule.instrument}</Text>
        <View style={[styles.statusBadge, { backgroundColor: sc.bg }]}>
          <View style={[styles.statusDot, { backgroundColor: sc.dot }]} />
          <Text style={[styles.statusText, { color: sc.text }]}>{sc.label}</Text>
        </View>
      </View>

      {/* Description */}
      <Text style={styles.description}>{rule.description}</Text>

      {/* Condition detail */}
      <Text style={styles.detail}>
        {condLabel} {rule.threshold}{isPct ? "%" : ""} {tfLabel}
      </Text>

      {/* Timestamps */}
      <Text style={styles.timestamp}>
        Created {new Date(rule.created_at).toLocaleDateString("en-IN")}
        {rule.triggered_at
          ? `  ·  Triggered ${new Date(rule.triggered_at).toLocaleTimeString("en-IN")}`
          : ""}
      </Text>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={onTest} activeOpacity={0.7}>
          <Text style={styles.actionBtnText}>▷ Test</Text>
        </TouchableOpacity>
        {rule.status === "triggered" && (
          <TouchableOpacity
            style={[styles.actionBtn, styles.resetBtn]}
            onPress={onReset}
            activeOpacity={0.7}
          >
            <Text style={[styles.actionBtnText, { color: colors.warning }]}>↺ Reset</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.actionBtn, styles.deleteBtn]}
          onPress={onDelete}
          activeOpacity={0.7}
        >
          <Text style={[styles.actionBtnText, { color: colors.danger }]}>✕ Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function StatBadge({ label, value, color }) {
  return (
    <View style={styles.statBadge}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  centered: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },

  statsRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  statBadge: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 12,
    borderRightWidth: 1,
    borderColor: colors.border,
  },
  statValue: { fontSize: 22, fontWeight: "700" },
  statLabel: { color: colors.textFaint, fontSize: 10, letterSpacing: 1, marginTop: 2 },

  listContent: { padding: 16, gap: 12 },
  emptyContainer: { flex: 1 },
  emptyState: { flex: 1, alignItems: "center", justifyContent: "center", padding: 40 },
  emptyIcon:    { fontSize: 36, color: colors.textFaint, marginBottom: 12 },
  emptyTitle:   { color: colors.text, fontSize: 18, fontWeight: "600", marginBottom: 6 },
  emptySubtitle:{ color: colors.textMuted, fontSize: 14, textAlign: "center", marginBottom: 24 },
  addButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  addButtonText: { color: "#fff", fontSize: 14 },

  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: 16,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  instrument: { color: colors.primaryLight, fontSize: 13, fontWeight: "600" },

  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  statusDot: { width: 6, height: 6, borderRadius: 3 },
  statusText: { fontSize: 10, letterSpacing: 1 },

  description: { color: colors.text, fontSize: 14, marginBottom: 4, lineHeight: 20 },
  detail:      { color: colors.textMuted, fontSize: 12, marginBottom: 4 },
  timestamp:   { color: colors.textFaint, fontSize: 11, marginBottom: 12 },

  actions: { flexDirection: "row", gap: 8 },
  actionBtn: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: 6,
  },
  resetBtn:  { borderColor: "#78350f" },
  deleteBtn: { borderColor: colors.dangerMuted },
  actionBtnText: { color: colors.textMuted, fontSize: 12 },
});
