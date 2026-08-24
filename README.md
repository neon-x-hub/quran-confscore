# Quran Ayah Confusability Scoring Engine

A text-analytic framework for quantifying and ranking pairwise confusability across all 6,236 verses of the Quran. The engine identifies *mutashabihat* — structurally or textually overlapping verses that present a genuine challenge during memorization revision — and exposes them through an interactive web explorer backed by temperature-controlled sampling.

The system requires no machine learning, no external dependencies, and no personalization. It is a deliberately transparent, mathematically grounded baseline built entirely on n-gram overlap, IDF weighting, exponential length scaling, and square-root length normalization.

---

## Live Demo

The interactive web visualizer is deployed on GitHub Pages:

**[quran-confscore — Live Explorer](https://quran.mmmo.dev/)**

Three tabs are available in the interface:

- **Ayah Explorer** — Browse all 6,236 verses ranked and filtered by confusability tier, with per-ayah competitor expansion and shared phrase highlights.
- **Practice Simulator** — Temperature-controlled softmax sampling draws random prompts biased by difficulty. Adjust the temperature slider to control how strongly the hard verses are favored.
- **Surah Leaderboard** — Surah-level confusability ranking by average score with best-ayah spotlighting.

---

## Motivation

Revision of long Quranic memorization is impaired most by *mutashabihat* — verses that share near-identical phrasing, formulaic refrains, or structural patterns. Classical examples include the 31 repetitions of "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ" in Surah Ar-Rahman, or the cluster of verses beginning with "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ" distributed across multiple surahs.

Rather than relying on human curation or community-labelled difficulty lists, this project asks a formal question: given only the text of the Quran, which verses are most likely to be confused with another verse, and by how much?

The answer is operationalized as the confusability score $D(A)$, a scalar derived from n-gram overlap weighted by rarity and phrase length, then normalized by verse length.

---

## Methodology

### 1. Text Normalization

Before any comparison, verses are normalized to a canonical form that strips surface variation not affecting lexical identity:

| Step | Operation |
| :--- | :--- |
| Unicode normalization | NFKD decomposition |
| Diacritic stripping | Removes harakat (tashkeel) and Quranic ornamental markers (U+064B to U+065F, U+0670, U+06D6 to U+06ED) |
| Alif normalization | Alef Wasla, Hamza above, Hamza below, and Madda — all mapped to bare Alif |
| Alif Maqsura | ى mapped to ي |
| Ta Marbuta | ة mapped to ه |
| Tokenization | Whitespace-delimited word tokens |

### 2. N-Gram Extraction

For each normalized verse $A$, word n-grams of lengths $n \in [2, 5]$ are extracted. Unigrams are deliberately excluded to suppress noise from high-frequency function words:

$$\text{NGrams}(A) = \bigcup_{n=2}^{5} \text{NGrams}_n(A)$$

### 3. Inverse Document Frequency

Each n-gram $g$ receives an IDF weight reflecting its rarity across the corpus. Smoothing prevents infinite weights for unseen n-grams:

$$\text{IDF}(g) = \ln\left(\frac{N + \epsilon}{\text{DF}(g) + \epsilon}\right)$$

where $N = 6{,}236$ is the total verse count, $\text{DF}(g)$ is the number of distinct verses containing $g$, and $\epsilon = 1$.

### 4. Exponential Length Scaling

A shared 5-word phrase is exponentially more diagnostic of confusability than a shared 2-word phrase. The weight function $H(n)$ applies an exponential multiplier to IDF scores:

$$H(n) = 2^{n-1} \quad \text{for } n \geq 2$$

The combined n-gram weight is:

$$W(g) = \text{IDF}(g) \times H(|g|)$$

| N-gram Length | Multiplier | Interpretation |
| :---: | :---: | :--- |
| 2-gram | x 2 | Baseline multi-word match |
| 3-gram | x 4 | Formulaic phrase match |
| 4-gram | x 8 | High-probability competitor phrase |
| 5-gram | x 16 | Near-identical verse refrain |

### 5. Pairwise Similarity

For two distinct verses $A$ and $B$, the similarity score is the sum of weights over all shared n-grams:

$$S(A, B) = \sum_{g \,\in\, \text{NGrams}(A) \cap \text{NGrams}(B)} W(g)$$

Each shared n-gram is counted once per pair, regardless of repetition within a single verse.

### 6. Top-K Aggregation

Rather than summing over all 6,235 possible competitors — which would reward a verse for having many weak matches — only the top $K = 10$ strongest competitors are aggregated:

$$C_{\text{topK}}(A) = \sum_{k=1}^{10} S(A, B_k)$$

This isolates the most dangerous confusion pairs and makes the score robust to sparse low-similarity noise.

### 7. Length Normalization

Shorter verses provide less disambiguating context. A square-root inverse length factor normalizes for verse length:

$$F_{\text{length}}(A) = \frac{1}{\sqrt{L(A)}}$$

### 8. Final Confusability Score

$$\boxed{D(A) = \left(\sum_{k=1}^{10}\; \sum_{g \,\in\, \text{NGrams}(A) \cap \text{NGrams}(B_k)} \text{IDF}(g) \cdot 2^{|g|-1}\right) \cdot \frac{1}{\sqrt{L(A)}}}$$

### 9. Sampling Probability

Scores are normalized into a probability mass for difficulty-weighted sampling:

$$P(A) = \frac{D(A)}{\sum_{i} D(i)}$$

The web simulator applies a temperature $T$ via softmax over min-max normalized scores:

$$P_T(A) = \frac{\exp\!\left(\hat{D}(A) / T\right)}{\sum_{i} \exp\!\left(\hat{D}(i) / T\right)}$$

At $T \to 0$ the distribution concentrates on the hardest verse. At $T \to \infty$ it approaches a uniform draw.

---

## Empirical Findings

**Top 5 surahs by average confusability:**

| Rank | Surah | Avg Score | Hardest Verse Score |
| :---: | :--- | ---: | ---: |
| 1 | Al-Jumu'ah (62) | 636.5 | 1610.1 |
| 2 | Al-Bayyinah (98) | 574.6 | 1748.9 |
| 3 | As-Saff (61) | 548.3 | 1942.9 |
| 4 | Al-Hadid (57) | 477.9 | 1536.5 |
| 5 | At-Taghabun (64) | 448.3 | 1528.5 |

**Least confusable surahs:**

| Rank | Surah | Avg Score |
| :---: | :--- | ---: |
| 110 | Ash-Sharh (94) | 8.6 |
| 111 | Al-Masad (111) | 4.7 |
| 112 | Quraysh (106) | 1.5 |
| 114 | Al-Kawthar (108) | 0.0 |

Al-Kawthar scores zero: its three short verses share no n-gram of length 2 or above with any other verse in the Quran.

---

## Directory Structure

```text
quran-confscore/
├── .gitignore                              # Build and cache exclusions
├── DESIGN.md                               # Full technical specification document
├── README.md                               # This file
├── index.html                              # Web explorer entry point
├── app.js                                  # Explorer logic, filtering, rendering, simulator
├── style.css                               # Design system (CSS custom properties, responsive layout)
├── serve.py                                # Local development HTTP server
├── data/
│   └── quran.json                          # Ground-truth Quran text (6,236 verses, 114 surahs)
├── dist/                                   # Generated build artifacts — do not edit manually
│   ├── quran_confusability_scores.csv      # Tabular export for spreadsheet analysis
│   ├── quran_confusability_scores.json     # Full-precision JSON (pipeline diagnostics)
│   └── quran_confusability_scores.min.json # Network-optimized distribution payload
└── scripts/
    ├── confusability_scorer.py             # Full scoring pipeline
    ├── experiment_retrieval.py             # Hardness benchmarks and competitor lookup
    └── minify_data.py                      # Standalone data minification utility
```

---

## Data Payload Minification

The raw scoring output is 13.72 MB. Shipped over GitHub Pages without optimization, this would impose a substantial load penalty on mobile connections. Three techniques reduce the network payload:

**Field Pruning** — Internal diagnostic metrics not used by the frontend are removed: `confusability_total`, `confusability_top_5`, `confusability_top_10`, `length_factor`.

**Attribute Key Compression** — All JSON keys are mapped to single-character tokens:

| Full Key | Minified |
| :--- | :---: |
| `ayah_id` | `i` |
| `surah` | `s` |
| `ayah_number` | `n` |
| `original_text` | `t` |
| `word_count` | `w` |
| `confusability_max` | `m` |
| `final_score` | `f` |
| `probability` | `p` |
| `top_competitors` | `c` |

**Precision Trimming and Whitespace Removal** — Floating-point values are rounded to 1 decimal place. JSON indentation and delimiter spacing are stripped.

| Artifact | Size |
| :--- | ---: |
| Raw pipeline output | 13.72 MB |
| Minified, uncompressed | 5.79 MB |
| Minified, Gzip HTTP transfer | ~1.1 MB |
| Transfer reduction | ~92% |

---

## Usage

### Prerequisites

- Python 3.9 or later
- No external packages — the entire pipeline uses the Python standard library only

### Re-run the Scoring Pipeline

To recompute all scores from the ground-truth text and regenerate all outputs in `dist/`:

```bash
python scripts/confusability_scorer.py
```

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--input` | `data/quran.json` | Path to the input Quran text |
| `--output-json` | `dist/quran_confusability_scores.json` | Full JSON output |
| `--output-min-json` | `dist/quran_confusability_scores.min.json` | Minified JSON output |
| `--output-csv` | `dist/quran_confusability_scores.csv` | CSV summary output |
| `--top-k` | `10` | Number of top competitors to aggregate |
| `--min-n` | `2` | Minimum n-gram length |
| `--max-n` | `5` | Maximum n-gram length |
| `--scaling` | `exponential` | Length weight function: `exponential`, `cubic`, `quadratic`, `linear` |
| `--exp-base` | `2.0` | Base for the exponential scaling function |

### Run Retrieval Experiments

Executes three analysis experiments: hardness-tier benchmarks, competitor verse lookup, and surah-level statistical rankings:

```bash
python scripts/experiment_retrieval.py
```

To query specific verses:

```bash
python scripts/experiment_retrieval.py --query 2:255 55:13 112:1
```

### Minify Separately

To run minification as a standalone step on an existing full JSON file:

```bash
python scripts/minify_data.py \
  --input dist/quran_confusability_scores.json \
  --output dist/quran_confusability_scores.min.json
```

### Local Development Server

```bash
python serve.py
```

Open `http://localhost:8000`. The server sets CORS headers and disables caching for development use.

---

## License

This project uses two separate licenses depending on the component.

**Source code** (scoring engine, web frontend, scripts) is released under the
MIT License. See [LICENSE](LICENSE).

**Quran text data** (`data/quran.json` and all derived artifacts in `dist/`)
is based on the [quran-json](https://github.com/risan/quran-json) dataset
by [Risan Bagja Pradana](https://github.com/risan), licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)
license. See [LICENSE-DATA](LICENSE-DATA).

### Attribution

The Quran text corpus used in this project is sourced from:

> Risan Bagja Pradana. *quran-json: Quran text and translations in JSON format.*
> https://github.com/risan/quran-json
> Licensed under CC BY-SA 4.0.

