# rag-practice

A small retrieval pipeline over the ROS 2 documentation that chunks the docs, embeds them with `all-MiniLM-L6-v2`, and is evaluated on hand-labelled questions. 🚧 Work in progress.

## Corpus

The [ROS 2 documentation](https://github.com/ros2/ros2_documentation) (rolling branch, 337 `.rst` files), © Open Robotics and contributors, licensed under CC BY 4.0. It is not included in this repo.

## Run

```bash
pip install -r requirements.txt
git clone https://github.com/ros2/ros2_documentation.git ros2_documentation-rolling
python evaluate.py          # recall@3 for every setting; or: python retrieval.py "your question"
```

## Results

20 hand-labelled questions, top k = 3.

- **Recall@3**: the chunk containing the answer is in the top 3.
- **MRR@3**: average of 1/rank of that chunk, counting 0 if it is not in the top 3.
- **File recall@3**: at least one top-3 chunk comes from a page that answers the question (right page, maybe not the right paragraph).

BM25 = keyword ranking over the chunk text (`rank-bm25`). Hybrid = dense and BM25 rankings combined with Reciprocal Rank Fusion (RRF, k = 60), which merges by rank so the two score scales need no normalisation. Chunk size is in characters. Bold = best in the column across both tables.

### Without contextual header

| Retrieval | Chunk size | Recall@3 | MRR@3 | File recall@3 |
|---|---|---|---|---|
| Dense | 200 | 0.30 | 0.22 | **0.75** |
| Dense | 500 | 0.30 | 0.18 | 0.60 |
| BM25 | 200 | 0.25 | 0.23 | 0.65 |
| BM25 | 500 | 0.35 | 0.22 | 0.65 |
| Hybrid (dense + BM25) | 200 | 0.35 | 0.26 | 0.60 |
| Hybrid (dense + BM25) | 500 | 0.40 | 0.28 | **0.75** |

### With contextual header

File title and section heading prepended to each chunk before indexing, e.g. `Recording And Playing Back Data > 3.1 Record a single topic`.

| Retrieval | Chunk size | Recall@3 | MRR@3 | File recall@3 |
|---|---|---|---|---|
| Dense + header | 200 | 0.40 | 0.26 | 0.50 |
| Dense + header | 500 | 0.30 | 0.19 | 0.55 |
| BM25 + header | 200 | 0.35 | 0.29 | 0.60 |
| BM25 + header | 500 | 0.30 | 0.21 | 0.55 |
| Hybrid (dense + header, BM25) | 200 | 0.40 | 0.38 | 0.65 |
| Hybrid (dense + header, BM25) | 500 | **0.50** | 0.33 | **0.75** |
| Hybrid (both + header) | 200 | 0.45 | **0.42** | 0.65 |
| Hybrid (both + header) | 500 | 0.35 | 0.27 | 0.70 |

With 20 questions each one is worth 0.05, so differences of one or two questions are still within noise. Per-question details are in [results.md](results.md).


## Key findings

From the results one can conclude that

1. no chunk size wins across methods,
2. the header (contextual retrieval) helps small chunks but can misled,
3. MRR shows the drop in rank that recall hides,
4. BM25 fails on paraphrased questions,
5. and the RRF hybrid beats either method alone, and adding the contextual header inside the hybrid gives the best scores (recall@3 0.50, MRR@3 0.42), though no single setting wins every metric.

How a sentence embedding is built, and why that matters for these results: [NOTES.md](NOTES.md).

## Next


LLM-judge evaluation of generated answers.
