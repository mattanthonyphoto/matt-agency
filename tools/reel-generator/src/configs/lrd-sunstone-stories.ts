import type { StoryConfig } from "../StoryReel";

// All photos live in public/lrd-sunstone/<num>.jpg
const p = (n: number) => `lrd-sunstone/${n}.jpg`;

// Music assignments — one unique track per story.
// Sunstone overall: elevated, warm, celebratory — Western Living award winner.
// - Award    → Jazzy Soul (neo-soul): brightest celebratory warmth, fits the win.
// - Kitchen  → Organic House: warm percussive daily-rhythm pulse for kitchen life.
// - Details  → Smoke Lo-fi R&B: atmospheric, close-focus tone for hidden details.
// - Primary  → Neo Soul Night: intimate, jazzy keys for the bedroom suite.
// - Mountain → House (Monume): warm open house feel for the expansive valley reveal.

export const sunstoneStoryAward: StoryConfig = {
  id: "LRD-Story-Sunstone-Award",
  title: "Sunstone — Award",
  musicFile: "sunsides-jazzy-soul-207549.mp3",
  // Lauren: the win is for the kitchen — images must reflect the kitchen only.
  frames: [
    { photo: p(7134), text: "Western Living Design 25 Winner 2026" },
    { photo: p(7150), text: "Sunstone Kitchen, Pemberton BC" },
    { photo: p(7126), text: "We're honored and still processing it." },
    {
      photo: p(7185),
      text: "Thank you @westernlivingmagazine — see our latest post.",
      duration: 6,
    },
  ],
};

export const sunstoneStoryKitchen: StoryConfig = {
  id: "LRD-Story-Sunstone-Kitchen",
  title: "Sunstone — Kitchen",
  musicFile: "progressive-house-organic-progressive-house-essentials-349339.mp3",
  frames: [
    { photo: p(7134), text: "Not everyone wants their everyday dishes behind a door." },
    { photo: p(7126), text: "An exposed shelf runs the full length of the kitchen." },
    { photo: p(7185), text: "Around the corner, a hidden pantry. No door." },
    { photo: p(7150), text: "New on the feed — Sunstone Kitchen." },
  ],
};

export const sunstoneStoryDetails: StoryConfig = {
  id: "LRD-Story-Sunstone-Details",
  title: "Sunstone — Details",
  musicFile: "soulprodmusic-smoke-143172.mp3",
  frames: [
    { photo: p(7305), text: "This shelf has a secret." },
    { photo: p(7293), text: "Hidden key drawer. Mitered top. You'd never know." },
    { photo: p(6976), text: "A pull-out folding shelf. Fold right where they're going." },
    { photo: p(7069), text: "See our latest post — the details that disappear." },
  ],
};

export const sunstoneStoryPrimary: StoryConfig = {
  id: "LRD-Story-Sunstone-Primary",
  title: "Sunstone — Primary Suite",
  musicFile: "sunsides-neo-soul-night-210447.mp3",
  frames: [
    { photo: p(6932), text: "Through the window, the valley." },
    { photo: p(6946), text: "The daily routine, considered." },
    { photo: p(6829), text: "Black hardwood as wall cladding. Not flooring." },
    { photo: p(6912), text: "Sunstone Primary Suite — new on the feed." },
  ],
};

export const sunstoneStoryMountain: StoryConfig = {
  id: "LRD-Story-Sunstone-Mountain",
  title: "Sunstone — Mountain",
  musicFile: "monume-house-509469.mp3",
  frames: [
    { photo: p(7196), text: "Up high above the valley in Pemberton." },
    { photo: p(7218), text: "Let the mountains do the work." },
    { photo: p(7261), text: "See our latest post." },
  ],
};

export const sunstoneStoryConfigs: StoryConfig[] = [
  sunstoneStoryAward,
  sunstoneStoryKitchen,
  sunstoneStoryDetails,
  sunstoneStoryPrimary,
  sunstoneStoryMountain,
];
