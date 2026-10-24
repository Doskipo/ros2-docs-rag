from pathlib import Path

def build_chunked_corpus(repo_dir, chunk_size=500, overlap=100):
    # Find the .rst files anywhere in the repo
    rst_files = list(Path(repo_dir).rglob('*.rst'))[:337]

    chunks = []
    chunk_id = 0
    step = chunk_size - overlap
    
    for file_path in rst_files:
        file_name = file_path.name
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            
        current_heading = "Introduction"
        current_text = ""
        
        for i in range(len(lines)):
            line = lines[i].strip()
            
            # Look ahead to see if the next line is a heading underline
            if i < len(lines) - 1:
                next_line = lines[i+1].strip()
                if len(next_line) > 0 and next_line == next_line[0] * len(next_line) and next_line[0] in "=-~^":
                    # We hit a new heading. Chunk the text accumulated so far.
                    if current_text:
                        for j in range(0, len(current_text), step):
                            chunk_text = current_text[j:j + chunk_size]
                            chunks.append({
                                "file": file_name,
                                "heading": current_heading,
                                "chunk_id": chunk_id,
                                "text": chunk_text
                            })
                            chunk_id += 1
                        current_text = ""
                    current_heading = line
                    continue 
            
            # Skip the actual underline characters from being added as text
            if not (len(line) > 0 and line == line[0] * len(line) and line[0] in "=-~^"):
                current_text += line + " "

        # Chunk any remaining text at the end of the file
        if current_text:
            for j in range(0, len(current_text), step):
                chunk_text = current_text[j:j + chunk_size]
                chunks.append({
                    "file": file_name,
                    "heading": current_heading,
                    "chunk_id": chunk_id,
                    "text": chunk_text
                })
                chunk_id += 1
                
    return chunks

# Usage: corpus_chunks = build_chunked_corpus("./ros2_documentation-rolling")