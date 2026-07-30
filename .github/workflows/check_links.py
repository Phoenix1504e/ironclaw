import re
from pathlib import Path
import sys

# Regex to find markdown links: [text](url)
# Negative lookahead (?!http|mailto) ensures we only grab relative links.
LINK_REGEX = re.compile(r'\[([^\]]+)\]\((?!http|https|mailto)(.*?)\)')

# Regex to find markdown headings (e.g., ## My Heading)
HEADING_REGEX = re.compile(r'^#+\s+(.*)$', re.MULTILINE)

def slugify(text):
    """
    Replicates standard GitHub-Flavored Markdown (GFM) heading slugification.
    - Convert to lowercase
    - Remove punctuation (except spaces and hyphens)
    - Replace spaces with hyphens
    """
    text = text.lower()
    # Strip everything that isn't alphanumeric, a space, or a hyphen
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    return text

def get_file_headings(filepath):
    """Reads a file and returns a set of all slugified headings."""
    if not filepath.exists():
        return set()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    headings = set()
    for match in HEADING_REGEX.finditer(content):
        headings.add(slugify(match.group(1)))
    return headings

def check_documentation():
    # Define the scope
    root_dir = Path('.')
    target_files = [root_dir / 'README.md'] + list((root_dir / 'docs').rglob('*.md'))
    
    errors_found = False

    for file_path in target_files:
        if not file_path.exists():
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all relative links in the file
        for match in LINK_REGEX.finditer(content):
            link_text = match.group(1)
            link_url = match.group(2)

            # Explicit exception requested by the author
            if file_path.name == 'scan-coverage.md' and link_url == '<deep doc>':
                continue

            # Split the URL into the file path and the anchor fragment
            if '#' in link_url:
                target_path_str, fragment = link_url.split('#', 1)
            else:
                target_path_str, fragment = link_url, None

            # Resolve the target file path
            if target_path_str == '':
                # The link is an anchor within the same file (e.g., #setup)
                target_file = file_path
            else:
                # Resolve relative to the directory of the current file
                target_file = (file_path.parent / target_path_str).resolve()

            # 1. Check if the target file exists
            if not target_file.exists():
                print(f"❌ [File Missing] in {file_path.name}: '{target_path_str}' does not exist.")
                errors_found = True
                continue

            # 2. Check if the anchor exists in the target file
            if fragment:
                valid_slugs = get_file_headings(target_file)
                if fragment not in valid_slugs:
                    print(f"❌ [Anchor Broken] in {file_path.name}: "
                          f"Heading '#{fragment}' not found in {target_file.name}")
                    errors_found = True

    if errors_found:
        print("\n💥 Link check failed. Please fix the broken links above.")
        sys.exit(1)
    else:
        print("\n✅ All relative links and anchor fragments are valid!")
        sys.exit(0)

if __name__ == '__main__':
    check_documentation()
