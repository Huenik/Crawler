import os
import glob


def combine_html_files(directory, output_file_prefix):
    # Define maximum size in bytes (5MB)
    max_size = 5 * 1024 * 1024
    # Get a sorted list of all .html files in the directory
    html_files = sorted(glob.glob(os.path.join(directory, "*.html")))

    piece_index = 1
    current_chunk = []  # to store file contents
    current_chunk_size = 0  # in bytes

    for html_file in html_files:
        file_size = os.path.getsize(html_file)
        if file_size > max_size:
            print(f"Skipping '{html_file}' (size: {file_size} bytes) because it exceeds 5MB.")
            continue

        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Get the size in bytes of the content when encoded as UTF-8
        content_bytes = content.encode('utf-8')
        content_size = len(content_bytes)

        # Determine size of the separator if needed (we use two newlines as separator)
        separator = "\n\n"
        separator_size = len(separator.encode('utf-8')) if current_chunk else 0

        # If adding this file would exceed the max size, write out the current chunk
        if current_chunk_size + separator_size + content_size > max_size:
            output_filename = f"{output_file_prefix}_{piece_index}.html"
            with open(output_filename, 'w', encoding='utf-8') as out_file:
                out_file.write(separator.join(current_chunk))
            print(f"Wrote '{output_filename}' (approx. {current_chunk_size} bytes).")
            piece_index += 1
            current_chunk = []
            current_chunk_size = 0

        # Add the current file's content to the chunk
        if current_chunk:
            # Add separator if chunk is not empty
            current_chunk_size += separator_size
        current_chunk.append(content)
        current_chunk_size += content_size

    # Write any remaining content to a final piece
    if current_chunk:
        output_filename = f"{output_file_prefix}_{piece_index}.html"
        with open(output_filename, 'w', encoding='utf-8') as out_file:
            out_file.write(separator.join(current_chunk))
        print(f"Wrote '{output_filename}' (approx. {current_chunk_size} bytes).")


if __name__ == "__main__":
    directory = input("Enter the directory path containing HTML files (press Enter for current directory): ")
    if not directory:
        directory = "."
    output_file_prefix = input("Enter the output file prefix (press Enter for 'combined'): ")
    if not output_file_prefix:
        output_file_prefix = "combined"

    combine_html_files(directory, output_file_prefix)
