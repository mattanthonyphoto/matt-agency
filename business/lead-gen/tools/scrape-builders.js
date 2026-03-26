const { ApifyClient } = require("apify-client");
const fs = require("fs");

const client = new ApifyClient({
  token: "apify_api_m1aRCBCFgIhOi401T7PxdfY3hgMwJl3Cmn2g",
});

const searches = [
  "custom home builder Vancouver BC",
  "home builder Vancouver BC",
  "construction company Vancouver BC",
  "residential builder Vancouver BC",
  "custom home builder Whistler BC",
  "home builder Whistler BC",
  "custom home builder Squamish BC",
  "home builder Squamish BC",
  "custom home builder Pemberton BC",
  "home builder Pemberton BC",
  "custom home builder Sunshine Coast BC",
  "home builder Sunshine Coast BC",
  "custom home builder Fraser Valley BC",
  "home builder Fraser Valley BC",
  "residential construction company Sea to Sky BC",
  "luxury home builder Vancouver BC",
  "luxury home builder Whistler BC",
];

async function run() {
  console.log(`Starting Google Maps scrape with ${searches.length} searches...`);

  const run = await client.actor("compass/crawler-google-places").call({
    searchStringsArray: searches,
    maxCrawledPlacesPerSearch: 50,
    language: "en",
    deeperCityScrape: false,
    skipClosedPlaces: true,
  });

  console.log(`Run finished. Fetching results...`);

  const { items } = await client.dataset(run.defaultDatasetId).listItems();

  // Deduplicate by website
  const seen = new Set();
  const leads = [];

  for (const item of items) {
    const name = item.title || item.name || "";
    const website = item.website || item.url || "";
    const key = website ? website.replace(/https?:\/\/(www\.)?/, "").replace(/\/$/, "") : name;

    if (!key || seen.has(key)) continue;
    seen.add(key);

    leads.push({
      name,
      website: website || "N/A",
      address: item.address || "",
      phone: item.phone || "",
      rating: item.totalScore || "",
      reviews: item.reviewsCount || "",
    });
  }

  // Sort by reviews count descending
  leads.sort((a, b) => (b.reviews || 0) - (a.reviews || 0));

  // Write CSV
  const csv = [
    "Company Name,Website,Address,Phone,Rating,Reviews",
    ...leads.map(
      (l) =>
        `"${l.name}","${l.website}","${l.address}","${l.phone}","${l.rating}","${l.reviews}"`
    ),
  ].join("\n");

  fs.writeFileSync("builders-leads.csv", csv);
  console.log(`\nDone! ${leads.length} unique builders saved to builders-leads.csv`);
}

run().catch(console.error);
