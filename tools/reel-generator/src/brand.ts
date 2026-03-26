export const colors = {
  ink: "#1A1A18",
  paper: "#F6F4F0",
  gold: "#C9A96E",
  warmMuted: "#B8975A",
  stone: "#8A8579",
  lightStone: "#D9D5CD",
  offWhite: "#EEECE6",
} as const;

export const fonts = {
  serif: "'Cormorant Garamond', Georgia, serif",
  sans: "'DM Sans', -apple-system, sans-serif",
  display: "'Josefin Sans', sans-serif",
} as const;

export type PhotoLayout = "fullscreen" | "horizontal-float" | "stacked-pair" | "triple-grid" | "big-small";

export interface Slide {
  layout: PhotoLayout;
  photos: string[];
  label?: string;
  location?: string;
  zoomDir?: "in" | "out";
  floatPos?: "top" | "center" | "bottom";
}

// Gallery — 9 photos from Matt's selection, mixed layouts
export const slides: Slide[] = [
  // 1. Warbler vertical hero — FULLSCREEN with zoom out (the money shot)
  { layout: "fullscreen", photos: ["fitz_b.jpg"], label: "FITZSIMMONS RESIDENCE", location: "WHISTLER, BC", zoomDir: "out" },

  // 2. Warbler horizontal floating top
  { layout: "horizontal-float", photos: ["warbler_a.jpg"], label: "WARBLER RESIDENCE", location: "WHISTLER, BC", floatPos: "top", zoomDir: "in" },

  // 3. Stacked pair — two warbler horizontals
  { layout: "stacked-pair", photos: ["warbler_b.jpg", "warbler_c.jpg"] },

  // 4. Fitz vertical fullscreen
  { layout: "fullscreen", photos: ["fitz_c.jpg"], zoomDir: "in" },

  // 5. Fitz horizontal float bottom
  { layout: "horizontal-float", photos: ["fitz_a.jpg"], floatPos: "bottom", zoomDir: "out" },

  // 6. Sugarloaf — big horizontal + small vertical
  { layout: "big-small", photos: ["sugar_a.jpg", "sugar_b.jpg"], label: "SUGARLOAF RESIDENCE", location: "PEMBERTON, BC" },

  // 7. Eagle horizontal float center
  { layout: "horizontal-float", photos: ["eagle_a.jpg"], label: "EAGLE RESIDENCE", location: "PEMBERTON, BC", floatPos: "center", zoomDir: "in" },
];

export const BPM = 96;
export const BEAT_INTERVAL = 60 / BPM;
