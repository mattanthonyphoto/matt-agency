import type { StoryConfig } from "../StoryReel";

// All photos live in public/lrd-sram/<name>.jpg
const p = (name: string) => `lrd-sram/${name}`;

// Music assignments — one unique track per story.
// SRAM overall: commercial HQ, bikes-are-culture, upbeat and energetic.
// - Space    → Whip Afro Dancehall (Kontraa): biggest commercial groove — the wheel,
//              the floor plan, the hero reveal.
// - Brand    → Genesis Pop Rap Beat (Amsleybeats, funk-house): swagger for the
//              black/grey/red brand language.
// - WorkLife → Dance Stan Town (Summer, funk-house): upbeat worklife energy, bikes
//              through the office.

export const sramStorySpace: StoryConfig = {
  id: "LRD-Story-SRAM-Space",
  title: "SRAM — Space",
  musicFile: "kontraa-whip-afro-dancehall-music-110235.mp3",
  frames: [
    { photo: p("sram-5.jpg"), text: "The floor plan started with a single idea: the wheel." },
    { photo: p("sram-7.jpg"), text: "Old shipping building. Original fir timbers." },
    { photo: p("sram.jpg"), text: "SRAM Canada HQ — new on the feed." },
  ],
};

export const sramStoryBrand: StoryConfig = {
  id: "LRD-Story-SRAM-Brand",
  title: "SRAM — Brand",
  musicFile: "amsleybeats-genesis-_-pop-rap-beat-265631.mp3",
  // Lauren rewrote the three lines in her voice.
  frames: [
    { photo: p("sram-2.jpg"), text: "Brand colours woven throughout." },
    { photo: p("sram-12.jpg"), text: "The culture of bike riders." },
    { photo: p("sram-15.jpg"), text: "Company identity represented in every space. See our latest post." },
  ],
};

export const sramStoryWorkLife: StoryConfig = {
  id: "LRD-Story-SRAM-WorkLife",
  title: "SRAM — Work Life",
  musicFile: "summer-dance-stan-town-main-version-40278-03-04.mp3",
  frames: [
    { photo: p("sram-3.jpg"), text: "The morning gathering point." },
    { photo: p("sram-25.jpg"), text: "Yes, someone's riding a bike through the office." },
    { photo: p("sram.jpg"), text: "Where work meets life. New on the feed." },
  ],
};

export const sramStoryConfigs: StoryConfig[] = [
  sramStorySpace,
  sramStoryBrand,
  sramStoryWorkLife,
];
