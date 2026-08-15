#!/usr/bin/env python3
"""
Quran Ayah Confusability Scoring Engine (v0.2)
Includes Non-Linear Length Weighting H(n) and Unigram Noise Suppression
Automated full export and network-minified JSON generation into dist/.
"""

import json
import math
import re
import unicodedata
import argparse
import os
import sys
from collections import defaultdict

def normalize_arabic(text: str) -> str:
    """
    Standardize Arabic orthography and strip diacritics according to DESIGN.md rules.
    """
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]', '', text)
    text = re.sub(r'[\u0622\u0623\u0625\u0671]', '\u0627', text)
    text = re.sub(r'\u0649', '\u064A', text)
    text = re.sub(r'\u0629', '\u0647', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def tokenize(normalized_text: str) -> list[str]:
    return normalized_text.split()

def extract_ngrams(tokens: list[str], min_n: int = 2, max_n: int = 5) -> set[tuple[str, ...]]:
    ngrams = set()
    num_tokens = len(tokens)
    for n in range(min_n, max_n + 1):
        for i in range(num_tokens - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams.add(ngram)
    return ngrams

def get_length_scaling_function(mode: str, base: float = 2.0):
    if mode == "linear":
        return lambda n: float(n)
    elif mode == "quadratic":
        return lambda n: float(n ** 2)
    elif mode == "cubic":
        return lambda n: float(n ** 3)
    elif mode == "exponential":
        return lambda n: float(base ** (n - 1))
    else:
        return lambda n: float(base ** (n - 1))

def run_confusability_pipeline(
    quran_json_path: str,
    top_k: int = 10,
    epsilon: float = 1.0,
    min_n: int = 2,
    max_n: int = 5,
    scaling_mode: str = "exponential",
    exp_base: float = 2.0
):
    print(f"[*] Loading Quran dataset from {quran_json_path}...")
    with open(quran_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    H = get_length_scaling_function(scaling_mode, base=exp_base)
    print(f"[*] Configuration: min_n={min_n}, max_n={max_n}, scaling={scaling_mode} (base={exp_base})")

    ayah_records = []
    print("[*] Phase 1: Preprocessing and extracting n-grams...")
    for surah in data:
        surah_id = surah['id']
        surah_name = surah.get('name', '')
        for verse in surah['verses']:
            v_id = verse['id']
            ayah_id = f"{surah_id}:{v_id}"
            orig_text = verse['text']
            norm_text = normalize_arabic(orig_text)
            tokens = tokenize(norm_text)
            ngrams = extract_ngrams(tokens, min_n=min_n, max_n=max_n)

            ayah_records.append({
                'ayah_id': ayah_id,
                'surah': surah_id,
                'surah_name': surah_name,
                'ayah_number': v_id,
                'original_text': orig_text,
                'normalized_text': norm_text,
                'tokens': tokens,
                'word_count': len(tokens),
                'ngrams': ngrams
            })

    N = len(ayah_records)
    print(f"    Loaded {N} ayahs.")

    print("[*] Phase 2: Computing Document Frequencies and Non-Linear Weighted IDF...")
    doc_freq = defaultdict(int)
    inverted_index = defaultdict(list)

    for i, record in enumerate(ayah_records):
        for g in record['ngrams']:
            doc_freq[g] += 1
            inverted_index[g].append(i)

    idf_weights = {}
    for g, df in doc_freq.items():
        idf = math.log((N + epsilon) / (df + epsilon))
        length = len(g)
        idf_weights[g] = idf * H(length)

    print("[*] Phase 3: Calculating pairwise confusability similarities...")
    results = []
    total_d_sum = 0.0

    for i, record in enumerate(ayah_records):
        ayah_id = record['ayah_id']
        pair_scores = defaultdict(float)
        pair_shared_ngrams = defaultdict(list)

        for g in record['ngrams']:
            w = idf_weights[g]
            for j in inverted_index[g]:
                if i == j:
                    continue
                pair_scores[j] += w
                if len(pair_shared_ngrams[j]) < 5:
                    pair_shared_ngrams[j].append(" ".join(g))

        sorted_pairs = sorted(pair_scores.items(), key=lambda x: x[1], reverse=True)

        confusability_total = sum(score for _, score in sorted_pairs)
        confusability_max = sorted_pairs[0][1] if sorted_pairs else 0.0
        confusability_top_5 = sum(score for _, score in sorted_pairs[:5])
        confusability_top_10 = sum(score for _, score in sorted_pairs[:top_k])

        word_count = record['word_count']
        length_factor = 1.0 / math.sqrt(word_count) if word_count > 0 else 0.0

        final_score = confusability_top_10 * length_factor
        total_d_sum += final_score

        top_competitors = []
        for match_idx, score in sorted_pairs[:top_k]:
            match_record = ayah_records[match_idx]
            top_competitors.append({
                'competitor_ayah_id': match_record['ayah_id'],
                'similarity_score': round(score, 4),
                'shared_ngrams': pair_shared_ngrams[match_idx]
            })

        results.append({
            'ayah_id': ayah_id,
            'surah': record['surah'],
            'ayah_number': record['ayah_number'],
            'original_text': record['original_text'],
            'word_count': word_count,
            'confusability_total': round(confusability_total, 4),
            'confusability_max': round(confusability_max, 4),
            'confusability_top_5': round(confusability_top_5, 4),
            'confusability_top_10': round(confusability_top_10, 4),
            'length_factor': round(length_factor, 4),
            'final_score': round(final_score, 4),
            'top_competitors': top_competitors
        })

    print("[*] Phase 4: Computing sampling probabilities...")
    for res in results:
        res['probability'] = round(res['final_score'] / total_d_sum, 8) if total_d_sum > 0 else 0.0

    return results

def minify_records(results: list[dict]) -> list[dict]:
    minified = []
    for item in results:
        comps = []
        for comp in item.get('top_competitors', []):
            comps.append({
                'i': comp['competitor_ayah_id'],
                's': round(float(comp['similarity_score']), 1),
                'n': comp.get('shared_ngrams', [])
            })
        minified.append({
            'i': item['ayah_id'],
            's': item['surah'],
            'n': item['ayah_number'],
            't': item['original_text'],
            'w': item['word_count'],
            'm': round(float(item['confusability_max']), 1),
            'f': round(float(item['final_score']), 1),
            'p': round(float(item['probability']), 8),
            'c': comps
        })
    return minified

def export_results(results: list[dict], output_json: str, output_min_json: str, output_csv: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)

    print(f"[*] Exporting full results to JSON ({output_json})...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if output_min_json:
        print(f"[*] Exporting minified JSON ({output_min_json})...")
        min_data = minify_records(results)
        with open(output_min_json, 'w', encoding='utf-8') as f:
            json.dump(min_data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"[*] Exporting summary to CSV ({output_csv})...")
    with open(output_csv, 'w', encoding='utf-8-sig') as f:
        f.write("ayah_id,word_count,confusability_total,confusability_max,confusability_top_5,confusability_top_10,length_factor,final_score,probability,top_competitor_id,top_competitor_score\n")
        for r in results:
            top_comp_id = r['top_competitors'][0]['competitor_ayah_id'] if r['top_competitors'] else ""
            top_comp_score = r['top_competitors'][0]['similarity_score'] if r['top_competitors'] else 0.0
            f.write(f"{r['ayah_id']},{r['word_count']},{r['confusability_total']},{r['confusability_max']},{r['confusability_top_5']},{r['confusability_top_10']},{r['length_factor']},{r['final_score']},{r['probability']},{top_comp_id},{top_comp_score}\n")

    print("[+] Processing complete successfully!")

def main():
    parser = argparse.ArgumentParser(description="Quran Ayah Confusability Scoring Engine")
    parser.add_argument("--input", default="data/quran.json", help="Path to input quran.json")
    parser.add_argument("--output-json", default="dist/quran_confusability_scores.json", help="Path for JSON output")
    parser.add_argument("--output-min-json", default="dist/quran_confusability_scores.min.json", help="Path for minified JSON output")
    parser.add_argument("--output-csv", default="dist/quran_confusability_scores.csv", help="Path for CSV output")
    parser.add_argument("--top-k", type=int, default=10, help="Top K competitors to aggregate")
    parser.add_argument("--min-n", type=int, default=2, help="Minimum n-gram length")
    parser.add_argument("--max-n", type=int, default=5, help="Maximum n-gram length")
    parser.add_argument("--scaling", default="exponential", choices=["linear", "quadratic", "cubic", "exponential"], help="Length scaling function H(n)")
    parser.add_argument("--exp-base", type=float, default=2.0, help="Base for exponential scaling H(n)=base^(n-1)")

    args = parser.parse_args()
    results = run_confusability_pipeline(
        args.input,
        top_k=args.top_k,
        min_n=args.min_n,
        max_n=args.max_n,
        scaling_mode=args.scaling,
        exp_base=args.exp_base
    )
    export_results(results, args.output_json, args.output_min_json, args.output_csv)

if __name__ == "__main__":
    main()
