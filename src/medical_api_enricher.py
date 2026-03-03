"""Medical API enricher for fetching condition information from external APIs."""

import json
import time
from pathlib import Path
from typing import Optional

import requests

ICD10_MAPPING = {
    "iron_deficiency_anemia": "D50",
    "diabetes_mellitus_type_2": "E11",
    "chronic_kidney_disease": "N18",
    "hypothyroidism": "E03",
    "inflammatory_bowel_disease": "K50",
    "urinary_tract_infection": "N39",
    "hepatitis": "B19",
    "colorectal_cancer": "C18",
    "leukemia": "C91",
}


class OpenFDAClient:
    """Client for OpenFDA API."""

    BASE_URL = "https://api.fda.gov"

    def search_drug_adverse_events(self, condition: str, limit: int = 5) -> list:
        """Search for drug adverse events related to a condition."""
        try:
            url = f"{self.BASE_URL}/drug/event.json"
            params = {"search": f'patient.reaction.reactionmeddrapt:"{condition}"', "limit": limit}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception:
            return []

    def search_drug_labels(self, drug_name: str, limit: int = 3) -> list:
        """Search for drug labels."""
        try:
            url = f"{self.BASE_URL}/drug/label.json"
            params = {"search": f'openfda.generic_name:"{drug_name}"', "limit": limit}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception:
            return []


class NIHMedlinePlusClient:
    """Client for NIH MedlinePlus API."""

    def get_health_topic_by_code(self, icd10_code: str) -> Optional[dict]:
        """Get health topic by ICD-10 code via MedlinePlus Connect."""
        try:
            url = "https://connect.medlineplus.gov/application"
            params = {
                "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.90",
                "mainSearchCriteria.v.c": icd10_code,
                "knowledgeResponseType": "application/json",
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def search_health_topic(self, term: str) -> Optional[dict]:
        """Search for health topic."""
        try:
            url = "https://wsearch.nlm.nih.gov/ws/query"
            params = {"db": "healthTopics", "term": term}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return {"raw": resp.text[:500]}
        except Exception:
            return None


class DiseaseOntologyClient:
    """Client for Disease Ontology API."""

    def search_disease(self, term: str) -> Optional[dict]:
        """Search for disease information."""
        try:
            url = "https://www.disease-ontology.org/api/search/"
            params = {"query": term}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None


class MedicalAPIEnricher:
    """Orchestrator for medical API enrichment."""

    def __init__(self):
        self.fda = OpenFDAClient()
        self.nih = NIHMedlinePlusClient()
        self.do = DiseaseOntologyClient()

    def enrich_condition(self, condition_id: str) -> dict:
        """Fetch enrichment data for a condition from all APIs."""
        time.sleep(0.5)  # Rate limiting

        icd10 = ICD10_MAPPING.get(condition_id)
        result = {
            "condition_id": condition_id,
            "icd10_code": icd10,
            "fda_adverse_events": [],
            "medlineplus_topic": None,
            "disease_ontology": None,
        }

        # OpenFDA
        result["fda_adverse_events"] = self.fda.search_drug_adverse_events(
            condition_id.replace("_", " ")
        )

        # NIH MedlinePlus
        if icd10:
            result["medlineplus_topic"] = self.nih.get_health_topic_by_code(icd10)

        # Disease Ontology
        result["disease_ontology"] = self.do.search_disease(condition_id.replace("_", " "))

        return result

    def enrich_all_conditions(self, output_path: Optional[str] = None) -> dict:
        """Enrich all mapped conditions and optionally save to file."""
        all_data = {}
        for condition_id in ICD10_MAPPING:
            print(f"Enriching: {condition_id}...")
            all_data[condition_id] = self.enrich_condition(condition_id)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2)
            print(f"Saved to {output_path}")

        return all_data

    def get_drug_info(self, drug_name: str) -> list:
        """Get drug information."""
        return self.fda.search_drug_labels(drug_name)

    def get_patient_education(self, condition_id: str) -> Optional[dict]:
        """Get patient education materials."""
        icd10 = ICD10_MAPPING.get(condition_id)
        if icd10:
            return self.nih.get_health_topic_by_code(icd10)
        return self.nih.search_health_topic(condition_id.replace("_", " "))
