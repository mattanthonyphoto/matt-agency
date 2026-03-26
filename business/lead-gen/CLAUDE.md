# Lead Gen Project

Builder/contractor lead generation and cold outreach system for Matt Anthony Photography.

## Project-Specific Notes

- Uses `apify-client` for web scraping
- Google service account credentials in `credentials/`
- Target market: BC builders and contractors

## Tools

- `tools/scrape-builders.js` — Scrape builder directories
- `tools/scrape-all-bc.js` — Scrape all BC builders
- `tools/scrape-ig-direct.js` — Direct Instagram scraping
- `tools/scrape-instagrams.js` / `2` / `3` — Instagram scraping iterations (consolidate when revisiting)
- `tools/clean-leads.js` — Clean and deduplicate lead data

## Data

All intermediate data lives in `.tmp/` — CSVs, XLSX exports, JSON configs.
