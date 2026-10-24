import numpy as np
from sentence_transformers import SentenceTransformer

from parsing import build_chunked_corpus




MODEL_NAME = "all-MiniLM-L6-v2"

def load_model():
    # Downloads the model the first time (~90 MB), then loads it from the local cache
    return SentenceTransformer(MODEL_NAME)

def normalize(vectors):
    # Divide each row by its L2 norm so that ||e|| = 1
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid dividing by zero on an empty vector
    return vectors / norms

def contextualize(chunk):
    # Cheap contextual retrieval: prepend "file title > section heading" to the chunk.
    # "Recording-And-Playing-Back-Data.rst" -> "Recording And Playing Back Data"
    title = chunk["file"].removesuffix(".rst").replace("-", " ").replace("_", " ")
    heading = chunk["heading"].replace("``", "")  # drop rst code markup
    return f"{title} > {heading}\n{chunk['text']}"

def embed_chunks(model, chunks, batch_size=32, contextual=False):
    # Only the text sent to the model changes; chunk["text"] itself is left untouched
    texts = [contextualize(chunk) if contextual else chunk["text"] for chunk in chunks]

    # One row per chunk, 384 columns (the output size of all-MiniLM-L6-v2)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return normalize(embeddings)

def embed_query(model, query):
    # Queries must go through the exact same model and normalization as the chunks
    embedding = model.encode([query], convert_to_numpy=True)
    return normalize(embedding)[0]

if __name__ == "__main__":
    corpus_chunks = build_chunked_corpus("./ros2_documentation-rolling")
    model = load_model()
    embeddings = embed_chunks(model, corpus_chunks)

    print("Chunks:", len(corpus_chunks))
    print("Embeddings shape:", embeddings.shape)

    # Sanity check: every norm should be 1.0 (up to float rounding)
    norms = np.linalg.norm(embeddings, axis=1)
    print("Min norm:", norms.min(), "Max norm:", norms.max())

    # Save so you don't have to re-embed every run (row i <-> corpus_chunks[i])
    np.save("embeddings.npy", embeddings)
