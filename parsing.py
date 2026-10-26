from pathlib import Path

HEADING_CHARS = "=-~^"

def is_underline(line):
    # An rst heading underline is one repeated character, e.g. "=====" or "-----"
    return len(line) > 0 and line == line[0] * len(line) and line[0] in HEADING_CHARS

def split_into_chunks(text, file_name, heading, chunk_size, overlap, start_id):
    # Fixed-size character windows; each one starts `chunk_size - overlap` after the previous
    step = chunk_size - overlap
    return [
        {
            "file": file_name,
            "heading": heading,
            "chunk_id": start_id + n,
            "text": text[j:j + chunk_size],
        }
        for n, j in enumerate(range(0, len(text), step))
    ]

def build_chunked_corpus(repo_dir, chunk_size=500, overlap=100):
    # Every .rst file anywhere in the repo, sorted so chunk ids are the same on every machine
    rst_files = sorted(Path(repo_dir).rglob("*.rst"))

    chunks = []
    for file_path in rst_files:
        lines = file_path.read_text(encoding="utf-8").split("\n")

        # (heading, text) for every section of the file
        sections = []
        current_heading = "Introduction"
        current_text = ""

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()

            # If the next line underlines this one, this line is a new heading:
            # close the section accumulated so far and start a new one
            if i < len(lines) - 1 and is_underline(lines[i + 1].strip()):
                sections.append((current_heading, current_text))
                current_heading = line
                current_text = ""
                continue

            # Skip the underline itself
            if not is_underline(line):
                current_text += line + " "

        sections.append((current_heading, current_text))

        for heading, text in sections:
            if text:
                chunks += split_into_chunks(text, file_path.name, heading,
                                            chunk_size, overlap, start_id=len(chunks))

    return chunks

# Usage: corpus_chunks = build_chunked_corpus("./ros2_documentation-rolling")
