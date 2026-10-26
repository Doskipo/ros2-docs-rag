from parsing import build_chunked_corpus
from embeddings import load_model, embed_chunks
from retrieval import REPO_DIR, build_bm25, dense_scores, bm25_scores, rrf_scores, top_k

K = 3

# (chunk_size, overlap) pairs to compare. Overlap stays at 20% of the size.
CHUNK_SETTINGS = [(200, 40), (500, 100)]

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

def evaluate(name, score_fn, chunks):
    # score_fn(question) -> one score per chunk; higher is better
    print(f"\n--- {name} ---")
    hits = 0
    reciprocal_ranks = []
    for gold in QUESTIONS:
        results = top_k(score_fn(gold["question"]), chunks, K)

        # Rank (1..K) of the first correct chunk, or None if it's not in the top K
        hit_rank = next((rank for rank, (_, chunk) in enumerate(results, start=1)
                         if is_relevant(chunk, gold)), None)
        hits += hit_rank is not None
        # MRR@K: 1/rank of the correct chunk, 0 if it's not in the top K
        reciprocal_ranks.append(1 / hit_rank if hit_rank else 0)

        status = f"HIT @ rank {hit_rank}" if hit_rank else "MISS"
        print(f"\n[{status}] {gold['question']}")
        for rank, (score, chunk) in enumerate(results, start=1):
            mark = "*" if is_relevant(chunk, gold) else " "
            print(f"   {mark} #{rank} {score:.3f}  {chunk['file']} > {chunk['heading']}")

    recall = hits / len(QUESTIONS)
    mrr = sum(reciprocal_ranks) / len(QUESTIONS)
    print(f"\nRecall@{K} = {hits}/{len(QUESTIONS)} = {recall:.2f}   MRR@{K} = {mrr:.2f}")
    return recall, mrr

if __name__ == "__main__":
    model = load_model()
    summary = []

    for chunk_size, overlap in CHUNK_SETTINGS:
        chunks = build_chunked_corpus(REPO_DIR, chunk_size=chunk_size, overlap=overlap)
        print(f"\n=== chunk_size={chunk_size}, overlap={overlap} ({len(chunks)} chunks) ===")

        # Build every index once per chunk size, then reuse it for each method
        plain = embed_chunks(model, chunks)
        contextual = embed_chunks(model, chunks, contextual=True)
        bm25 = build_bm25(chunks)

        methods = {
            "Dense": lambda q: dense_scores(q, model, plain),
            "Dense + contextual header": lambda q: dense_scores(q, model, contextual),
            "BM25": lambda q: bm25_scores(q, bm25),
            "Hybrid (dense + BM25, RRF)": lambda q: rrf_scores(
                [dense_scores(q, model, plain), bm25_scores(q, bm25)]),
        }
        for name, score_fn in methods.items():
            recall, mrr = evaluate(name, score_fn, chunks)
            summary.append((name, chunk_size, recall, mrr))

    print("\n=== Summary ===")
    for name, chunk_size, recall, mrr in summary:
        print(f"{name:<28} chunk_size={chunk_size:<5} Recall@{K} = {recall:.2f}   MRR@{K} = {mrr:.2f}")
