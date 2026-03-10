/**
 * AddRuleScreen.js
 * User types a plain-English rule → Claude API parses it → user confirms → saved
 */

import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { colors, CONDITIONS, TIMEFRAMES } from "../theme";
import { parseRule, createRule } from "../services/api";

const EXAMPLES = [
  "Alert if Nifty drops 1.5% from open",
  "Reliance crosses ₹3000",
  "TCS rises 2% from yesterday's close",
  "Alert if Sensex falls below 73000",
];

export default function AddRuleScreen({ navigation }) {
  const [text, setText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [parsed, setParsed] = useState(null);
  const [error, setError] = useState("");

  const handleParse = async () => {
    if (!text.trim()) return;
    setParsing(true);
    setError("");
    setParsed(null);
    try {
      const result = await parseRule(text.trim());
      setParsed(result);
    } catch (e) {
      setError("Could not parse the rule. Try rephrasing or check your backend connection.");
    } finally {
      setParsing(false);
    }
  };

  const handleSave = async () => {
    if (!parsed) return;
    setSaving(true);
    try {
      await createRule(parsed);
      Alert.alert("Rule saved ✓", parsed.description, [
        {
          text: "View Rules",
          onPress: () => navigation.navigate("Rules"),
        },
        {
          text: "Add Another",
          onPress: () => {
            setText("");
            setParsed(null);
          },
        },
      ]);
    } catch (e) {
      Alert.alert("Save failed", e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    setParsed(null);
    setError("");
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {/* Input Section */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>DESCRIBE YOUR RULE</Text>
          <TextInput
            style={styles.input}
            value={text}
            onChangeText={setText}
            placeholder="e.g. Alert if Nifty drops 1.5% from open"
            placeholderTextColor={colors.textFaint}
            multiline
            numberOfLines={3}
            returnKeyType="done"
            blurOnSubmit
          />

          <TouchableOpacity
            style={[styles.parseButton, (!text.trim() || parsing) && styles.disabled]}
            onPress={handleParse}
            disabled={!text.trim() || parsing}
            activeOpacity={0.8}
          >
            {parsing ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.parseButtonText}>⟐  Parse with Claude</Text>
            )}
          </TouchableOpacity>

          {!!error && <Text style={styles.errorText}>{error}</Text>}
        </View>

        {/* Examples */}
        {!parsed && (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>EXAMPLES — tap to use</Text>
            {EXAMPLES.map((ex) => (
              <TouchableOpacity
                key={ex}
                style={styles.exampleChip}
                onPress={() => { setText(ex); setParsed(null); setError(""); }}
                activeOpacity={0.7}
              >
                <Text style={styles.exampleText}>{ex}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Parsed Rule Preview */}
        {parsed && (
          <View style={styles.parsedCard}>
            <Text style={styles.parsedHeader}>✓ PARSED RULE</Text>

            <View style={styles.parsedGrid}>
              <ParsedField label="Instrument" value={parsed.instrument} highlight />
              <ParsedField
                label="Condition"
                value={`${CONDITIONS[parsed.condition] ?? parsed.condition} ${parsed.threshold}${parsed.condition?.includes("pct") ? "%" : ""}`}
              />
              <ParsedField
                label="Timeframe"
                value={TIMEFRAMES[parsed.timeframe] ?? parsed.timeframe}
              />
              <ParsedField label="Summary" value={parsed.description} fullWidth />
            </View>

            <View style={styles.parsedActions}>
              <TouchableOpacity
                style={[styles.saveButton, saving && styles.disabled]}
                onPress={handleSave}
                disabled={saving}
                activeOpacity={0.8}
              >
                {saving ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>✓  Save Rule</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.discardButton}
                onPress={handleDiscard}
                activeOpacity={0.7}
              >
                <Text style={styles.discardButtonText}>✕  Discard</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function ParsedField({ label, value, highlight, fullWidth }) {
  return (
    <View style={[styles.parsedField, fullWidth && styles.fullWidth]}>
      <Text style={styles.parsedFieldLabel}>{label}</Text>
      <Text style={[styles.parsedFieldValue, highlight && { color: colors.primaryLight }]}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingBottom: 40 },

  section: { marginBottom: 28 },
  sectionLabel: {
    color: colors.textFaint,
    fontSize: 11,
    letterSpacing: 1.5,
    marginBottom: 10,
  },

  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 14,
    color: colors.text,
    fontSize: 15,
    fontFamily: "Courier New",
    minHeight: 90,
    textAlignVertical: "top",
    marginBottom: 12,
  },

  parseButton: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingVertical: 13,
    alignItems: "center",
  },
  parseButtonText: { color: "#fff", fontSize: 14, letterSpacing: 0.5 },
  disabled: { opacity: 0.5 },

  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginTop: 10,
    lineHeight: 18,
  },

  exampleChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 6,
    padding: 11,
    marginBottom: 8,
  },
  exampleText: { color: colors.textMuted, fontSize: 13 },

  parsedCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: "#1e3a2f",
    borderRadius: 8,
    padding: 18,
  },
  parsedHeader: {
    color: colors.success,
    fontSize: 11,
    letterSpacing: 1.5,
    marginBottom: 14,
  },
  parsedGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  parsedField: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: 6,
    padding: 10,
    width: "47%",
  },
  fullWidth: { width: "100%" },
  parsedFieldLabel: { color: colors.textFaint, fontSize: 10, marginBottom: 4 },
  parsedFieldValue: { color: colors.text, fontSize: 13 },

  parsedActions: { flexDirection: "row", gap: 10, marginTop: 16 },
  saveButton: {
    flex: 1,
    backgroundColor: "#059669",
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
  },
  saveButtonText: { color: "#fff", fontSize: 14 },
  discardButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
  },
  discardButtonText: { color: colors.textMuted, fontSize: 14 },
});
