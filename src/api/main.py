from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
import pandas as pd
from pathlib import Path

app = FastAPI(
    title="ChestData API",
    description="API de consumo de datos clinicos validados del proyecto ChestData Pipeline",
    version="1.0.0"
)

PARQUET_PATH = Path("data/processed/chest_xray_enriched.parquet")

# Cargar los datos una sola vez al iniciar la API
df = pd.read_parquet(PARQUET_PATH)


@app.get("/")
def root():
    return {
        "message": "ChestData API activa",
        "total_records": len(df),
        "docs": "/docs"
    }


@app.get("/records")
def get_records(
    gender: Optional[str] = Query(None, description="Filtrar por genero: M o F"),
    finding: Optional[str] = Query(None, description="Filtrar por diagnostico, ej: Nodule"),
    limit: int = Query(20, ge=1, le=300, description="Cantidad maxima de registros a devolver")
):
    result = df.copy()

    if gender:
        result = result[result["patient_gender"] == gender.upper()]

    if finding:
        result = result[result["finding_labels"].apply(lambda labels: finding in list(labels))]

    result = result.head(limit)

    records = []
    for _, row in result.iterrows():
        records.append({
            "image_index": str(row["image_index"]),
            "finding_labels": list(row["finding_labels"]),
            "patient_age": int(row["patient_age"]),
            "patient_gender": str(row["patient_gender"]),
            "view_position": str(row["view_position"]),
        })

    return {
        "count": len(result),
        "results": records
    }


@app.get("/records/{image_index}")
def get_record_by_image(image_index: str):
    record = df[df["image_index"] == image_index]

    if record.empty:
        raise HTTPException(status_code=404, detail=f"No se encontro el registro: {image_index}")

    row = record.iloc[0]
    return {
        "image_index": str(row["image_index"]),
        "finding_labels": list(row["finding_labels"]),
        "patient_age": int(row["patient_age"]),
        "patient_gender": str(row["patient_gender"]),
        "view_position": str(row["view_position"]),
    }


@app.get("/stats")
def get_stats():
    return {
        "total_records": len(df),
        "gender_distribution": df["patient_gender"].value_counts().to_dict(),
        "view_position_distribution": df["view_position"].value_counts().to_dict(),
        "age_avg": round(df["patient_age"].mean(), 1),
        "age_min": int(df["patient_age"].min()),
        "age_max": int(df["patient_age"].max()),
    }

@app.get("/records/{image_index}/diagnosis-codes")
def get_diagnosis_codes(image_index: str):
    record = df[df["image_index"] == image_index]

    if record.empty:
        raise HTTPException(status_code=404, detail=f"No se encontro el registro: {image_index}")

    row = record.iloc[0]
    return {
        "image_index": image_index,
        "finding_labels": list(row["finding_labels"]),
        "icd10_codes": list(row["icd10_codes"])
    }