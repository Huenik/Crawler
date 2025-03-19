#!/usr/bin/env python3

import argparse
import os
from urllib.parse import urlparse

def get_path_segments(url):
    """
    Returns a list of path segments from the given URL.
    Example: 'https://domain.com/a/b/c' -> ['a', 'b', 'c']
    """
    parsed = urlparse(url)
    # Strip leading/trailing slashes and split on '/'
    path_str = parsed.path.strip('/')
    if not path_str:
        return []
    return path_str.split('/')

def group_urls_by_prefix(urls, parents=1):
    """
    Given a list of (url, filename) pairs, group them by their 'path prefix'
    up to (path_length - parents) segments.

    Example:
      If parents=1, we remove the last path segment from each URL to define its grouping prefix.
      So pages that share that prefix go together.

    Returns a dict:
      key = prefix_string (the joined path segments up to path_length - parents)
      val = list of (url, filename) tuples that match that prefix
    """
    groups = {}

    for (url, filename) in urls:
        segments = get_path_segments(url)
        # Drop the last 'parents' segments to form the grouping prefix.
        cutoff = max(0, len(segments) - parents)
        prefix_segments = segments[:cutoff]

        # Convert list of segments into a single string
        prefix_str = "/".join(prefix_segments)

        if prefix_str not in groups:
            groups[prefix_str] = []
        groups[prefix_str].append((url, filename))

    return groups

def combine_group(prefix_key, items, input_dir, output_dir):
    """
    Combine the contents of all files in `items` into a single HTML file.
      - prefix_key is a string (the grouping prefix).
      - items is a list of (url, filename) pairs for that prefix.
      - input_dir is where the .html files live.
      - output_dir is where the combined .html file is saved.
    """
    # Build a single filename for the combined output.
    # Because prefix_key can contain '/', ':', etc., replace them with underscores.
    if prefix_key == "":
        sanitized_prefix = "root"
    else:
        sanitized_prefix = prefix_key.replace("/", "_").replace(":", "_")

    combined_filename = f"combined_{sanitized_prefix}.html"
    out_path = os.path.join(output_dir, combined_filename)

    combined_content = []
    for (url, fname) in items:
        file_path = os.path.join(input_dir, fname)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()
                # Insert a comment referencing the original URL for clarity
                combined_content.append(f"<!-- START OF {url} -->\n{html}\n<!-- END OF {url} -->\n")
        else:
            print(f"[!] Warning: {file_path} not found, skipping...")

    # Write them all out
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(combined_content))

    print(f"[+] Created combined file for prefix '{prefix_key}' => {out_path}")

def combine_all(map_file, input_dir, output_dir, parents=1):
    """
    High-level function to read the map file, group the URLs, and combine them.
    """
    if not os.path.exists(map_file):
        print(f"[!] Map file not found: {map_file}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1) Read URL->filename pairs from the map file
    url_filename_pairs = []
    with open(map_file, "r", encoding="utf-8") as mf:
        for line in mf:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')  # we assume a tab separator
            if len(parts) != 2:
                print(f"[!] Skipping malformed line in map file: {line}")
                continue
            url, fname = parts
            url_filename_pairs.append((url, fname))

    # 2) Group them by prefix
    groups = group_urls_by_prefix(url_filename_pairs, parents=parents)

    # 3) Combine each group
    for prefix_key, items in groups.items():
        if not items:
            continue
        combine_group(prefix_key, items, input_dir, output_dir)

def main():
    parser = argparse.ArgumentParser(
        description="Combine downloaded HTML files that share the same parent prefix."
    )
    parser.add_argument(
        '-m', '--map',
        required=True,
        help="Path to the map file (tab-separated) that lists URL and downloaded filename."
    )
    parser.add_argument(
        '-i', '--input',
        default='downloaded_html',
        help="Directory with the individual downloaded HTML files (default: 'downloaded_html')."
    )
    parser.add_argument(
        '-o', '--output',
        default='combined_html',
        help="Directory where combined HTML files will be stored (default: 'combined_html')."
    )
    parser.add_argument(
        '-p', '--parents',
        type=int,
        default=1,
        help="Number of path segments to treat as 'parents' to group by (default=1)."
    )
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    combine_all(
        map_file=args.map,
        input_dir=args.input,
        output_dir=args.output,
        parents=args.parents
    )

    print("\nAll done! Combined HTML files are in:", args.output)

if __name__ == "__main__":
    main()
