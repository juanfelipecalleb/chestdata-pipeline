import pandas as pd
import shutil
from pathlib import Path

# --- Configuración de rutas ---
RAW_DIR = Path("data/raw/sample_extracted")
IMAGES_DIR = RAW_DIR / "images"
CSV_PATH = RAW_DIR / "sample_labels.csv"

OUTPUT_DIR = Path("data/raw/images_subset")
OUTPUT_CSV = Path("data/raw/sample_labels_subset.csv")

SAMPLE_SIZE = 300
RANDOM_SEED = 42  # para que la muestra sea reproducible

def main():
    # Crear carpeta de salida si no existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Leer CSV completo
    df = pd.read_csv(CSV_PATH)
    print(f"Total de filas en el CSV original: {len(df)}")

    # Tomar muestra aleatoria
    df_subset = df.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"Filas seleccionadas para el subset: {len(df_subset)}")

    # Copiar las imágenes correspondientes
    copied, missing = 0, 0
    for image_name in df_subset["Image Index"]:
        src = IMAGES_DIR / image_name
        dst = OUTPUT_DIR / image_name
        if src.exists():
            shutil.copy2(src, dst)
            copied += 1
        else:
            print(f"Imagen no encontrada: {image_name}")
            missing += 1

    print(f"\nImágenes copiadas: {copied}")
    print(f"Imágenes faltantes: {missing}")

    # Guardar el CSV recortado
    df_subset.to_csv(OUTPUT_CSV, index=False)
    print(f"\nCSV subset guardado en: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()