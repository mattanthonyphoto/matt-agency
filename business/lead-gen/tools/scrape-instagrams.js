const { ApifyClient } = require("apify-client");
const fs = require("fs");

const client = new ApifyClient({
  token: "apify_api_m1aRCBCFgIhOi401T7PxdfY3hgMwJl3Cmn2g",
});

// Read existing CSV
const raw = fs.readFileSync("builders-bc-all.csv", "utf8");
const lines = raw.split("\n");

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

// Extract all websites
const leads = [];
for (let i = 1; i < lines.length; i++) {
  const line = lines[i].trim();
  if (!line) continue;
  const fields = parseCsvLine(line);
  const [name, website, city, address, phone, email, rating, reviews] = fields;
  leads.push({ name, website, city, address, phone, email, rating, reviews, instagram: "" });
}

// Get unique websites to scrape
const urls = leads
  .filter((l) => l.website && l.website.startsWith("http"))
  .map((l) => {
    // Clean URL to just the homepage
    try {
      const u = new URL(l.website);
      return { url: u.origin, originalWebsite: l.website };
    } catch {
      return null;
    }
  })
  .filter(Boolean);

// Deduplicate URLs
const uniqueUrls = [...new Map(urls.map((u) => [u.url, u])).values()];
console.log(`Scraping ${uniqueUrls.length} websites for Instagram links...\n`);

async function run() {
  // Use cheerio-scraper to visit each site and extract Instagram links
  const result = await client.actor("apify/cheerio-scraper").call(
    {
      startUrls: uniqueUrls.map((u) => ({ url: u.url })),
      maxRequestsPerCrawl: uniqueUrls.length,
      maxCrawlingDepth: 0, // Only visit the homepage
      maxRequestRetries: 1,
      requestHandlerTimeoutSecs: 15,
      pageFunction: async function pageFunction(context) {
        const { $, request } = context;
        const igLinks = new Set();

        // Find all links containing instagram.com
        $('a[href*="instagram.com"]').each((_, el) => {
          const href = $(el).attr("href");
          if (href && href.includes("instagram.com")) {
            // Clean up the URL
            const match = href.match(/instagram\.com\/([a-zA-Z0-9_.]+)/);
            if (match && !["explore", "accounts", "p", "reel", "stories", "direct"].includes(match[1])) {
              igLinks.add(`https://www.instagram.com/${match[1]}/`);
            }
          }
        });

        return {
          url: request.url,
          instagrams: [...igLinks],
        };
      },
    },
    { waitSecs: 0 }
  );

  console.log("Scrape finished. Fetching results...");

  const { items } = await client.dataset(result.defaultDatasetId).listItems();

  // Build a map of website -> instagram
  const igMap = new Map();
  for (const item of items) {
    if (item.instagrams && item.instagrams.length > 0) {
      try {
        const origin = new URL(item.url).origin;
        igMap.set(origin, item.instagrams[0]); // Take first IG link
      } catch {}
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
}

run().catch(console.error);
