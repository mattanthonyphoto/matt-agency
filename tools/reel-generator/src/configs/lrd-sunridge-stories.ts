import type { StoryConfig } from "../StoryReel";

// All photos live in public/lrd-sunridge/<name>.jpg
const p = (name: string) => `lrd-sunridge/${name}`;

// Music assignments — one unique track per story.
// Sunridge overall: polished mountain-modern log home at Whistler altitude.
// - Tower     → Sweet Life Luxury Chill: the big round stone tower reveal deserves
//               the brightest polished chill-house cut we have.
// - Heritage  → Acoustic / A Call to the Soul: acoustic neo-soul for honouring
//               original log timbers, warm and grounded.
// - Kitchen   → Sames (Tresor warm house): modern domestic morning energy.
// - Bathrooms → Chill RnB Background (Nightfall): moody, atmospheric, stone-and-backlit
//               mirrors vibe.
// - Artists   → Aesthetics (neo-soul): intimate, craft-forward for the maker stories.

export const sunridgeStoryTower: StoryConfig = {
  id: "LRD-Story-Sunridge-Tower",
  title: "Sunridge — Tower",
  musicFile: "alexgrohl-sweet-life-luxury-chill-438146.mp3",
  frames: [
    {
      photo: p("sunridge-whistler-curved-staircase-stone-tower-floating-treads.jpg"),
      text: "A round stone structure anchors the middle of the house.",
    },
    {
      photo: p("sunridge-whistler-bar-stone-arch-cedar-ceiling-glassware.jpg"),
      text: "Inside: a bar. Cedar ceiling. Hot, cold, and sparkling water.",
    },
    {
      photo: p("sunridge-whistler-powder-room-arched-mirror-pedestal-sink-backlit.jpg"),
      text: "And a powder room with a backlit arched mirror.",
    },
    {
      photo: p("sunridge-whistler-living-room-stone-fireplace-log-beams-mountain-view.jpg"),
      text: "Sunridge, Whistler — new on the feed.",
    },
  ],
};

export const sunridgeStoryHeritage: StoryConfig = {
  id: "LRD-Story-Sunridge-Heritage",
  title: "Sunridge — Heritage",
  musicFile: "folk_acoustic_music-a-call-to-the-soul-149262.mp3",
  frames: [
    {
      photo: p("sunridge-whistler-exterior-log-home-mountain-view-renovation.jpg"),
      text: "An existing timber log home.",
    },
    {
      photo: p("sunridge-whistler-kitchen-marble-waterfall-island-range-hood.jpg"),
      text: "The challenge: modernize while honouring the timbers.",
    },
    {
      photo: p("sunridge-whistler-oak-cabinetry-detail-log-wall-junction.jpg"),
      text: "Where new oak meets original log.",
    },
    {
      photo: p("sunridge-whistler-dining-room-log-beams-pendant-lights.jpg"),
      text: "See our latest post.",
    },
  ],
};

export const sunridgeStoryKitchen: StoryConfig = {
  id: "LRD-Story-Sunridge-Kitchen",
  title: "Sunridge — Kitchen",
  musicFile: "tresor-sames-main-version-33583-03-44.mp3",
  frames: [
    {
      photo: p("sunridge-whistler-coffee-station-oak-cabinet-log-wall.jpg"),
      text: "The coffee bar has retractable doors.",
    },
    {
      photo: p("sunridge-whistler-kitchen-island-bar-seating-forest-window.jpg"),
      text: "Open them up. There's a hidden TV.",
    },
    {
      photo: p("sunridge-whistler-kitchen-marble-island-black-cabinets-wide.jpg"),
      text: "Morning sports with your coffee. New on the feed.",
    },
  ],
};

export const sunridgeStoryBathrooms: StoryConfig = {
  id: "LRD-Story-Sunridge-Bathrooms",
  title: "Sunridge — Bathrooms",
  musicFile: "soulprodmusic-nightfall-future-bass-music-228100.mp3",
  frames: [
    {
      photo: p("sunridge-whistler-master-ensuite-black-freestanding-tub-stone-accent.jpg"),
      text: "Six bathrooms. Each one different.",
    },
    {
      photo: p("sunridge-whistler-walk-in-shower-backlit-stone-niche-rain-head.jpg"),
      text: "But they all share a thread.",
    },
    {
      photo: p("sunridge-whistler-guest-bathroom-vanity-stone-tile.jpg"),
      text: "Natural stone. Black fixtures. Backlit mirrors.",
    },
    {
      photo: p("sunridge-whistler-cedar-sauna-interior-bench-detail.jpg"),
      text: "Plus a custom sauna. See our latest post.",
    },
  ],
};

export const sunridgeStoryArtists: StoryConfig = {
  id: "LRD-Story-Sunridge-Artists",
  title: "Sunridge — Artists",
  musicFile: "soulprodmusic-aesthetics-138637 (1).mp3",
  frames: [
    {
      photo: p("sunridge-whistler-living-room-fireplace-detail-bubble-chandelier.jpg"),
      text: "This chandelier is by Bachi. Hand-blown glass. Local BC artist.",
    },
    {
      photo: p("sunridge-whistler-entry-foyer-log-walls-modern-console.jpg"),
      text: "The entry light is by Matthew McCormick. Also local.",
    },
    {
      photo: p("sunridge-whistler-living-room-double-height-stone-fireplace-carved-art-wide.jpg"),
      text: "We love working with makers from this province.",
    },
  ],
};

export const sunridgeStoryConfigs: StoryConfig[] = [
  sunridgeStoryTower,
  sunridgeStoryHeritage,
  sunridgeStoryKitchen,
  sunridgeStoryBathrooms,
  sunridgeStoryArtists,
];
