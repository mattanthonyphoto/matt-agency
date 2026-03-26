"""Strip baked-in nav boilerplate from all code blocks except homepage."""
import os
import glob

code_dir = os.path.expanduser("~/Documents/Claude/business/website/code-blocks")
skip = {"homepage.html", "sitewide-header.html"}

for filepath in sorted(glob.glob(os.path.join(code_dir, "*.html"))):
    fname = os.path.basename(filepath)
    if fname in skip:
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Check if nav boilerplate exists
    if '<div id="maHeader">' not in content:
        print(f"  No nav: {fname}")
        continue

    lines = content.split('\n')
    nav_style_start = -1
    nav_script_end = -1

    # Find the shared <style> block that starts with #header override
    for i, line in enumerate(lines):
        if line.strip() == '<style>' and i + 1 < len(lines) and '#header,header,.header' in lines[i + 1]:
            nav_style_start = i
            break

    if nav_style_start < 0:
        print(f"  No override style: {fname}")
        continue

    # Find the </script> that ends the nav JS block
    # It's the one containing the toggle/scroll code
    for i in range(nav_style_start, len(lines)):
        if '</script>' in lines[i] and ('classList.toggle' in lines[i] or 'classList.remove' in lines[i] or (i > 0 and 'closest' in lines[i])):
            nav_script_end = i
            break

    if nav_script_end < 0:
        # Try another approach - find the script that has the nav JS
        for i in range(nav_style_start, len(lines)):
            if lines[i].strip().startswith('<script>') and 'maToggle' in lines[i]:
                # Find its closing </script>
                if '</script>' in lines[i]:
                    nav_script_end = i
                    break

    if nav_script_end < 0:
        print(f"  No script end: {fname}")
        continue

    # Remove lines from nav_style_start to nav_script_end (inclusive)
    new_lines = lines[:nav_style_start] + lines[nav_script_end + 1:]
    result = '\n'.join(new_lines)

    # Clean up excessive blank lines
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')

    with open(filepath, "w") as f:
        f.write(result)

    removed = nav_script_end - nav_style_start + 1
    print(f"  Stripped {removed} lines from {fname}")

# Refresh all .txt copies
for filepath in sorted(glob.glob(os.path.join(code_dir, "*.html"))):
    txt_path = filepath.replace(".html", ".txt")
    with open(filepath, "r") as f:
        content = f.read()
    with open(txt_path, "w") as f:
        f.write(content)

print("\nAll .txt copies refreshed.")
