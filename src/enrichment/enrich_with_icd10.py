import time
import json
import requests
import pandas as pd
from pathlib import Path

INPUT_PARQUET = Path("data/processed/chest_xray_validated.parquet")
OUTPUT_PARQUET = Path("data/processed/chest_xray_enriched.parquet")
MAPPING_LOG = Path("docs/icd10_mapping.json")

API_URL = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"

# Terminos que no son diagnosticos reales, no se buscan en la API

NON_DIAGNOSIS_TERMS = {"No Finding"}

# Contexto clinico adicional para mejorar la precision de la busqueda,
# ya que terminos sueltos son ambiguos entre especialidades medicas
SEARCH_CONTEXT_OVERRIDES = {
    "Edema": "pulmonary edema",
    "Effusion": "pleural effusion",
    "Fibrosis": "pulmonary fibrosis",
    "Mass": "abnormal lung",
    "Nodule": "pulmonary nodule",
    "Pneumonia": "pneumonia unspecified organism",
    "Infiltration": "abnormal lung",
    "Pleural_Thickening": "pleural plaque",
    # "Consolidation" queda sin override: no se encontro codigo ICD-10 especifico,
    # es un hallazgo radiologico descriptivo, no un diagnostico formal codificable por si solo
}


def search_icd10(term: str) -> dict:
    """Busca un termino en la API de ICD-10-CM y devuelve el primer resultado."""
    params = {"terms": term, "sf": "code,name", "df": "code,name"}
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data[0] > 0:
            code, name = data[3][0]
            return {"icd10_code": code, "icd10_name": name}
        return {"icd10_code": None, "icd10_name": None}
    except requests.RequestException as e:
        print(f"  Error consultando '{term}': {e}")
        return {"icd10_code": None, "icd10_name": None}


def build_diagnosis_mapping(all_labels: set) -> dict:
    mapping = {}
    for label in sorted(all_labels):
        if label in NON_DIAGNOSIS_TERMS:
            mapping[label] = {"icd10_code": None, "icd10_name": "No aplica (sin hallazgo)"}
            continue

        search_term = SEARCH_CONTEXT_OVERRIDES.get(label, label)
        print(f"Consultando: {label} (busqueda: '{search_term}')")
        result = search_icd10(search_term)
        mapping[label] = result
        time.sleep(0.2)

    return mapping


def main():
    print(f"Cargando datos desde: {INPUT_PARQUET}")
    df = pd.read_parquet(INPUT_PARQUET)

    # Extraer todos los diagnosticos unicos (finding_labels es una lista por fila)
    all_labels = set()
    for labels in df["finding_labels"]:
        all_labels.update(labels)

    print(f"\nDiagnosticos unicos encontrados: {len(all_labels)}")
    print(sorted(all_labels))

    print("\nConsultando API de ICD-10-CM (NLM Clinical Tables)...")
    mapping = build_diagnosis_mapping(all_labels)

    # Guardar el mapeo como referencia/documentacion
    Path("docs").mkdir(exist_ok=True)
    MAPPING_LOG.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nMapeo guardado en: {MAPPING_LOG}")

    # Enriquecer el dataframe: agregar columna con los codigos ICD-10 correspondientes
    def get_codes_for_row(labels):
        return [mapping[label]["icd10_code"] for label in labels if mapping[label]["icd10_code"]]

    df["icd10_codes"] = df["finding_labels"].apply(get_codes_for_row)

    df.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"\nDataset enriquecido guardado en: {OUTPUT_PARQUET}")
    print(f"\nEjemplo de fila enriquecida:")
    print(df[["image_index", "finding_labels", "icd10_codes"]].head(3).to_string())


if __name__ == "__main__":
    main()