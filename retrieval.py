import re
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from parsing import build_chunked_corpus
from embeddings import load_model, embed_chunks, embed_query, contextualize

REPO_DIR = "./ros2_documentation-rolling"
EMBEDDINGS_FILE = "embeddings.npy"

def load_or_build_embeddings(model, chunks):
    # Reuse the saved matrix only if it still has one row per chunk
    if Path(EMBEDDINGS_FILE).exists():
        embeddings = np.load(EMBEDDINGS_FILE)
        if embeddings.shape[0] == len(chunks):
            return embeddings
    embeddings = embed_chunks(model, chunks)
    np.save(EMBEDDINGS_FILE, embeddings)
    return embeddings

def tokenize(text):
    # Lowercase word tokens: "ros2 bag record --topics" -> ["ros2", "bag", "record", "topics"]
    return re.findall(r"\w+", text.lower())

def build_bm25(chunks, contextual=False):
    # BM25 index over the chunk text (keyword matching, no embeddings).
    # contextual=True indexes "file title > section heading" + text, like the embeddings
    texts = [contextualize(chunk) if contextual else chunk["text"] for chunk in chunks]
    return BM25Okapi([tokenize(text) for text in texts])

def dense_scores(query, model, embeddings):
    # Both sides have norm 1, so the dot product IS the cosine similarity.
    # (N, 384) @ (384,) -> (N,): one score per chunk
    return embeddings @ embed_query(model, query)

def bm25_scores(query, bm25):
    return bm25.get_scores(tokenize(query))

def rrf_scores(score_lists, k=60):
    # Reciprocal Rank Fusion: fused(d) = sum over methods of 1 / (k + rank(d)).
    # Only ranks are used, so cosine (0..1) and BM25 (unbounded) need no rescaling.
    fused = np.zeros(len(score_lists[0]))
    for scores in score_lists:
        ranks = np.empty(len(scores))
        ranks[np.argsort(scores)[::-1]] = np.arange(1, len(scores) + 1)
        fused += 1 / (k + ranks)
    return fused

def top_k(scores, chunks, k=3):
    # argsort sorts ascending, so reverse it and keep the first k indices
    best = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), chunks[i]) for i in best]

def retrieve(query, model, chunks, embeddings, k=3):
    return top_k(dense_scores(query, model, embeddings), chunks, k)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "How do I create a ROS 2 package?"

    chunks = build_chunked_corpus(REPO_DIR)
    model = load_model()
    embeddings = load_or_build_embeddings(model, chunks)

    print("Query:", query)
    for rank, (score, chunk) in enumerate(retrieve(query, model, chunks, embeddings), start=1):
        print(f"\n#{rank}  score={score:.4f}  {chunk['file']} > {chunk['heading']} (chunk {chunk['chunk_id']})")
        print(chunk["text"])
