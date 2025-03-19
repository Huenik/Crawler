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
    Given a list of URLs, group them by their 'path prefix' up to
    (path_length - parents) segments.

    Example:
      If parents=1, we effectively remove the last path segment from each URL
      to define its grouping prefix. Pages that share that prefix go together.

    Returns a dict where:
      key = prefix_string (the joined path segments up to path_length - parents)
      val = list of (url, filename) tuples that match that prefix
    """
    groups = {}

    for (url, filename) in urls:
        segments = get_path_segments(url)

        # We define the grouping prefix by dropping the last 'parents' segments.
        # e.g. if segments = ["Category:Arma_Reforger","Modding","Assets","1","2","3"]
        # and parents=1, we keep everything except the last one:
        # => prefix_segments = ["Category:Arma_Reforger","Modding","Assets","1","2"]
        cutoff = max(0, len(segments) - parents)
        prefix_segments = segments[:cutoff]

        # Convert the list of segments into a string for dict key
        # so e.g. prefix_segments=["Category:Arma_Reforger","Modding","Assets","1","2"]
        # becomes "Category:Arma_Reforger/Modding/Assets/1/2"
        prefix_str = "/".join(prefix_segments)

        # Add to the dictionary
        if prefix_str not in groups:
            groups[prefix_str] = []
        groups[prefix_str].append((url, filename))

    return groups


def combine_group(prefix_key, items, input_dir, output_dir):
    """
    Combine the contents of all files in `items` into a single HTML file.
      - prefix_key is a string (the grouping prefix).
      - items is a list of (url, filename) for that prefix.
      - input_dir is where the .html files live.
      - output_dir is where we store the combined .html file.
    """

    # Build a single filename for the combined output
    # Because prefix_key can be empty or contain '/', let's sanitize it
    # Replace slashes with underscores, etc.
    if prefix_key == "":
        sanitized_prefix = "root"
    else:
        sanitized_prefix = prefix_key.replace("/", "_").replace(":", "_")

    combined_filename = f"combined_{sanitized_prefix}.html"
    out_path = os.path.join(output_dir, combined_filename)

    # Read and concatenate
    combined_content = []
    for (url, fname) in items:
        file_path = os.path.join(input_dir, fname)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()
                # You might want to insert some markers, e.g. a line with <hr> or
                # a comment referencing the original URL, for clarity:
                combined_content.append(f"<!-- START OF {url} -->\n{html}\n<!-- END OF {url} -->\n")
        else:
            # The file doesn't exist? Log or skip
            print(f"[!] Warning: {file_path} not found, skipping...")

    # Write them all out
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(combined_content))

    print(f"[+] Created combined file for prefix '{prefix_key}' => {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Combine downloaded HTML files that share the same parent prefix."
    )
    parser.add_argument(
        '-m', '--map',
        required=True,
        help="Path to the map file (tab- or space-separated) that lists URL and downloaded filename."
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
        help="Number of path segments to treat as 'parents' to group by. (default: 1)"
    )
    args = parser.parse_args()

    # Ensure the output directory exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 1) Read the map file
    # The map file is assumed to have lines like:
    #   <URL>  <filename>
    # If you used tab as a separator, we can split on `\t`. If you used space or multi-spaces,
    # you'll want to do a `.split()` or `re.split()`. Adjust as necessary.
    url_filename_pairs = []
    with open(args.map, "r", encoding="utf-8") as mf:
        for line in mf:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')  # if you used tab
            # If you used spaces, do: parts = line.split()
            if len(parts) != 2:
                print(f"[!] Skipping malformed line in map file: {line}")
                continue
            url, fname = parts
            url_filename_pairs.append((url, fname))

    # 2) Group them by prefix
    groups = group_urls_by_prefix(url_filename_pairs, parents=args.parents)

    # 3) Combine each group into a single HTML file
    for prefix_key, items in groups.items():
        if not items:
            continue
        combine_group(prefix_key, items, args.input, args.output)

    print("\nAll done! Combined HTML files are in:", args.output)


if __name__ == "__main__":
    main()
