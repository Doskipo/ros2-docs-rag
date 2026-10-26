from parsing import build_chunked_corpus
from embeddings import load_model, embed_chunks
from retrieval import REPO_DIR, build_bm25, dense_scores, bm25_scores, rrf_scores, top_k

K = 3

# (chunk_size, overlap) pairs to compare. Overlap stays at 20% of the size.
CHUNK_SETTINGS = [(200, 40), (500, 100)]

# Each question has a "gold" answer: the file(s) that answer it plus a short phrase
# from the answer. A retrieved chunk counts as correct if it comes from one of
# those files AND contains the phrase. We can't use chunk_id as the label,
# because chunk ids change when the chunk size changes.
# A file is only listed when it really answers the question, not when it merely
# mentions the phrase (e.g. a changelog line).
# Phrases are at most 40 chars (the smallest overlap), so every phrase is
# guaranteed to sit whole inside at least one chunk.
QUESTIONS = [
    {
        "question": "Which ROS domain ID range is safe to choose?",
        "files": ["About-Domain-ID.rst"],
        "phrase": "between 0 and 101",
    },
    {
        "question": "How do I create a new Python package?",
        "files": ["Creating-Your-First-ROS2-Package.rst"],
        "phrase": "--build-type ament_python",
    },
    {
        "question": "What happens to messages with the best effort reliability policy?",
        "files": ["About-Quality-of-Service-Settings.rst"],
        "phrase": "network is not robust",
    },
    {
        "question": "How can I save the data published on a topic to a file?",
        "files": ["Recording-And-Playing-Back-Data.rst"],
        "phrase": "ros2 bag record",
    },
    {
        "question": "Which command builds all the packages in my workspace?",
        "files": ["Colcon-Tutorial.rst"],
        "phrase": "colcon build --symlink-install",
    },
    {
        "question": "Which communication pattern should I use for a short request-reply interaction between nodes?",
        "files": ["About-Services.rst"],
        "phrase": "send requests and receive responses",
    },
    {
        "question": "How can a node run a long task, get progress updates and cancel it halfway?",
        "files": ["About-Actions.rst"],
        "phrase": "receives progress feedback",
    },
    {
        "question": "How do I save the current parameters of a node to a YAML file?",
        "files": ["Understanding-ROS2-Parameters.rst"],
        "phrase": "ros2 param dump /turtlesim",
    },
    {
        "question": "Which languages can ROS 2 launch files be written in?",
        "files": ["Launch-file-different-formats.rst", "About-Launch.rst",
                  "Creating-Launch-Files.rst", "Using-ROS2-Launch-For-Large-Projects.rst"],
        "phrase": "written in XML, YAML, or Python",
    },
    {
        "question": "Is there a ready-made tool to publish a fixed transform between two frames?",
        "files": ["Writing-A-Tf2-Static-Broadcaster-Py.rst", "Writing-A-Tf2-Static-Broadcaster-Cpp.rst"],
        "phrase": "provides an executable named",
    },
    {
        "question": "How do I install all the dependencies of the packages in my workspace?",
        "files": ["Rosdep.rst"],
        "phrase": "--from-paths src -y --ignore-src",
    },
    {
        "question": "What do I have to run in every new terminal before using ROS 2 commands?",
        "files": ["Configuring-ROS2-Environment.rst"],
        "phrase": "source /opt/ros/{DISTRO}/setup.bash",
    },
    {
        "question": "How can I check my ROS 2 installation for configuration problems?",
        "files": ["Getting-Started-With-Ros2doctor.rst"],
        "phrase": "ros2 doctor",
    },
    {
        "question": "How do I make a node print debug messages when I start it?",
        "files": ["Logging-and-logger-configuration.rst"],
        "phrase": "--ros-args --log-level debug",
    },
    {
        "question": "How can I stop my nodes from discovering nodes on other computers?",
        "files": ["Improved-Dynamic-Discovery.rst", "Configuring-ROS2-Environment.rst"],
        "phrase": "ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST",
    },
    {
        "question": "How many components does a quaternion have?",
        "files": ["Quaternion-Fundamentals.rst"],
        "phrase": "A quaternion has 4 components",
    },
    {
        "question": "How can I run several nodes inside a single process?",
        "files": ["About-Composition.rst"],
        "phrase": "load and manage multiple components",
    },
    {
        "question": "How do I call a service from the terminal?",
        "files": ["Understanding-ROS2-Services.rst"],
        "phrase": "ros2 service call <service_name>",
    },
    {
        "question": "What severity levels can log messages have?",
        "files": ["About-Logging.rst"],
        "phrase": "``WARN``, ``ERROR`` or ``FATAL``",
    },
    {
        "question": "How can I measure how often messages arrive on a topic?",
        "files": ["Understanding-ROS2-Topics.rst"],
        "phrase": "ros2 topic hz /turtle1/pose",
    },
]

def is_relevant(chunk, gold):
    return chunk["file"] in gold["files"] and gold["phrase"] in chunk["text"]

def evaluate(name, score_fn, chunks):
    # score_fn(question) -> one score per chunk; higher is better
    print(f"\n--- {name} ---")
    hits = 0
    file_hits = 0
    reciprocal_ranks = []
    for gold in QUESTIONS:
        results = top_k(score_fn(gold["question"]), chunks, K)

        # Rank (1..K) of the first correct chunk, or None if it's not in the top K
        hit_rank = next((rank for rank, (_, chunk) in enumerate(results, start=1)
                         if is_relevant(chunk, gold)), None)
        hits += hit_rank is not None
        # MRR@K: 1/rank of the correct chunk, 0 if it's not in the top K
        reciprocal_ranks.append(1 / hit_rank if hit_rank else 0)
        # Looser check: did any top-K chunk at least come from a gold file?
        file_hits += any(chunk["file"] in gold["files"] for _, chunk in results)

        status = f"HIT @ rank {hit_rank}" if hit_rank else "MISS"
        print(f"\n[{status}] {gold['question']}")
        for rank, (score, chunk) in enumerate(results, start=1):
            mark = "*" if is_relevant(chunk, gold) else " "
            print(f"   {mark} #{rank} {score:.3f}  {chunk['file']} > {chunk['heading']}")

    recall = hits / len(QUESTIONS)
    mrr = sum(reciprocal_ranks) / len(QUESTIONS)
    file_recall = file_hits / len(QUESTIONS)
    print(f"\nRecall@{K} = {hits}/{len(QUESTIONS)} = {recall:.2f}   MRR@{K} = {mrr:.2f}   "
          f"File recall@{K} = {file_recall:.2f}")
    return recall, mrr, file_recall

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
            summary.append((name, chunk_size, *evaluate(name, score_fn, chunks)))

    print("\n=== Summary ===")
    for name, chunk_size, recall, mrr, file_recall in summary:
        print(f"{name:<28} chunk_size={chunk_size:<5} Recall@{K} = {recall:.2f}   MRR@{K} = {mrr:.2f}   "
              f"File recall@{K} = {file_recall:.2f}")
