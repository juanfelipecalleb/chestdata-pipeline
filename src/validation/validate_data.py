import pandas as pd
from pathlib import Path
from pydantic import ValidationError
from schema import ChestXrayRecord

INPUT_CSV = Path("data/raw/sample_labels_subset.csv")
OUTPUT_PARQUET = Path("data/processed/chest_xray_validated.parquet")
ERROR_LOG = Path("data/processed/validation_errors.csv")

def clean_age(age_str: str) -> int:
    """
    Convierte edad con unidad a años enteros.
    '066Y' -> 66 (años)
    '003M' -> 0  (meses -> redondeado a años, 3 meses = 0 años completos)
    '001D' -> 0  (días -> redondeado a años, 1 día = 0 años completos)
    """
    unit = age_str[-1]
    value = int(age_str[:-1])

    if unit == "Y":
        return value
    elif unit == "M":
        return value // 12
    elif unit == "D":
        return value // 365
    else:
        raise ValueError(f"Unidad de edad desconocida: {age_str}")

def main():
    df = pd.read_csv(INPUT_CSV)
    print(f"Filas a validar: {len(df)}")

    # Limpieza previa mínima (antes de validar tipos)
    df["Patient Age Clean"] = df["Patient Age"].apply(clean_age)
    df["Finding Labels List"] = df["Finding Labels"].apply(lambda x: x.split("|"))

    valid_records = []
    errors = []

    for idx, row in df.iterrows():
        try:
            record = ChestXrayRecord(
                image_index=row["Image Index"],
                finding_labels=row["Finding Labels List"],
                follow_up_number=row["Follow-up #"],
                patient_id=row["Patient ID"],
                patient_age=row["Patient Age Clean"],
                patient_gender=row["Patient Gender"],
                view_position=row["View Position"],
                original_width=row["OriginalImageWidth"],
                original_height=row["OriginalImageHeight"],
                pixel_spacing_x=row["OriginalImagePixelSpacing_x"],
                pixel_spacing_y=row["OriginalImagePixelSpacing_y"],
            )
            valid_records.append(record.model_dump())
        except ValidationError as e:
            errors.append({"row_index": idx, "image_index": row["Image Index"], "error": str(e)})

    print(f"\nRegistros válidos: {len(valid_records)}")
    print(f"Registros con error: {len(errors)}")

    # Guardar registros válidos como Parquet
    df_valid = pd.DataFrame(valid_records)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df_valid.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"\nParquet guardado en: {OUTPUT_PARQUET}")

    # Guardar log de errores si hay
    if errors:
        pd.DataFrame(errors).to_csv(ERROR_LOG, index=False)
        print(f"Log de errores guardado en: {ERROR_LOG}")

    # Chequeo extra: duplicados
    duplicated = df["Image Index"].duplicated().sum()
    print(f"\nImágenes duplicadas en el CSV: {duplicated}")

if __name__ == "__main__":
    main()