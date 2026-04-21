import type { StoryConfig } from "../StoryReel";

// All photos live in public/lrd-tapleys/<name>.jpg
const p = (name: string) => `lrd-tapleys/${name}`;

// NOTE on substitutions:
// - Frame "LRD-2500px-8.jpg" (wood fins fireplace detail) — no CDN URL existed in
//   any source doc. Substituted LRD-2500px-28.jpg (oak slatted panel detail),
//   the closest visual analog for "fins/slats" language.
// - Frame "LRD-2500px-32.jpg" (teal accent detail) — no CDN URL existed in any
//   source doc. Substituted LRD-2500px-37.jpg (boys teal-zellige bathroom vanity),
//   which is the clearest on-brand "teal" image and matches "the boys chose the teal."

// Music assignments — one unique track per story.
// Tapleys overall: domestic, warm, renewal of a family home.
// - Transformation → Dream Pop Lofi: cozy before/after domestic softness.
// - Kitchen        → Lounge Chill RnB: smooth, detail-focused kitchen browse.
// - Craft          → Smoke (warm house): atmospheric close-focus on materials/brass.
// - Generations    → Searching (neo-soul introspective): multi-generation warmth.

export const tapleysStoryTransformation: StoryConfig = {
  id: "LRD-Story-Tapleys-Transformation",
  title: "Tapleys — Transformation",
  musicFile: "dragon-studio-dream-pop-lofi-317545.mp3",
  // Lauren: first two captions didn't match the images — replacements below
  // speak to textured tile + black Carmanah stone fireplace.
  frames: [
    {
      photo: p("LRD-2500px-29.jpg"),
      text: "Textured tile has a soft spot in the hearts of many.",
    },
    {
      photo: p("LRD-2500px-1.jpg"),
      text: "Black Carmanah natural stone hugs this modest fireplace.",
    },
    // Substitute for 32.jpg (teal accent) — see note above
    { photo: p("LRD-2500px-37.jpg"), text: "The boys chose the teal." },
    { photo: p("LRD-2500px-7.jpg"), text: "Tapleys, Whistler — new on the feed." },
  ],
};

export const tapleysStoryKitchen: StoryConfig = {
  id: "LRD-Story-Tapleys-Kitchen",
  title: "Tapleys — Kitchen",
  musicFile: "tunetank-deep-house-347239.mp3",
  // Photo assignments verified against the actual images by Matt.
  frames: [
    { photo: p("LRD-2500px-10.jpg"), text: "A wine pocket and a cookbook pocket. At the island." },
    { photo: p("LRD-2500px-5.jpg"), text: "Hidden coffee nook around the corner." },
    { photo: p("LRD-2500px-7.jpg"), text: "Two floating shelves flanking the stove." },
    { photo: p("LRD-2500px-11.jpg"), text: "Every detail — new on the feed." },
  ],
};

export const tapleysStoryCraft: StoryConfig = {
  id: "LRD-Story-Tapleys-Craft",
  title: "Tapleys — Craft",
  musicFile: "soulprodmusic-smoke-143172 (1).mp3",
  frames: [
    // Substitute for 8.jpg (wood fins) — see note above
    {
      photo: p("LRD-2500px-28.jpg"),
      text: "Timeless wood slat detail conceals a corner cabinet.",
    },
    { photo: p("LRD-2500px-22.jpg"), text: "Zellige tiles. Organic texture. Every piece different." },
    { photo: p("LRD-2500px-31.jpg"), text: "Black and brass. By M-Tack. See our latest post." },
  ],
};

export const tapleysStoryGenerations: StoryConfig = {
  id: "LRD-Story-Tapleys-Generations",
  title: "Tapleys — Generations",
  musicFile: "romarecord1973-searching-of-insanity-126654.mp3",
  frames: [
    { photo: p("LRD-2500px-33.jpg"), text: "A parent suite with its own kitchenette." },
    { photo: p("LRD-2500px-34.jpg"), text: "Its own ensuite and wardrobe." },
    { photo: p("LRD-2500px-10.jpg"), text: "Designed for families. For years to come." },
    { photo: p("LRD-2500px-11.jpg"), text: "New on the feed — see our latest post." },
  ],
};

export const tapleysStoryConfigs: StoryConfig[] = [
  tapleysStoryTransformation,
  tapleysStoryKitchen,
  tapleysStoryCraft,
  tapleysStoryGenerations,
];
