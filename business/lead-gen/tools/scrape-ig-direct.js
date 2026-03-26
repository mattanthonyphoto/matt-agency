const fs = require("fs");
const https = require("https");
const http = require("http");

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

function fetchUrl(url, redirects = 3) {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => resolve(""), 8000);
    const proto = url.startsWith("https") ? https : http;
    try {
      const req = proto.get(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        timeout: 7000,
      }, (res) => {
        if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location && redirects > 0) {
          clearTimeout(timeout);
          let redirectUrl = res.headers.location;
          if (redirectUrl.startsWith("/")) {
            const u = new URL(url);
            redirectUrl = u.origin + redirectUrl;
          }
          resolve(fetchUrl(redirectUrl, redirects - 1));
          return;
        }
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
          if (body.length > 200000) { // Only read first 200KB
            res.destroy();
            clearTimeout(timeout);
            resolve(body);
          }
        });
        res.on("end", () => { clearTimeout(timeout); resolve(body); });
        res.on("error", () => { clearTimeout(timeout); resolve(""); });
      });
      req.on("error", () => { clearTimeout(timeout); resolve(""); });
      req.on("timeout", () => { req.destroy(); clearTimeout(timeout); resolve(""); });
    } catch { clearTimeout(timeout); resolve(""); }
  });
}

function extractInstagram(html) {
  const igRegex = /(?:https?:\/\/)?(?:www\.)?instagram\.com\/([a-zA-Z0-9_.]{2,30})\/?/gi;
  const skip = new Set(["explore", "accounts", "p", "reel", "reels", "stories", "direct", "about", "developer", "legal", "privacy", "tags", "share"]);
  const matches = html.matchAll(igRegex);
  for (const match of matches) {
    const username = match[1].toLowerCase();
    if (!skip.has(username)) {
      return `https://www.instagram.com/${username}/`;
    }
  }
  return "";
}

function extractEmail(html) {
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  const skip = ["example.com", "email.com", "yourdomain", "domain.com", "sentry.io", "wixpress.com", "googleapis.com", "gravatar.com", "wordpress.com", "w3.org", "schema.org", "squarespace.com", "getbootstrap.com"];
  const matches = html.matchAll(emailRegex);
  for (const match of matches) {
    const email = match[0].toLowerCase();
    if (!skip.some((s) => email.includes(s)) && !email.endsWith(".png") && !email.endsWith(".jpg") && !email.endsWith(".svg")) {
      return email;
    }
  }
  return "";
}

async function run() {
  const withWebsite = leads.filter((l) => l.website && l.website.startsWith("http"));
  console.log(`Fetching ${withWebsite.length} websites for Instagram links & emails...\n`);

  const CONCURRENCY = 20;
  let completed = 0;
  let igFound = 0;
  let emailFound = 0;

  async function processLead(lead) {
    let url = lead.website;
    try {
      const u = new URL(url);
      url = u.origin; // Just fetch homepage
    } catch {
      return;
    }

    const html = await fetchUrl(url);

    if (html) {
      const ig = extractInstagram(html);
      if (ig && !lead.instagram) {
        lead.instagram = ig;
        igFound++;
      }
      const email = extractEmail(html);
      if (email && !lead.email) {
        lead.email = email;
        emailFound++;
      }
    }

    completed++;
    if (completed % 100 === 0) {
      console.log(`  Progress: ${completed}/${withWebsite.length} (IG: ${igFound}, Emails: ${emailFound})`);
    }
  }

  // Process in chunks
  for (let i = 0; i < withWebsite.length; i += CONCURRENCY) {
    const chunk = withWebsite.slice(i, i + CONCURRENCY);
    await Promise.all(chunk.map(processLead));
  }

  console.log(`\nDone fetching!`);
  console.log(`Instagram found: ${igFound}`);
  console.log(`Emails found: ${emailFound}`);

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
  console.log(`\nUpdated builders-bc-all.csv`);

  // Show examples
  const withIg = leads.filter((l) => l.instagram);
  console.log(`\n${withIg.length} leads with Instagram:`);
  withIg.slice(0, 25).forEach((l) => console.log(`  ${l.name} → ${l.instagram}`));
}

run().catch(console.error);
