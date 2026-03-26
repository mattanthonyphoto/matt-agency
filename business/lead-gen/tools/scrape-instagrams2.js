const { ApifyClient } = require("apify-client");
const fs = require("fs");

const client = new ApifyClient({
  token: "apify_api_m1aRCBCFgIhOi401T7PxdfY3hgMwJl3Cmn2g",
});

// Parse CSV
function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (const ch of line) {
    if (ch === '"') { inQuotes = !inQuotes; continue; }
    if (ch === "," && !inQuotes) { fields.push(current); current = ""; continue; }
    current += ch;
  }
  fields.push(current);
  return fields;
}

const raw = fs.readFileSync("builders-bc-all.csv", "utf8");
const lines = raw.split("\n");
const header = parseCsvLine(lines[0]);

const leads = [];
for (let i = 1; i < lines.length; i++) {
  const line = lines[i].trim();
  if (!line) continue;
  const fields = parseCsvLine(line);
  leads.push({
    name: fields[0] || "",
    website: fields[1] || "",
    city: fields[2] || "",
    address: fields[3] || "",
    phone: fields[4] || "",
    email: fields[5] || "",
    instagram: fields[6] || "",
    rating: fields[7] || "",
    reviews: fields[8] || "",
  });
}

// Get unique homepage URLs
const urlMap = new Map();
for (const lead of leads) {
  if (lead.website && lead.website.startsWith("http")) {
    try {
      const origin = new URL(lead.website).origin;
      if (!urlMap.has(origin)) urlMap.set(origin, lead.website);
    } catch {}
  }
}
const uniqueUrls = [...urlMap.keys()];
console.log(`Scraping ${uniqueUrls.length} websites for Instagram links...\n`);

async function run() {
  // Use website-content-crawler to extract links
  const result = await client.actor("apify/website-content-crawler").call(
    {
      startUrls: uniqueUrls.map((u) => ({ url: u })),
      maxCrawlDepth: 0,
      maxCrawlPages: uniqueUrls.length,
      maxRequestRetries: 1,
      requestTimeoutSecs: 15,
      crawlerType: "cheerio",
      saveFiles: false,
      saveScreenshots: false,
      saveMarkdown: false,
      saveHtml: true,
    },
    { waitSecs: 0 }
  );

  console.log("Scrape finished. Fetching results...");
  const { items } = await client.dataset(result.defaultDatasetId).listItems();
  console.log(`Got ${items.length} pages back`);

  // Extract Instagram links from HTML
  const igMap = new Map();
  const igRegex = /(?:https?:\/\/)?(?:www\.)?instagram\.com\/([a-zA-Z0-9_.]{2,30})\/?/gi;
  const skipUsernames = new Set(["explore", "accounts", "p", "reel", "reels", "stories", "direct", "about", "developer", "legal", "privacy"]);

  for (const item of items) {
    const html = item.html || item.text || item.markdown || "";
    const url = item.url || "";
    let origin;
    try { origin = new URL(url).origin; } catch { continue; }

    const matches = html.matchAll(igRegex);
    for (const match of matches) {
      const username = match[1].toLowerCase();
      if (!skipUsernames.has(username)) {
        igMap.set(origin, `https://www.instagram.com/${username}/`);
        break; // Take first valid one
      }
    }
  }

  console.log(`Found Instagram links for ${igMap.size} companies\n`);

  // Match back to leads
  let igCount = 0;
  for (const lead of leads) {
    if (lead.website) {
      try {
        const origin = new URL(lead.website).origin;
        if (igMap.has(origin)) {
          lead.instagram = igMap.get(origin);
          igCount++;
        }
      } catch {}
    }
  }

  // Write updated CSV
  const escapeCsv = (s) => `"${String(s || "").replace(/"/g, '""')}"`;
  const csv = [
    "Company Name,Website,City,Address,Phone,Email,Instagram,Rating,Reviews",
    ...leads.map((l) =>
      [l.name, l.website, l.city, l.address, l.phone, l.email, l.instagram, l.rating, l.reviews]
        .map(escapeCsv)
        .join(",")
    ),
  ].join("\n");

  fs.writeFileSync("builders-bc-all.csv", csv);
  console.log(`Done! Updated builders-bc-all.csv with Instagram column`);
  console.log(`${igCount} / ${leads.length} leads now have an Instagram link`);

  // Show some examples
  const withIg = leads.filter((l) => l.instagram);
  console.log("\nSample leads with Instagram:");
  withIg.slice(0, 15).forEach((l) => console.log(`  ${l.name} → ${l.instagram}`));
}

run().catch(console.error);
