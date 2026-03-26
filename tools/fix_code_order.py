"""Move meta tags, JSON-LD, and comments to the bottom of each code block.
The <style> tag must come first for Squarespace compatibility."""
import os
import glob
import re

code_dir = os.path.expanduser("~/Documents/Claude/business/website/code-blocks")
skip = {"homepage.html", "sitewide-header.html"}

for filepath in sorted(glob.glob(os.path.join(code_dir, "*.html"))):
    fname = os.path.basename(filepath)
    if fname in skip:
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Find the first <style> tag (the page-specific CSS)
    style_match = re.search(r'<style>', content)
    if not style_match:
        print(f"  No <style> found: {fname}")
        continue

    style_pos = style_match.start()

    # Everything before <style> is the "preamble" (comments, meta, JSON-LD)
    preamble = content[:style_pos].strip()
    rest = content[style_pos:]

    if not preamble:
        print(f"  Already clean: {fname}")
        continue

    # Move preamble to end of file
    new_content = rest.rstrip() + "\n\n" + preamble + "\n"

    with open(filepath, "w") as f:
        f.write(new_content)

    # Also write .txt
    with open(filepath.replace(".html", ".txt"), "w") as f:
        f.write(new_content)

    print(f"  Fixed: {fname}")

print("\nDone.")
