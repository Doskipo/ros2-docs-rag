import sys
from pathlib import Path

import numpy as np

from parsing import build_chunked_corpus
from embeddings import load_model, embed_chunks, embed_query

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

def retrieve(query, model, chunks, embeddings, k=3):
    q = embed_query(model, query)

    # Both sides have norm 1, so the dot product IS the cosine similarity.
    # (N, 384) @ (384,) -> (N,): one score per chunk
    scores = embeddings @ q

    # argsort sorts ascending, so reverse it and keep the first k indices
    top_k = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), chunks[i]) for i in top_k]

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "How do I create a ROS 2 package?"

    chunks = build_chunked_corpus(REPO_DIR)
    model = load_model()
    embeddings = load_or_build_embeddings(model, chunks)

    print("Query:", query)
    for rank, (score, chunk) in enumerate(retrieve(query, model, chunks, embeddings), start=1):
        print(f"\n#{rank}  score={score:.4f}  {chunk['file']} > {chunk['heading']} (chunk {chunk['chunk_id']})")
        print(chunk["text"])



"""
A little bit of my explanation:

text is mapped to tokens. These tokens correspond to a particular vector
in a >300 dimensional space (for this model) as a look up table. Then, 
perform 6 transform layers to add context and finally pool all the text.
The text could be a 10 word query or a 500 word text; and all of them 
finish as a single >300 vector. There are many consequences on that.
The cosine similarity can catch as much as it can.

"""