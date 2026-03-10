/**
 * api.js — All calls to the FastAPI backend
 * Set API_BASE to your server's IP/URL.
 * During development: use your machine's local IP (not localhost)
 * so the phone/emulator can reach it, e.g. http://192.168.1.10:8000
 */

import Constants from "expo-constants";

export const API_BASE =
  Constants.expoConfig?.extra?.apiBaseUrl ?? "http://10.57.170.125:8000";

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Rules ─────────────────────────────────────────────────────────────────────

/** Parse plain-English text into a structured rule via Claude */
export const parseRule = (text) =>
  request("/api/rules/parse", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

/** Save a parsed rule */
export const createRule = (rule) =>
  request("/api/rules", {
    method: "POST",
    body: JSON.stringify(rule),
  });

/** Fetch all rules (active + triggered) */
export const getRules = () => request("/api/rules");

/** Delete a rule */
export const deleteRule = (ruleId) =>
  request(`/api/rules/${ruleId}`, { method: "DELETE" });

/** Dry-run a rule against live market data */
export const testRule = (ruleId) =>
  request(`/api/rules/${ruleId}/test`, { method: "POST" });

/** Re-arm a triggered rule */
export const resetRule = (ruleId) =>
  request(`/api/rules/${ruleId}/reset`, { method: "POST" });

// ── Alert History ─────────────────────────────────────────────────────────────

export const getAlertHistory = () => request("/api/alerts/history");

// ── Polling Control ───────────────────────────────────────────────────────────

export const getPollingStatus = () => request("/api/polling/status");
export const startPolling = () =>
  request("/api/polling/start", { method: "POST" });
export const stopPolling = () =>
  request("/api/polling/stop", { method: "POST" });

// ── Push Token Registration ───────────────────────────────────────────────────

/** Send the Expo push token to the backend so it can push alerts */
export const registerPushToken = (token) =>
  request("/api/push/register", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
