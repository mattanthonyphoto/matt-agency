import type { ReelConfig } from "../LRDProjectReel";

// =============================================================
// LRD Studio — 5 project hero reels, 9:16, 20-30s each.
// Each reel: 2s intro card + 7 photos @ 2.5s + 2s outro = ~21.5s.
// =============================================================
//
// Music selection (Apr 2026):
//   `musicFile` can reference ANY file sitting in `public/` or
//   `public/music-library/`. Remotion's <Audio> resolves relative
//   to `public/`, so:
//       "music2.mp3"                        -> public/music2.mp3  (legacy)
//       "music-library/pb-neo-soul-night-210447.mp3" -> from the curated library
//
// Full curated library (55 royalty-free tracks across 5 mood buckets
// matching Lauren's taste: warm house, neo-soul, dream-pop, chill R&B,
// funk-house) lives in `public/music-library/`. See `catalog.json`
// in that folder, or the preview page at
//     /Users/matthewfernandes/Documents/Claude/clients/lrd-studio/music-library.html
// to audition tracks before picking one.
//
// To override the track for a single reel, just set its `musicFile`
// to a different path — e.g.
//     musicFile: "music-library/pb-almost-true-alanajordan.mp3"
//
// Current default below (`MUSIC`) keeps the existing music2.mp3 so
// already-rendered reels are unchanged. Update per-reel if you want
// fresh audio on re-render.
// =============================================================

const MUSIC = "music2.mp3";

// ---- Sunstone (Pemberton, BC) — Western Living Design 25 winner
export const sunstoneReel: ReelConfig = {
  id: "LRD-Reel-Sunstone",
  title: "Sunstone — Hero Reel",
  intro: { text: "Sunstone", subtitle: "PEMBERTON, BC" },
  frames: [
    { photo: "lrd-sunstone/7150.jpg" },
    { photo: "lrd-sunstone/7134.jpg" },
    { photo: "lrd-sunstone/7090.jpg", textOverlay: "Western Living Design 25 Winner 2026" },
    { photo: "lrd-sunstone/6932.jpg" },
    { photo: "lrd-sunstone/7196.jpg" },
    { photo: "lrd-sunstone/7069.jpg" },
    { photo: "lrd-sunstone/7305.jpg" },
  ],
  outro: { text: "LRD Studio", subtitle: "LRDSTUDIO.CA" },
  musicFile: MUSIC,
};

// ---- Tapleys (Whistler, BC) — classic home, transformed
export const tapleysReel: ReelConfig = {
  id: "LRD-Reel-Tapleys",
  title: "Tapleys — Hero Reel",
  intro: { text: "Tapleys", subtitle: "WHISTLER, BC" },
  frames: [
    { photo: "lrd-tapleys/LRD-2500px-29.jpg" },
    { photo: "lrd-tapleys/LRD-2500px-1.jpg" },
    { photo: "lrd-tapleys/LRD-2500px-7.jpg", textOverlay: "A classic home, transformed." },
    { photo: "lrd-tapleys/LRD-2500px-10.jpg" },  // sub for -14 (not in public/)
    { photo: "lrd-tapleys/LRD-2500px-22.jpg" },  // sub for -17 (not in public/)
    { photo: "lrd-tapleys/LRD-2500px-37.jpg" },
    { photo: "lrd-tapleys/LRD-2500px-28.jpg" },
  ],
  outro: { text: "LRD Studio", subtitle: "LRDSTUDIO.CA" },
  musicFile: MUSIC,
};

// ---- Sunridge (Whistler, BC) — stone tower at the heart
export const sunridgeReel: ReelConfig = {
  id: "LRD-Reel-Sunridge",
  title: "Sunridge — Hero Reel",
  intro: { text: "Sunridge", subtitle: "WHISTLER, BC" },
  frames: [
    { photo: "lrd-sunridge/sunridge-whistler-exterior-log-home-mountain-view-renovation.jpg" },
    { photo: "lrd-sunridge/sunridge-whistler-curved-staircase-stone-tower-floating-treads.jpg", textOverlay: "A stone tower at the heart." },
    { photo: "lrd-sunridge/sunridge-whistler-bar-stone-arch-cedar-ceiling-glassware.jpg" },
    { photo: "lrd-sunridge/sunridge-whistler-powder-room-arched-mirror-pedestal-sink-backlit.jpg" },
    { photo: "lrd-sunridge/sunridge-whistler-living-room-stone-fireplace-log-beams-mountain-view.jpg" },
    { photo: "lrd-sunridge/sunridge-whistler-kitchen-marble-waterfall-island-range-hood.jpg" },
    { photo: "lrd-sunridge/sunridge-whistler-master-ensuite-black-freestanding-tub-stone-accent.jpg" },
  ],
  outro: { text: "LRD Studio", subtitle: "LRDSTUDIO.CA" },
  musicFile: MUSIC,
};

// ---- Balsam (Whistler, BC) — steel, limestone, oak
export const balsamReel: ReelConfig = {
  id: "LRD-Reel-Balsam",
  title: "Balsam — Hero Reel",
  intro: { text: "Balsam", subtitle: "WHISTLER, BC" },
  frames: [
    { photo: "lrd-balsam/0441.jpg" },
    { photo: "lrd-balsam/0531.jpg" },
    { photo: "lrd-balsam/0555.jpg", textOverlay: "Steel. Limestone. Oak." },
    { photo: "lrd-balsam/0657.jpg" },
    { photo: "lrd-balsam/0450.jpg" },
    { photo: "lrd-balsam/0575.jpg" },   // sub for 0569 (not in public/)
    { photo: "lrd-balsam/0678.jpg" },
  ],
  outro: { text: "LRD Studio", subtitle: "LRDSTUDIO.CA" },
  musicFile: MUSIC,
};

// ---- SRAM Canada (North Vancouver) — a floor plan built around the wheel
export const sramReel: ReelConfig = {
  id: "LRD-Reel-SRAM",
  title: "SRAM — Hero Reel",
  intro: { text: "SRAM Canada", subtitle: "NORTH VANCOUVER" },
  frames: [
    { photo: "lrd-sram/sram-2.jpg" },
    { photo: "lrd-sram/sram-5.jpg", textOverlay: "A floor plan built around the wheel." },
    { photo: "lrd-sram/sram.jpg" },
    { photo: "lrd-sram/sram-7.jpg" },
    { photo: "lrd-sram/sram-15.jpg" },
    { photo: "lrd-sram/sram-3.jpg" },
    { photo: "lrd-sram/sram-25.jpg" },
  ],
  outro: { text: "LRD Studio", subtitle: "LRDSTUDIO.CA" },
  musicFile: MUSIC,
};

export const lrdReelConfigs: ReelConfig[] = [
  sunstoneReel,
  tapleysReel,
  sunridgeReel,
  balsamReel,
  sramReel,
];
