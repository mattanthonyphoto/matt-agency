"""Add location links row to every footer that's missing it."""
import os
import glob
import re

code_dir = os.path.expanduser("~/Documents/Claude/business/website/code-blocks")
skip = {"sitewide-header.html", "sitewide-header.txt"}

# Location row HTML for each CSS prefix
def get_loc_row(prefix):
    return f'''<div class="{prefix}ft-locs"><a href="/squamish-architectural-photography">Squamish</a><a href="/whistler-architectural-photography">Whistler</a><a href="/pemberton-photography">Pemberton</a><a href="/sunshine-coast-photography">Sunshine Coast</a><a href="/vancouver-architectural-photographer">Vancouver</a><a href="/fraser-valley-photography">Fraser Valley</a><a href="/okanagan-architectural-photographer">Okanagan</a></div>'''

# CSS for location row
def get_loc_css(prefix):
    return f'.{prefix}ft-locs{{display:flex;justify-content:center;gap:2rem;padding:1.75rem 5vw;border-bottom:1px solid rgba(201,169,110,.08);flex-wrap:wrap}}.{prefix}ft-locs a{{font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:rgba(246,244,240,.35);font-weight:500;transition:color .3s ease}}.{prefix}ft-locs a:hover{{color:#c9a96e}}'

# Mobile CSS for location row
def get_loc_mobile(prefix):
    return f'.{prefix}ft-locs{{gap:1rem;padding:1.5rem 6vw;justify-content:flex-start}}.{prefix}ft-locs a{{font-size:.55rem}}'

fixed = 0
for dirpath, dirnames, filenames in os.walk(code_dir):
    for fname in sorted(filenames):
        if not fname.endswith('.html') or fname in skip:
            continue

        filepath = os.path.join(dirpath, fname)
        with open(filepath, 'r') as f:
            content = f.read()

        # Skip if already has location row
        if 'squamish-architectural-photography' in content or 'ft-locs' in content:
            continue

        # Detect the CSS prefix by finding the footer class
        prefix_match = re.search(r'\.(\w+)-ft\{', content)
        if not prefix_match:
            prefix_match = re.search(r'\.(\w+)-ft-r\{', content)
        if not prefix_match:
            print(f"  No footer prefix found: {fname}")
            continue

        prefix = prefix_match.group(1) + '-'

        # 1. Add location CSS before the footer CSS
        loc_css = get_loc_css(prefix)
        ft_pattern = f'.{prefix}ft{{'
        if ft_pattern in content:
            content = content.replace(ft_pattern, loc_css + ft_pattern, 1)

        # 2. Add mobile CSS for locations
        loc_mobile = get_loc_mobile(prefix)
        # Find the mobile media query and add inside it, before the footer mobile rules
        mobile_ft = f'.{prefix}ft-r{{flex-direction:column'
        if mobile_ft in content:
            content = content.replace(mobile_ft, loc_mobile + mobile_ft, 1)

        # 3. Add location row HTML right after the footer div opens
        loc_html = get_loc_row(prefix)
        # The footer starts with <div class="XX-ft"> and the first child is <div class="XX-ft-r">
        ft_r_pattern = f'<div class="{prefix}ft-r">'
        if ft_r_pattern in content:
            content = content.replace(ft_r_pattern, loc_html + '\n' + ft_r_pattern, 1)

        with open(filepath, 'w') as f:
            f.write(content)

        # Also write .txt
        txt_path = filepath.replace('.html', '.txt')
        with open(txt_path, 'w') as f:
            f.write(content)

        fixed += 1
        rel_path = os.path.relpath(filepath, code_dir)
        print(f"  Fixed: {rel_path}")

print(f"\nDone. Added location row to {fixed} pages.")
