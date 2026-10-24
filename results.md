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


## Reproduce

```powershell
python evaluate.py
```

Chunk settings (including the `contextual` flag) and questions are defined at the top of `evaluate.py` (`CHUNK_SETTINGS`, `QUESTIONS`).
