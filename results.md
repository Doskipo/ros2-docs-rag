# RAG retrieval evaluation: Recall@3 vs chunk size

## Setup

| Component | Choice |
|---|---|
| Corpus | ROS 2 documentation (`ros2_documentation-rolling`), 337 `.rst` files |
| Chunking | Heading-aware, fixed-size character windows with overlap (`parsing.py`) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) |
| Normalisation | L2, so that ‖e‖ = 1 for every chunk and query |
| Similarity | Dot product (equal to cosine similarity for unit vectors) |
| Retrieval | Top k = 3 chunks by score |

Chunk settings compared (overlap kept at 20% of the chunk size):

| Chunk size | Overlap | Number of chunks |
|---|---|---|
| 200 | 40 | 29,556 |
| 500 | 100 | 13,544 |

## What Recall@k measures

Recall answers: *of the items I should have found, how many did I find?*

$$\text{Recall} = \frac{\text{relevant items retrieved}}{\text{all relevant items}}$$

In this exercise each question has one correct ("gold") chunk. **Recall@k** asks whether that chunk is among the top k results: a hit counts as 1 and a miss as 0, averaged over all questions:

$$\text{Recall@3} = \frac{\#\text{ questions whose gold chunk is in the top 3}}{\#\text{ questions}}$$

This is the metric that matters for retrieval: the language model only sees the top k chunks, so if the answer is not among them it cannot answer, however good the model is.

### How a chunk is judged correct

Chunk ids change when the chunk size changes, so they cannot be used as labels. Each question instead has a **gold file plus a short phrase from the answer**. A retrieved chunk is correct if it comes from that file **and** contains the phrase. Every phrase is shorter than the smallest overlap (40 characters), so it always appears whole in at least one chunk.

## Questions

| # | Question | Gold file | Gold phrase |
|---|---|---|---|
| 1 | Which ROS domain ID range is safe to choose? | `About-Domain-ID.rst` | `between 0 and 101` |
| 2 | How do I create a new Python package? | `Creating-Your-First-ROS2-Package.rst` | `--build-type ament_python` |
| 3 | What happens to messages with the best effort reliability policy? | `About-Quality-of-Service-Settings.rst` | `network is not robust` |
| 4 | How can I save the data published on a topic to a file? | `Recording-And-Playing-Back-Data.rst` | `ros2 bag record` |
| 5 | Which command builds all the packages in my workspace? | `Colcon-Tutorial.rst` | `colcon build --symlink-install` |

## Results

| # | Question | 200 / 40 | 500 / 100 |
|---|---|---|---|
| 1 | Safe domain ID range | ✅ rank 1 | ✅ rank 1 |
| 2 | Create a Python package | ❌ | ❌ |
| 3 | Best effort reliability | ✅ rank 3 | ❌ |
| 4 | Save topic data to a file | ❌ | ✅ rank 2 |
| 5 | Build the workspace | ❌ | ✅ rank 1 |
| | **Recall@3** | **2/5 = 0.40** | **3/5 = 0.60** |

### Top 3 per question

`*` marks a chunk judged correct. Format: score, file › heading.

#### Chunk size 200, overlap 40

**Q1. Which ROS domain ID range is safe to choose?** (HIT at rank 1)
1. `*` 0.800 About-Domain-ID.rst › Choosing a domain ID (short version)
2. 0.751 Configuring-ROS2-Environment.rst › 3.1 (Optional) Set the `ROS_DOMAIN_ID` variable
3. 0.676 About-Domain-ID.rst › Participant constraints

**Q2. How do I create a new Python package?** (MISS)
1. 0.672 About-Build-System.rst › The `ament_package` package
2. 0.644 Creating-Your-First-ROS2-Package.rst › 1 Create a package
3. 0.642 Creating-Your-First-ROS2-Package.rst › 5 Examine package contents

**Q3. What happens to messages with the best effort reliability policy?** (HIT at rank 3)
1. 0.607 Quality-of-Service.rst › Add network traffic
2. 0.527 About-Quality-of-Service-Settings.rst › Quality of Service settings
3. `*` 0.512 About-Quality-of-Service-Settings.rst › QoS policies

**Q4. How can I save the data published on a topic to a file?** (MISS)
1. 0.638 Recording-A-Bag-From-Your-Own-Node-Py.rst › Background
2. 0.586 Recording-A-Bag-From-Your-Own-Node-Py.rst › Background
3. 0.572 Recording-A-Bag-From-Your-Own-Node-Py.rst › 2.1 Examine the code

**Q5. Which command builds all the packages in my workspace?** (MISS)
1. 0.660 Creating-A-Workspace.rst › Summary
2. 0.645 Colcon-Tutorial.rst › Source an underlay
3. 0.622 Creating-Your-First-ROS2-Package.rst › 2 Build a package

#### Chunk size 500, overlap 100

**Q1. Which ROS domain ID range is safe to choose?** (HIT at rank 1)
1. `*` 0.797 About-Domain-ID.rst › Choosing a domain ID (short version)
2. 0.686 About-Domain-ID.rst › Platform-specific constraints
3. 0.657 About-Domain-ID.rst › The ROS_DOMAIN_ID

**Q2. How do I create a new Python package?** (MISS)
1. 0.658 Creating-Your-First-ROS2-Package.rst › 1 Create a package
2. 0.641 Writing-A-Simple-Py-Publisher-And-Subscriber.rst › Prerequisites
3. 0.640 Migrating-Python-Package-Example.rst › Migrate the `setup.py`

**Q3. What happens to messages with the best effort reliability policy?** (MISS)
1. 0.539 About-Quality-of-Service-Settings.rst › Overview
2. 0.490 DDS-tuning.rst › Addressing common DDS tuning issues - how-to
3. 0.479 About-Quality-of-Service-Settings.rst › QoS compatibilities

**Q4. How can I save the data published on a topic to a file?** (HIT at rank 2)
1. 0.610 Recording-A-Bag-From-Your-Own-Node-Py.rst › 2.1 Examine the code
2. `*` 0.595 Recording-And-Playing-Back-Data.rst › 3.1 Record a single topic
3. 0.519 Understanding-ROS2-Topics.rst › 7 Publish data to a topic

**Q5. Which command builds all the packages in my workspace?** (HIT at rank 1)
1. `*` 0.617 Colcon-Tutorial.rst › Summary
2. 0.595 Ubuntu-Development-Setup-Pixi.rst › Build the code in the workspace
3. 0.585 Creating-A-Workspace.rst › 3 Clone a sample repo

## Analysis

- **Larger chunks did better on questions that need context (Q4, Q5).** A 200-character chunk is often little more than a bare command such as `colcon build --symlink-install`, with too little text to say what it is for. A 500-character chunk keeps the explanation around the command ("build the workspace", "record a topic"), so its embedding is closer to a question written in natural language.
- **Smaller chunks did better on a narrow definition (Q3).** The 200-character chunk is almost entirely the "best effort" bullet. In the 500-character chunk the same sentence is averaged together with the other QoS policies, which dilutes its signal. This follows from mean pooling: the model produces one vector per chunk by averaging its token vectors.
- **Some misses are near-misses.** In Q2 both sizes retrieved the right file and the "1 Create a package" section, but not the piece containing `ament_python`. In Q4 at size 200 a different but valid bag-recording tutorial ranked first. A looser criterion, such as "right file", would give higher recall for both sizes.
- **Small sample.** With 5 questions each one is worth 0.20, so the gap between 0.40 and 0.60 is a single question. The result suggests a direction but is not statistically meaningful. A sound comparison would need dozens of questions.

## Conclusion

On this question set, **chunk size 500 with overlap 100 gave the higher Recall@3 (0.60 against 0.40)**. The trade-off is that larger chunks carry more context for descriptive questions, while smaller chunks are more precise for narrow definitions. A larger question set would be needed to confirm the difference.

## Contextual retrieval (cheap version)

**Change:** before embedding, each chunk gets its file title and section heading prepended, for example `Recording And Playing Back Data > 3.1 Record a single topic`. Only the embedded text changes; the chunk text used for judging and for the LLM stays the same.

| # | Question | 200 | 200 + header | 500 | 500 + header |
|---|---|---|---|---|---|
| 1 | Safe domain ID range | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 |
| 2 | Create a Python package | ❌ | ❌ | ❌ | ❌ |
| 3 | Best effort reliability | ✅ 3 | ✅ 3 | ❌ | ❌ |
| 4 | Save topic data to a file | ❌ | ✅ 2 | ✅ 2 | ✅ 3 |
| 5 | Build the workspace | ❌ | ❌ | ✅ 1 | ✅ 2 |
| | **Recall@3** | **0.40** | **0.60** | **0.60** | **0.60** |

**Changes per query:**
- **Q1:** still rank 1; top score rose from 0.80 to 0.85.
- **Q2:** still a miss. With the header, `Python.rst › Package Setup` ranks first in both sizes. That file is a page about *testing*, but its title "Python" plus the heading "Package Setup" matches the query almost word for word.
- **Q3:** unchanged. At size 500 all three results now come from the right file, but not the chunk with the answer.
- **Q4:** at size 200, miss → rank 2, because the title "Recording And Playing Back Data" matches the question. At size 500, rank 2 → 3.
- **Q5:** at size 200, still a miss. At size 500, rank 1 → 2, because "Build the code in the workspace" headings from other pages now compete.

**Conclusions:**
- The header helps most with **small chunks**, which lack context on their own. Recall@3 for size 200 went from 0.40 to 0.60, matching size 500.
- It helps find the **right document** but not always the **right paragraph**, since every chunk in a section gets the same header.
- File names can **mislead** (Q2): "Python.rst" drops the folder path that says it is about testing. Using the full path or the document's real title, or having an LLM write the context as in Anthropic's full method, should fix this.
- As before, with 5 questions each change is a single question.


### Compared with Anthropic's full version
The cheap version only adds metadata that already exists. Adding an LLM text would fix the Q2 problem for example, since it gives context e.g. "This chunk is from the ROS 2 testing guida and shows how to configure setup.py for running pytest". Should be tested as another upgrade.


## Expanded set: 20 questions, BM25 and hybrid

**Changes:**
- 15 new questions (6–20) across services, actions, parameters, launch, tf2, rosdep, logging, discovery and composition. Most are paraphrased rather than copying the docs' wording.
- A question can now have several gold files when more than one page really answers it (e.g. the Python and C++ static-broadcaster tutorials). Pages that only mention the phrase in passing, such as changelogs, are not gold.
- Two new methods: **BM25** (keyword ranking, `rank-bm25`) and **Hybrid**, which fuses the dense and BM25 rankings with Reciprocal Rank Fusion (k = 60).
- New metric, **file recall@3**: at least one top-3 chunk comes from a gold file, even if it is not the paragraph with the answer.

### Summary

| Retrieval | Size | Recall@3 | MRR@3 | File recall@3 |
|---|---|---|---|---|
| Dense | 200 | 0.30 | 0.22 | 0.75 |
| Dense | 500 | 0.30 | 0.18 | 0.60 |
| Dense + contextual header | 200 | 0.40 | 0.26 | 0.50 |
| Dense + contextual header | 500 | 0.30 | 0.19 | 0.55 |
| BM25 | 200 | 0.25 | 0.23 | 0.65 |
| BM25 | 500 | 0.35 | 0.22 | 0.65 |
| Hybrid (RRF) | 200 | 0.35 | 0.26 | 0.60 |
| Hybrid (RRF) | 500 | 0.40 | 0.28 | 0.75 |

### Per question

Rank of the correct chunk in the top 3 (– = not in the top 3). Ctx = dense + contextual header.

| # | Question | Dense 200 | Ctx 200 | BM25 200 | Hybrid 200 | Dense 500 | Ctx 500 | BM25 500 | Hybrid 500 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Safe domain ID range | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | Create a Python package | – | – | – | – | – | – | – | – |
| 3 | Best effort reliability | 3 | 3 | 2 | 2 | – | – | – | – |
| 4 | Save topic data to a file | – | 2 | – | 3 | 2 | 3 | 2 | 1 |
| 5 | Build all workspace packages | – | – | – | – | 1 | 2 | – | 2 |
| 6 | Request-reply between nodes | – | – | – | – | – | – | – | – |
| 7 | Long task with progress and cancel | 2 | 3 | 1 | 1 | – | – | 1 | 2 |
| 8 | Save node parameters to YAML | – | – | – | – | – | – | – | – |
| 9 | Launch file languages | 2 | 2 | 1 | 3 | 3 | – | 2 | – |
| 10 | Tool to publish a fixed transform | – | – | – | – | – | – | – | 3 |
| 11 | Install workspace dependencies | – | – | – | – | – | – | 2 | 1 |
| 12 | Run in every new terminal | – | – | – | – | – | – | – | – |
| 13 | Check installation for problems | – | 2 | – | – | – | 1 | – | – |
| 14 | Print debug messages | – | – | – | – | – | – | – | – |
| 15 | Stop discovery on other computers | – | – | – | – | – | – | – | – |
| 16 | Quaternion components | – | – | – | – | – | – | 3 | 3 |
| 17 | Several nodes in one process | – | – | – | – | – | – | – | – |
| 18 | Call a service from the terminal | 1 | 1 | – | 1 | 2 | 2 | – | – |
| 19 | Log severity levels | 1 | 1 | 1 | 1 | 3 | 2 | 2 | 1 |
| 20 | Measure topic message rate | – | – | – | – | – | – | – | – |

**Observations:**
- **Strict recall is low for every method (0.25–0.40), and 8 questions are missed by all of them.** Most of these are near-misses: the right page, often the right section, is retrieved but not the chunk with the answer. For example, in the hybrid 500 run Q8 retrieves the section "Save the parameters of a node to a file" but not the chunk with `ros2 param dump`, and Q15 and Q17 rank their gold page first with a neighbouring chunk. File recall@3 (0.50–0.75) shows this.
- **Hybrid with 500-character chunks is the best overall:** top or tied-top on all three metrics. It is the only setting that finds Q10, and it lifts Q11 from rank 2 (BM25) to rank 1.
- **BM25 and dense fail on different questions.** BM25 finds commands named in the question's wording (Q11 rosdep, Q16 quaternion) but misses Q18 entirely. Dense handles paraphrases like Q18 but misses Q11 and Q16. That complementarity is why fusing them helps.
- **The contextual header gives the best strict recall at size 200 (0.40) but the worst file recall (0.50).** Prepending page titles likely pulls in other pages with similar titles (as with `Python.rst` in Q2), so the top 3 more often contain no gold page at all.
- **With 20 questions each one is worth 0.05.** Most gaps between methods are one or two questions, so the ranking of methods is a direction, not a firm result.

## Contextual header with BM25 and hybrid

**Change:** the contextual header (file title + section heading) is now also tested on BM25 and in two hybrids:
- **Hybrid (dense + header, BM25):** the header only on the dense side; BM25 indexes the plain text.
- **Hybrid (both + header):** the header on both the dense and the BM25 side, as in Anthropic's method.

| Retrieval | Size | Recall@3 | MRR@3 | File recall@3 |
|---|---|---|---|---|
| BM25 + header | 200 | 0.35 | 0.29 | 0.60 |
| BM25 + header | 500 | 0.30 | 0.21 | 0.55 |
| Hybrid (dense + header, BM25) | 200 | 0.40 | 0.38 | 0.65 |
| Hybrid (dense + header, BM25) | 500 | 0.50 | 0.33 | 0.75 |
| Hybrid (both + header) | 200 | 0.45 | 0.42 | 0.65 |
| Hybrid (both + header) | 500 | 0.35 | 0.27 | 0.70 |

Rank of the correct chunk, compared with the plain hybrid (– = not in the top 3). Questions missed by all of these are left out.

| # | Question | Hybrid 200 | Dense+h, BM25 200 | Both+h 200 | Hybrid 500 | Dense+h, BM25 500 | Both+h 500 |
|---|---|---|---|---|---|---|---|
| 1 | Safe domain ID range | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | Best effort reliability | 2 | 1 | 1 | – | 2 | 2 |
| 4 | Save topic data to a file | 3 | 1 | 1 | 1 | 1 | 1 |
| 5 | Build all workspace packages | – | – | – | 2 | 3 | 3 |
| 7 | Long task with progress and cancel | 1 | 1 | 1 | 2 | 3 | – |
| 8 | Save node parameters to YAML | – | – | 3 | – | – | – |
| 9 | Launch file languages | 3 | 1 | 1 | – | – | – |
| 10 | Tool to publish a fixed transform | – | – | – | 3 | 2 | – |
| 11 | Install workspace dependencies | – | – | – | 1 | 1 | 2 |
| 16 | Quaternion components | – | 2 | 1 | 3 | 2 | – |
| 18 | Call a service from the terminal | 1 | 1 | 1 | – | 2 | 1 |
| 19 | Log severity levels | 1 | 1 | 1 | 1 | 1 | 1 |

**Observations:**
- **The header works better inside the hybrid than on its own.** On their own, dense + header and BM25 + header are mixed: better strict recall at size 200, equal or worse at size 500, and lower file recall. Inside the hybrid, the header on the dense side gives the best strict recall (0.50 at size 500), and the header on both sides gives the best MRR (0.42 at size 200).
- **The gains show up mostly as higher ranks.** At size 200, Q3, Q4 and Q9 move up to rank 1 and Q16 enters the top 3. This is why MRR rises more than recall.
- **No single setting wins every metric.** The best strict recall, MRR and file recall come from three different rows, and the header on the BM25 side helps at size 200 but hurts at size 500 (Q7, Q10, Q16 drop out).
- **Overfitting risk.** These are 7 methods × 2 sizes tried on the same 20 questions, and the best rows lead by one or two questions. The best row on this set may not stay best on new questions. A held-out question set would be needed to choose a winner reliably.

## Reproduce

```powershell
python evaluate.py
```

Chunk sizes and questions are defined at the top of `evaluate.py` (`CHUNK_SETTINGS`, `QUESTIONS`). Every run evaluates all seven methods (dense, BM25 and hybrid, each with and without the contextual header, plus the hybrid with the header on both sides) at each chunk size.
