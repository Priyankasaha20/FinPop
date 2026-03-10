// theme.js — shared design tokens

export const colors = {
  bg:          "#0b0f1a",
  surface:     "#0f172a",
  surfaceAlt:  "#1e2d3d",
  border:      "#1e2d3d",
  borderLight: "#334155",

  text:        "#e2e8f0",
  textMuted:   "#94a3b8",
  textFaint:   "#475569",

  primary:     "#1d4ed8",
  primaryLight:"#60a5fa",

  success:     "#10b981",
  warning:     "#f59e0b",
  danger:      "#ef4444",
  dangerMuted: "#7f1d1d",
};

export const fonts = {
  mono: "Courier New",
};

export const STATUS = {
  active: {
    bg:   "rgba(16,185,129,0.12)",
    text: "#10b981",
    dot:  "#10b981",
    label: "ACTIVE",
  },
  triggered: {
    bg:   "rgba(245,158,11,0.12)",
    text: "#f59e0b",
    dot:  "#f59e0b",
    label: "TRIGGERED",
  },
  paused: {
    bg:   "rgba(100,116,139,0.12)",
    text: "#94a3b8",
    dot:  "#94a3b8",
    label: "PAUSED",
  },
};

export const CONDITIONS = {
  pct_change_down: "% Drop",
  pct_change_up:   "% Rise",
  above:           "Price above ₹",
  below:           "Price below ₹",
};

export const TIMEFRAMES = {
  from_open:       "from Today's Open",
  from_prev_close: "from Prev Close",
  absolute:        "(absolute)",
};
