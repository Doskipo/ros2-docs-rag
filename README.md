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

5 hand-labelled questions, top k = 3. MRR@3 is the average of 1/rank of the correct chunk, counting 0 if it is not in the top 3.

| Retrieval | Chunk size | Recall@3 | MRR@3 |
|---|---|---|---|
| Dense | 200 | 0.40 | 0.27 |
| Dense | 500 | 0.60 | 0.50 |
| Dense + contextual header | 200 | 0.60 | 0.37 |
| Dense + contextual header | 500 | 0.60 | 0.37 |
| BM25 | 200 | 0.40 | 0.30 |
| BM25 | 500 | 0.40 | 0.30 |
| Hybrid (dense + BM25, RRF) | 200 | 0.60 | 0.37 |
| Hybrid (dense + BM25, RRF) | 500 | 0.60 | 0.50 |

Contextual header = file title and section heading prepended to each chunk before embedding. With only 5 questions, each one is worth 0.20, so treat the differences as indicative. Per-question details are in [results.md](results.md).

BM25 = keyword ranking over the raw chunk text (`rank-bm25`). Hybrid = dense and BM25 rankings combined with Reciprocal Rank Fusion (RRF, k = 60), which merges by rank so the two score scales need no normalisation.


## Key findings

From the results one can conclude that

1. larger chunks win on context-heavy questions,
2. the header (contextual retrieval) helps small chunks but can misled,
3. and MRR shows the drop in rank that recall hides.

## Next


LLM-judge evaluation of generated answers.
