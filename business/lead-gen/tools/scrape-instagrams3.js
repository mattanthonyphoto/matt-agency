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

// Build Google search queries: "company name" site:instagram.com
const queries = leads.map((l, i) => ({
  term: `"${l.name}" site:instagram.com`,
  index: i,
}));

console.log(`Searching Google for ${queries.length} company Instagram pages...\n`);

// Process in batches to avoid overloading
const BATCH_SIZE = 200;

async function run() {
  for (let batch = 0; batch < Math.ceil(queries.length / BATCH_SIZE); batch++) {
    const start = batch * BATCH_SIZE;
    const end = Math.min(start + BATCH_SIZE, queries.length);
    const batchQueries = queries.slice(start, end);

    console.log(`Batch ${batch + 1}: searching ${start + 1}-${end} of ${queries.length}...`);

    const result = await client.actor("apify/google-search-scraper").call(
      {
        queries: batchQueries.map((q) => q.term).join("\n"),
        maxPagesPerQuery: 1,
        resultsPerPage: 3,
        languageCode: "en",
        countryCode: "ca",
      },
      { waitSecs: 0 }
    );

    const { items } = await client.dataset(result.defaultDatasetId).listItems();

    // Match results back to leads
    let foundInBatch = 0;
    for (const item of items) {
      const searchQuery = item.searchQuery?.term || "";
      // Find which lead this was for
      const nameMatch = searchQuery.match(/^"(.+?)"\s+site:instagram\.com$/);
      if (!nameMatch) continue;
      const companyName = nameMatch[1];

      const leadIndex = leads.findIndex(
        (l) => l.name === companyName && !l.instagram
      );
      if (leadIndex === -1) continue;

      // Get the first Instagram URL from organic results
      const organicResults = item.organicResults || [];
      for (const result of organicResults) {
        const url = result.url || "";
        const igMatch = url.match(/instagram\.com\/([a-zA-Z0-9_.]{2,30})\/?/);
        if (igMatch) {
          const username = igMatch[1].toLowerCase();
          const skip = ["explore", "accounts", "p", "reel", "reels", "stories", "direct", "about", "developer", "legal", "privacy", "tags"];
          if (!skip.includes(username)) {
            leads[leadIndex].instagram = `https://www.instagram.com/${username}/`;
            foundInBatch++;
            break;
          }
        }
      }
    }
    console.log(`  Found ${foundInBatch} Instagram pages in this batch\n`);
  }

  // Write updated CSV
  const igCount = leads.filter((l) => l.instagram).length;
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
  console.log(`Done! ${igCount} / ${leads.length} leads now have Instagram links`);

  // Show examples
  const withIg = leads.filter((l) => l.instagram);
  console.log("\nSample leads with Instagram:");
  withIg.slice(0, 20).forEach((l) => console.log(`  ${l.name} → ${l.instagram}`));
}

run().catch(console.error);
