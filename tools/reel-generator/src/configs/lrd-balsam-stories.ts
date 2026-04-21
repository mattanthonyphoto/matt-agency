import type { StoryConfig } from "../StoryReel";

// All photos live in public/lrd-balsam/<name>.jpg
const p = (name: string) => `lrd-balsam/${name}`;

// Music assignments — one unique track per story.
// Balsam overall: entertaining, groovy, designed around gathering.
// - Kitchen   → Deep House Lounge (Tunetank): lounge energy for the entertaining kitchen.
// - WineRoom  → Bewitched (Deep House, warm melodic): jewel-box teaky lounge.
// - Details   → Je Vais Trouver (warm house): warm glow for underlit-step details.
// - Stone     → RnB Youtube / Movement (chill moody): atmospheric for natural-stone focus.

export const balsamStoryKitchen: StoryConfig = {
  id: "LRD-Story-Balsam-Kitchen",
  title: "Balsam — Kitchen",
  musicFile: "tunetank-deep-house-lounge-music-349539.mp3",
  frames: [
    { photo: p("0441.jpg"), text: "Cold rolled steel. Chisel limestone. Rustic oak." },
    { photo: p("0627.jpg"), text: "One of our favourite kitchens to date." },
    { photo: p("0639.jpg"), text: "The broom closet? You'd never know it's there." },
    { photo: p("0531.jpg"), text: "New on the feed — Balsam Kitchen." },
  ],
};

export const balsamStoryWineRoom: StoryConfig = {
  id: "LRD-Story-Balsam-WineRoom",
  title: "Balsam — Wine Room",
  musicFile: "soulprodmusic-bewitched-121509.mp3",
  frames: [
    { photo: p("0555.jpg"), text: "A jewel box of a wine room." },
    { photo: p("0657.jpg"), text: "They call it the tiki bar." },
    { photo: p("0450.jpg"), text: "This home was designed around gathering." },
    { photo: p("0626.jpg"), text: "See our latest post." },
  ],
};

export const balsamStoryDetails: StoryConfig = {
  id: "LRD-Story-Balsam-Details",
  title: "Balsam — Details",
  musicFile: "olleaugust-je-vais-trouver-441385.mp3",
  frames: [
    { photo: p("0678.jpg"), text: "Each step underlit. A warm glow guiding you up." },
    { photo: p("0696.jpg"), text: "Subtle until you look twice." },
    { photo: p("0575.jpg"), text: "Even the wardrobe rods are underlit." },
    { photo: p("0723.jpg"), text: "New on the feed — the things we spend the most time on." },
  ],
};

export const balsamStoryStone: StoryConfig = {
  id: "LRD-Story-Balsam-Stone",
  title: "Balsam — Stone",
  musicFile: "soulprodmusic-movement-200697.mp3",
  // Lauren: first image was the mudroom — swap to three living-room frames
  // (stone fireplace hero + coffee-table decor).
  frames: [
    { photo: p("0544.jpg"), text: "Ocean black natural stone. One of our favourite designs." },
    { photo: p("0552.jpg"), text: "Kingston slate. From Ontario, where the clients are from." },
    { photo: p("0626.jpg"), text: "Every material tells a story. See our latest post." },
  ],
};

export const balsamStoryConfigs: StoryConfig[] = [
  balsamStoryKitchen,
  balsamStoryWineRoom,
  balsamStoryDetails,
  balsamStoryStone,
];
