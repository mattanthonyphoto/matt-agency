const { ApifyClient } = require("apify-client");
const fs = require("fs");

const client = new ApifyClient({
  token: "apify_api_m1aRCBCFgIhOi401T7PxdfY3hgMwJl3Cmn2g",
});

const bcCities = [
  "Vancouver BC", "North Vancouver BC", "West Vancouver BC",
  "Burnaby BC", "Surrey BC", "Richmond BC", "Langley BC",
  "Coquitlam BC", "Port Moody BC", "New Westminster BC",
  "Delta BC", "White Rock BC", "Maple Ridge BC",
  "Whistler BC", "Squamish BC", "Pemberton BC", "Lions Bay BC",
  "Gibsons BC", "Sechelt BC", "Powell River BC",
  "Abbotsford BC", "Chilliwack BC", "Mission BC", "Hope BC",
  "Victoria BC", "Nanaimo BC", "Kelowna BC", "Kamloops BC",
  "Vernon BC", "Penticton BC", "Courtenay BC", "Campbell River BC",
  "Prince George BC", "Cranbrook BC", "Nelson BC", "Revelstoke BC",
  "Tofino BC", "Ucluelet BC", "Parksville BC", "Qualicum Beach BC",
  "Comox BC", "Duncan BC", "Sidney BC", "Sooke BC",
  "Lake Country BC", "West Kelowna BC", "Summerland BC",
  "Invermere BC", "Fernie BC", "Golden BC", "Canmore BC",
];

const keywords = [
  "custom home builder",
  "home builder",
  "construction company",
  "residential builder",
  "luxury home builder",
  "general contractor residential",
];

// Build search strings: each keyword × each city
const searches = [];
for (const keyword of keywords) {
  for (const city of bcCities) {
    searches.push(`${keyword} ${city}`);
  }
}

async function run() {
  console.log(`Starting Google Maps scrape: ${searches.length} searches across all BC...`);
  console.log(`Keywords: ${keywords.length}, Cities: ${bcCities.length}\n`);

  const result = await client.actor("compass/crawler-google-places").call({
    searchStringsArray: searches,
    maxCrawledPlacesPerSearch: 30,
    language: "en",
    deeperCityScrape: false,
    skipClosedPlaces: true,
  });

  console.log(`Run finished. Fetching results...`);

  const { items } = await client.dataset(result.defaultDatasetId).listItems();
  console.log(`Raw results: ${items.length}`);

  // Extract city from address
  function extractCity(address) {
    if (!address) return "";
    // Try to match "City, BC" or "City, British Columbia"
    const match = address.match(/,\s*([^,]+),\s*BC\b/i) ||
                  address.match(/,\s*([^,]+),\s*British Columbia/i);
    if (match) return match[1].trim();
    // Try just city before postal code
    const match2 = address.match(/,\s*([A-Za-z\s]+)\s+V\d/);
    if (match2) return match2[1].trim();
    return "";
  }

  // Filter and deduplicate
  const excluded = [
    "real estate", "realtor", "realty", "rona", "home depot", "lowes", "lowe's",
    "outlet", "engraving", "cleaning", "plumber", "plumbing", "electrical contractor",
    "roofing", "painter", "painting", "flooring", "hvac", "heating", "moving",
    "storage", "insurance", "mortgage", "law", "legal", "dental", "medical",
    "restaurant", "cafe", "hotel", "motel", "salon", "spa", "gym", "fitness",
    "pet", "veterinar", "school", "church", "temple", "bank", "pharmacy",
    "grocery", "supermarket", "auto", "car dealer", "tire", "towing",
    "appliance", "furniture store", "mattress", "carpet",
  ];

  const bcPostalPattern = /\bV\d[A-Z]\s?\d[A-Z]\d\b/i;
  const seen = new Set();
  const leads = [];

  for (const item of items) {
    const name = item.title || item.name || "";
    const website = item.website || "";
    const address = item.address || "";
    const phone = item.phone || "";
    const email = item.email || "";
    const lower = `${name} ${address}`.toLowerCase();

    // Skip excluded categories
    if (excluded.some((ex) => lower.includes(ex))) continue;

    // Must be in BC (address contains BC or BC postal code)
    const isBC = /\bBC\b/.test(address) || /British Columbia/i.test(address) || bcPostalPattern.test(address);
    if (!isBC && address) continue;

    // Deduplicate by domain or name
    const domain = website
      .replace(/https?:\/\/(www\.)?/, "")
      .replace(/[/?#].*$/, "")
      .toLowerCase();
    const key = domain || name.toLowerCase().trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);

    const city = extractCity(address);

    leads.push({
      name,
      website: website || "",
      city,
      address,
      phone,
      email,
      rating: item.totalScore || "",
      reviews: item.reviewsCount || "",
    });
  }

  // Sort by city then name
  leads.sort((a, b) => a.city.localeCompare(b.city) || a.name.localeCompare(b.name));

  // Write CSV
  const escapeCsv = (s) => `"${String(s).replace(/"/g, '""')}"`;
  const csv = [
    "Company Name,Website,City,Address,Phone,Email,Rating,Reviews",
    ...leads.map((l) =>
      [l.name, l.website, l.city, l.address, l.phone, l.email, l.rating, l.reviews]
        .map(escapeCsv)
        .join(",")
    ),
  ].join("\n");

  fs.writeFileSync("builders-bc-all.csv", csv);
  console.log(`\nDone! ${leads.length} unique BC builders saved to builders-bc-all.csv`);

  // Summary by city
  const byCityCount = {};
  for (const l of leads) {
    const c = l.city || "Unknown";
    byCityCount[c] = (byCityCount[c] || 0) + 1;
  }
  console.log("\nLeads by city:");
  Object.entries(byCityCount)
    .sort((a, b) => b[1] - a[1])
    .forEach(([city, count]) => console.log(`  ${city}: ${count}`));
}

run().catch(console.error);
