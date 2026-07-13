import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / "validation"))

import pandas as pd
from pydantic import ValidationError
from dotenv import load_dotenv
from openai import OpenAI
sys.path.append(str(Path(__file__).parent.parent / "validation"))
from schema import ChestXrayRecord

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_MODELS_TOKEN")
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4o-mini"

client = OpenAI(base_url=ENDPOINT, api_key=GITHUB_TOKEN)


def clean_age(age_str: str) -> int:
    unit = age_str[-1]
    value = int(age_str[:-1])
    if unit == "Y":
        return value
    elif unit == "M":
        return value // 12
    elif unit == "D":
        return value // 365
    raise ValueError(f"Unidad de edad desconocida: {age_str}")


def validate_csv(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    df["Patient Age Clean"] = df["Patient Age"].apply(clean_age)
    df["Finding Labels List"] = df["Finding Labels"].apply(lambda x: x.split("|"))

    valid_count, errors = 0, []

    for idx, row in df.iterrows():
        try:
            ChestXrayRecord(
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
            valid_count += 1
        except ValidationError as e:
            errors.append({"image_index": row["Image Index"], "error": str(e)})

    return {
        "file": csv_path.name,
        "total_rows": len(df),
        "valid_rows": valid_count,
        "invalid_rows": len(errors),
        "errors": errors[:10],
    }


def generate_ai_summary(stats: dict) -> str:
    prompt = f"""
Eres un asistente de calidad de datos en un proyecto de imagenes medicas clinicas.
Redacta un resumen ejecutivo breve (maximo 150 palabras), en espanol, para un lider
de proyecto NO tecnico, explicando el resultado de la validacion de un nuevo archivo
de datos. Se claro sobre si el archivo es apto para continuar en el pipeline o no.

Datos de la validacion:
{json.dumps(stats, indent=2, ensure_ascii=False)}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def main(csv_path_str: str):
    csv_path = Path(csv_path_str)
    print(f"Validando archivo: {csv_path}")

    stats = validate_csv(csv_path)
    print(f"\nTotal filas: {stats['total_rows']}")
    print(f"Validas: {stats['valid_rows']}")
    print(f"Con error: {stats['invalid_rows']}")

    print("\nGenerando resumen ejecutivo con IA...")
    summary = generate_ai_summary(stats)

    print("\n--- RESUMEN EJECUTIVO ---")
    print(summary)

    Path("docs").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(f"docs/validation_report_{timestamp}.md")
    report_path.write_text(
        f"# Reporte de validacion\n\n**Archivo:** {stats['file']}\n\n"
        f"**Fecha:** {datetime.now().isoformat()}\n\n"
        f"## Estadisticas\n- Total filas: {stats['total_rows']}\n"
        f"- Validas: {stats['valid_rows']}\n- Con error: {stats['invalid_rows']}\n\n"
        f"## Resumen ejecutivo (generado con IA)\n\n{summary}\n",
        encoding="utf-8"
    )
    print(f"\nReporte guardado en: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validate_new_upload.py <ruta_al_csv>")
        sys.exit(1)
    main(sys.argv[1])