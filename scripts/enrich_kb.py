"""Script to enrich the knowledge base with data from external medical APIs."""

import argparse

from src.medical_api_enricher import ICD10_MAPPING, MedicalAPIEnricher
from src.config import DATA_DIR


def main():
    parser = argparse.ArgumentParser(description="Enrich medical knowledge base with API data")
    parser.add_argument("--condition", type=str, help="Specific condition ID to enrich")
    parser.add_argument("--output", type=str, help="Output file path", default=None)
    args = parser.parse_args()

    enricher = MedicalAPIEnricher()
    output_path = args.output or str(DATA_DIR / "api_enrichment_cache.json")

    if args.condition:
        if args.condition not in ICD10_MAPPING:
            print(f"Unknown condition: {args.condition}")
            print(f"Available conditions: {', '.join(ICD10_MAPPING.keys())}")
            return
        print(f"Enriching condition: {args.condition}")
        result = enricher.enrich_condition(args.condition)
        import json
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Enriching all {len(ICD10_MAPPING)} conditions...")
        enricher.enrich_all_conditions(output_path)
        print(f"Done. Results saved to {output_path}")


if __name__ == "__main__":
    main()
