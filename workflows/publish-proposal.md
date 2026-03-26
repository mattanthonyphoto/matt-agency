# Publish Proposal to GitHub Pages

## Objective
Upload an approved HTML proposal/pitch to GitHub Pages so it's publicly accessible via a shareable URL.

## When to Use
After a proposal has been approved and is ready to send to the client.

## Tool
`tools/publish_proposal.py`

## Hosting
- **Repo:** github.com/mattanthonyphoto/matt-proposals (public)
- **URL base:** https://mattanthonyphoto.github.io/matt-proposals/
- **Deploys:** Automatic on push, takes 30-60 seconds

## Process

### 1. Pre-flight Checks
- [ ] No base64 images (file should be under 200KB)
- [ ] All Squarespace CDN image URLs load
- [ ] Content is final (client name, dates, pricing)
- [ ] Valid-through date hasn't passed

### 2. Publish
```bash
# Upload a proposal
python3 tools/publish_proposal.py upload business/sales/balmoral-retainer-proposal.html \
  --client balmoral --name creative-partner-proposal.html

# Upload awards pitch
python3 tools/publish_proposal.py upload business/sales/balmoral-awards-strategy.html \
  --client balmoral --name awards-strategy.html
```

### 3. Verify
- Open the returned URL in browser
- Check mobile layout
- Test in incognito (no auth needed)

### 4. Share
URL can be sent via email, linked from GHL, or embedded in follow-up sequences.

## Managing Published Files

```bash
# List all published proposals
python3 tools/publish_proposal.py list

# List for a specific client
python3 tools/publish_proposal.py list --client balmoral

# Get URL
python3 tools/publish_proposal.py url balmoral/creative-partner-proposal.html

# Update (re-upload same path — overwrites, same URL)
python3 tools/publish_proposal.py upload business/sales/balmoral-retainer-proposal.html \
  --client balmoral --name creative-partner-proposal.html

# Remove expired proposal
python3 tools/publish_proposal.py delete balmoral/creative-partner-proposal.html
```

## File Naming Convention
```
{client-slug}/{document-type}.html
```
Examples:
- `balmoral/creative-partner-proposal.html`
- `balmoral/awards-strategy.html`
- `summerhill/project-photography-proposal.html`

## Notes
- Repo is public (required for free GitHub Pages) — proposals are accessible by URL but not discoverable via search (no indexing)
- Re-uploading the same path overwrites the file, keeping the same URL
- GitHub Pages takes 30-60 seconds to update after push
- No Supabase needed — this uses GitHub Pages directly
