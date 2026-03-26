const fs = require("fs");

const raw = fs.readFileSync("builders-leads.csv", "utf8");
const lines = raw.split("\n");
const header = lines[0];

const excluded = [
  "real estate", "realtor", "rona", "home depot", "lowes", "outlet",
  "engraving", "cleaning", "plumbing", "electrical", "roofing",
  "painting", "flooring", "hvac", "heating", "moving", "storage",
  "insurance", "mortgage", "law", "legal", "dental", "medical",
];

const bcIndicators = ["BC", "British Columbia", "V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9"];
const targetAreas = [
  "vancouver", "whistler", "squamish", "pemberton", "sunshine coast",
  "fraser valley", "north vancouver", "west vancouver", "burnaby",
  "surrey", "langley", "coquitlam", "port moody", "new westminster",
  "richmond", "delta", "white rock", "abbotsford", "chilliwack",
  "mission", "maple ridge", "gibsons", "sechelt", "powell river",
  "sea to sky", "lions bay",
];

const results = [];
const seen = new Set();

for (let i = 1; i < lines.length; i++) {
  const line = lines[i].trim();
  if (!line) continue;

  // Parse CSV (simple quoted field parser)
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (const ch of line) {
    if (ch === '"') { inQuotes = !inQuotes; continue; }
    if (ch === "," && !inQuotes) { fields.push(current); current = ""; continue; }
    current += ch;
  }
  fields.push(current);

  const [name, website, address] = fields;
  const lower = `${name} ${website} ${address}`.toLowerCase();

  // Skip non-builder businesses
  if (excluded.some((ex) => lower.includes(ex))) continue;

  // Must be in BC or target area
  const isBC = bcIndicators.some((ind) => (address || "").includes(ind));
  const isTargetArea = targetAreas.some((area) => lower.includes(area));
  if (!isBC && !isTargetArea) continue;

  // Deduplicate by domain
  const domain = (website || "")
    .replace(/https?:\/\/(www\.)?/, "")
    .replace(/\/.*$/, "")
    .toLowerCase();
  const key = domain || name.toLowerCase();
  if (seen.has(key)) continue;
  seen.add(key);

  results.push({ name, website: website || "N/A" });
}

// Write clean CSV
const csv = [
  "Company Name,Website",
  ...results.map((r) => `"${r.name}","${r.website}"`),
].join("\n");

fs.writeFileSync("builders-leads-clean.csv", csv);
console.log(`Cleaned: ${results.length} BC builders saved to builders-leads-clean.csv\n`);

// Print them out
results.forEach((r, i) => {
  console.log(`${i + 1}. ${r.name} — ${r.website}`);
});
