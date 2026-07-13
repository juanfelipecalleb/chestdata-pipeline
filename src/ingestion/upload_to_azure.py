import os
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# --- Cargar variables de entorno desde .env ---
load_dotenv()

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

if not ACCOUNT_NAME or not ACCOUNT_KEY:
    raise ValueError("Faltan variables de entorno. Revisa tu archivo .env")

# --- Configuración de rutas locales ---
RAW_CSV = Path("data/raw/sample_labels_subset.csv")
RAW_IMAGES_DIR = Path("data/raw/images_subset")
PROCESSED_PARQUET = Path("data/processed/chest_xray_validated.parquet")

# --- Configuración de destino en Azure ---
RAW_CONTAINER = "raw"
PROCESSED_CONTAINER = "processed"

def get_blob_service_client() -> BlobServiceClient:
    account_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=ACCOUNT_KEY)

def upload_file(service_client: BlobServiceClient, container: str, local_path: Path, blob_name: str):
    blob_client = service_client.get_blob_client(container=container, blob=blob_name)
    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"  Subido: {blob_name}")

def upload_directory(service_client: BlobServiceClient, container: str, local_dir: Path, blob_prefix: str):
    files = list(local_dir.glob("*"))
    print(f"\nSubiendo {len(files)} archivos desde {local_dir} -> {container}/{blob_prefix}/")
    for i, file_path in enumerate(files, start=1):
        blob_name = f"{blob_prefix}/{file_path.name}"
        upload_file(service_client, container, file_path, blob_name)
        if i % 50 == 0:
            print(f"  ... {i}/{len(files)} completados")
    print(f"Carga de {local_dir.name} completada: {len(files)} archivos.")

def main():
    print("Conectando a Azure Blob Storage...")
    service_client = get_blob_service_client()

    # 1. Subir CSV crudo
    print("\n[1/3] Subiendo CSV de metadata...")
    upload_file(service_client, RAW_CONTAINER, RAW_CSV, RAW_CSV.name)

    # 2. Subir imágenes
    print("\n[2/3] Subiendo imagenes...")
    upload_directory(service_client, RAW_CONTAINER, RAW_IMAGES_DIR, "images")

    # 3. Subir Parquet validado
    print("\n[3/3] Subiendo Parquet validado...")
    upload_file(service_client, PROCESSED_CONTAINER, PROCESSED_PARQUET, PROCESSED_PARQUET.name)

    print("\nProceso completo. Todos los archivos fueron subidos a Azure Blob Storage.")

    # 4. Subir Parquet enriquecido (con codigos ICD-10)

    print("\n[4/4] Subiendo Parquet enriquecido...")

    enriched_path = Path("data/processed/chest_xray_enriched.parquet")

    upload_file(service_client, PROCESSED_CONTAINER, enriched_path, enriched_path.name)

if __name__ == "__main__":
    main()