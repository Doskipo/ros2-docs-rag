from parsing import build_chunked_corpus
from embeddings import load_model, embed_chunks
from retrieval import retrieve, REPO_DIR

K = 3

# (chunk_size, overlap, contextual) settings to compare. Overlap stays at 20% of the size.
# contextual=True prepends "file title > section heading" to each chunk before embedding.
CHUNK_SETTINGS = [
    (200, 40, False),
    (500, 100, False),
    (200, 40, True),
    (500, 100, True),
]

# Each question has a "gold" answer: the file it lives in plus a short phrase
# that appears in the answer. A retrieved chunk counts as correct if it comes
# from that file AND contains the phrase. We can't use chunk_id as the label,
# because chunk ids change when the chunk size changes.
# Phrases are shorter than the smallest overlap (40 chars), so every phrase is
# guaranteed to sit whole inside at least one chunk.
QUESTIONS = [
    {
        "question": "Which ROS domain ID range is safe to choose?",
        "file": "About-Domain-ID.rst",
        "phrase": "between 0 and 101",
    },
    {
        "question": "How do I create a new Python package?",
        "file": "Creating-Your-First-ROS2-Package.rst",
        "phrase": "--build-type ament_python",
    },
    {
        "question": "What happens to messages with the best effort reliability policy?",
        "file": "About-Quality-of-Service-Settings.rst",
        "phrase": "network is not robust",
    },
    {
        "question": "How can I save the data published on a topic to a file?",
        "file": "Recording-And-Playing-Back-Data.rst",
        "phrase": "ros2 bag record",
    },
    {
        "question": "Which command builds all the packages in my workspace?",
        "file": "Colcon-Tutorial.rst",
        "phrase": "colcon build --symlink-install",
    },
]

def is_relevant(chunk, gold):
    return chunk["file"] == gold["file"] and gold["phrase"] in chunk["text"]

def evaluate(model, chunk_size, overlap, contextual):
    chunks = build_chunked_corpus(REPO_DIR, chunk_size=chunk_size, overlap=overlap)
    embeddings = embed_chunks(model, chunks, contextual=contextual)

    print(f"\n=== chunk_size={chunk_size}, overlap={overlap}, contextual={contextual} "
          f"({len(chunks)} chunks) ===")
    hits = 0
    for gold in QUESTIONS:
        results = retrieve(gold["question"], model, chunks, embeddings, k=K)

        # Rank (1..K) of the first correct chunk, or None if it's not in the top K
        hit_rank = next((rank for rank, (_, chunk) in enumerate(results, start=1)
                         if is_relevant(chunk, gold)), None)
        hits += hit_rank is not None

        status = f"HIT @ rank {hit_rank}" if hit_rank else "MISS"
        print(f"\n[{status}] {gold['question']}")
        for rank, (score, chunk) in enumerate(results, start=1):
            mark = "*" if is_relevant(chunk, gold) else " "
            print(f"   {mark} #{rank} {score:.3f}  {chunk['file']} > {chunk['heading']}")

    recall = hits / len(QUESTIONS)
    print(f"\nRecall@{K} = {hits}/{len(QUESTIONS)} = {recall:.2f}")
    return recall

if __name__ == "__main__":
    model = load_model()
    summary = {settings: evaluate(model, *settings) for settings in CHUNK_SETTINGS}

    print("\n=== Summary ===")
    for (chunk_size, overlap, contextual), recall in summary.items():
        print(f"chunk_size={chunk_size:<5} overlap={overlap:<4} contextual={contextual!s:<6} "
              f"Recall@{K} = {recall:.2f}")
