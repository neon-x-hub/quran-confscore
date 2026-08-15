#!/usr/bin/env python3
"""
Experiment Retrieval Script for Quran Ayah Confusability Scores.
Demonstrates:
1. Hardness-based retrieval & sampling (stratified tiers, temperature softmax).
2. Similar confusable verses lookup engine.
3. Comparative statistical analysis across Surahs and difficulty distributions.
Supports both standard and minified JSON datasets.
"""

import json
import math
import random
import sys
import os
import argparse
import unicodedata
import re
from collections import defaultdict

def normalize_record(raw_record: dict) -> dict:
    """Normalize raw dict regardless of minified or full keys."""
    if 'i' in raw_record:
        return {
            'ayah_id': raw_record['i'],
            'surah': raw_record['s'],
            'ayah_number': raw_record['n'],
            'original_text': raw_record['t'],
            'word_count': raw_record['w'],
            'confusability_max': raw_record['m'],
            'final_score': raw_record['f'],
            'probability': raw_record['p'],
            'top_competitors': [
                {
                    'competitor_ayah_id': c['i'],
                    'similarity_score': c['s'],
                    'shared_ngrams': c['n']
                } for c in raw_record.get('c', [])
            ]
        }
    return raw_record

def load_data(json_path="dist/quran_confusability_scores.min.json"):
    if not os.path.exists(json_path):
        if os.path.exists("dist/quran_confusability_scores.json"):
            json_path = "dist/quran_confusability_scores.json"
        elif os.path.exists("quran_confusability_scores.json"):
            json_path = "quran_confusability_scores.json"

    print(f"[*] Loading dataset from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [normalize_record(r) for r in data]

def experiment_hardness_levels(data):
    print("=========================================================")
    print(" EXPERIMENT 1: RETRIEVAL BY HARDNESS LEVEL & SAMPLING")
    print("=========================================================")

    sorted_data = sorted(data, key=lambda x: x['final_score'], reverse=True)
    total_count = len(sorted_data)

    tier_size = total_count // 5
    tiers = {
        "Tier 1: Extreme Hardness (Top 20%)": sorted_data[:tier_size],
        "Tier 2: High Hardness (20-40%)": sorted_data[tier_size:2*tier_size],
        "Tier 3: Medium Hardness (40-60%)": sorted_data[2*tier_size:3*tier_size],
        "Tier 4: Low Hardness (60-80%)": sorted_data[3*tier_size:4*tier_size],
        "Tier 5: Very Low Hardness (Bottom 20%)": sorted_data[4*tier_size:]
    }

    print("\n--- Hardness Tier Statistics ---")
    for tier_name, ayahs in tiers.items():
        min_score = ayahs[-1]['final_score']
        max_score = ayahs[0]['final_score']
        avg_score = sum(a['final_score'] for a in ayahs) / len(ayahs)
        avg_words = sum(a['word_count'] for a in ayahs) / len(ayahs)
        print(f"\n[{tier_name}] (Count: {len(ayahs)})")
        print(f"  Score Range: {min_score:.2f} to {max_score:.2f} | Avg Score: {avg_score:.2f} | Avg Word Count: {avg_words:.1f}")
        sample = random.sample(ayahs, 2)
        for s in sample:
            print(f"   - Sample {s['ayah_id']} (Score: {s['final_score']:.1f}): {s['original_text'][:70]}...")

    print("\n--- Temperature Softmax Sampling Simulation (1,000 Draws) ---")
    scores = [a['final_score'] for a in sorted_data]
    temperatures = [0.1, 0.5, 1.0, 5.0, 50.0]

    for T in temperatures:
        max_s = max(scores)
        exp_scores = [math.exp((s - max_s) / T) for s in scores]
        sum_exp = sum(exp_scores)
        probs = [e / sum_exp for e in exp_scores]

        samples = random.choices(sorted_data, weights=probs, k=1000)
        top20_count = sum(1 for s in samples if s in tiers["Tier 1: Extreme Hardness (Top 20%)"])
        bottom20_count = sum(1 for s in samples if s in tiers["Tier 5: Very Low Hardness (Bottom 20%)"])

        print(f"  Temp T={T:4.1f} | Top 20% Selection Rate: {top20_count/10.0:5.1f}% | Bottom 20% Selection Rate: {bottom20_count/10.0:5.1f}%")

def experiment_confusable_lookup(data, query_ayah_ids):
    print("\n=========================================================")
    print(" EXPERIMENT 2: SIMILAR CONFUSABLE VERSES LOOKUP")
    print("=========================================================")

    id_map = {a['ayah_id']: a for a in data}

    for q_id in query_ayah_ids:
        if q_id not in id_map:
            print(f"\n[!] Ayah ID {q_id} not found.")
            continue

        target = id_map[q_id]
        print(f"\n>>> QUERY AYAH: {target['ayah_id']} (Surah {target['surah']}, Ayah {target['ayah_number']})")
        print(f"    Original Text : {target['original_text']}")
        print(f"    Metrics       : Final Score D(A) = {target['final_score']:.2f} | Word Count = {target['word_count']}")
        print("    Top Similar Confusable Competitor Verses:")

        for idx, comp in enumerate(target['top_competitors'][:5], 1):
            comp_id = comp['competitor_ayah_id']
            comp_record = id_map.get(comp_id, {})
            comp_text = comp_record.get('original_text', 'N/A')
            sim_score = comp['similarity_score']
            shared = comp['shared_ngrams']

            print(f"      {idx}. Match: Ayah {comp_id:<6} | Sim Score S(A,B) = {sim_score:7.2f}")
            print(f"         Text        : {comp_text}")
            print(f"         Shared Phrases: {shared}")
        print("-" * 65)

def experiment_surah_benchmark(data):
    print("\n=========================================================")
    print(" EXPERIMENT 3: SURAH CONFUSABILITY RANKING")
    print("=========================================================")

    surah_groups = defaultdict(list)
    for a in data:
        surah_groups[a['surah']].append(a)

    surah_stats = []
    for s_id, ayahs in surah_groups.items():
        avg_score = sum(a['final_score'] for a in ayahs) / len(ayahs)
        max_score = max(a['final_score'] for a in ayahs)
        total_words = sum(a['word_count'] for a in ayahs)
        surah_stats.append({
            'surah_id': s_id,
            'count': len(ayahs),
            'avg_score': avg_score,
            'max_score': max_score,
            'total_words': total_words
        })

    surah_stats.sort(key=lambda x: x['avg_score'], reverse=True)

    print("\n--- Top 5 Surahs with Highest Average Ayah Confusability ---")
    for s in surah_stats[:5]:
        print(f"  Surah {s['surah_id']:3d} | Ayahs: {s['count']:3d} | Avg Score: {s['avg_score']:6.2f} | Max Ayah Score: {s['max_score']:6.2f}")

    print("\n--- Bottom 5 Surahs with Lowest Average Ayah Confusability ---")
    for s in surah_stats[-5:]:
        print(f"  Surah {s['surah_id']:3d} | Ayahs: {s['count']:3d} | Avg Score: {s['avg_score']:6.2f} | Max Ayah Score: {s['max_score']:6.2f}")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="Quran Confusability Experiment Engine")
    parser.add_argument("--scores-json", default="dist/quran_confusability_scores.min.json")
    parser.add_argument("--query", nargs="*", default=["7:65", "26:8", "55:13", "2:255", "112:1"])
    args = parser.parse_args()

    data = load_data(args.scores_json)

    experiment_hardness_levels(data)
    experiment_confusable_lookup(data, args.query)
    experiment_surah_benchmark(data)

if __name__ == "__main__":
    main()
