#!/usr/bin/env python3
"""
Quran Ayah Confusability Data Minifier
Strips unused backend fields, rounds floats, abbreviates attribute keys,
and compresses JSON output to optimize network transport.
"""

import json
import os
import argparse
import sys

def minify_records(records: list[dict]) -> list[dict]:
    minified = []
    for item in records:
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

def minify_file(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        print(f"[!] Input file {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Reading dataset from {input_path}...")
    orig_size = os.path.getsize(input_path)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    min_data = minify_records(data)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"[*] Exporting minified JSON to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(min_data, f, ensure_ascii=False, separators=(',', ':'))

    new_size = os.path.getsize(output_path)
    reduction = ((orig_size - new_size) / orig_size) * 100.0 if orig_size > 0 else 0
    print(f"[+] Minification complete!")
    print(f"    Original Size: {orig_size / (1024*1024):.2f} MB ({orig_size:,} bytes)")
    print(f"    Minified Size: {new_size / (1024*1024):.2f} MB ({new_size:,} bytes)")
    print(f"    Reduction:     {reduction:.2f}% size decrease")

def main():
    parser = argparse.ArgumentParser(description="Minify Quran Confusability JSON dataset")
    parser.add_argument("--input", default="quran_confusability_scores.json", help="Path to input full JSON file")
    parser.add_argument("--output", default="dist/quran_confusability_scores.min.json", help="Path for output minified JSON file")
    args = parser.parse_args()

    # Fallback checks if default input doesn't exist
    input_file = args.input
    if not os.path.exists(input_file) and os.path.exists("dist/quran_confusability_scores.json"):
        input_file = "dist/quran_confusability_scores.json"

    minify_file(input_file, args.output)

if __name__ == "__main__":
    main()
