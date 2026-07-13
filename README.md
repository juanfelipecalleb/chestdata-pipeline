# ChestData Pipeline

Proyecto de práctica end-to-end de ingeniería de datos aplicado a un dataset clínico 
de imágenes médicas (NIH Chest X-ray sample), simulando un flujo real de estructuración, 
validación, almacenamiento en la nube y consumo de datos para proyectos de IA.

## Fase 1 — Ingesta y validación de datos 

- **Fuente**: [NIH Chest X-ray Sample Dataset](https://www.kaggle.com/datasets/nih-chest-xrays/sample) (Kaggle)
- **Subset de trabajo**: 300 imágenes seleccionadas aleatoriamente (seed=42) + su metadata correspondiente
- **Validación**: esquema definido con Pydantic (`src/validation/schema.py`), que valida:
  - Rango de edad (0-120 años)
  - Valores permitidos de género (M/F) y posición de vista (AP/PA)
  - Dimensiones e información de spacing positivas
- **Decisiones de limpieza de datos**:
  - `Patient Age` venía en formato mixto (`066Y`, `003M`, `001D` = años, meses, días). 
    Se normalizó todo a años completos.
  - `Finding Labels` es multi-label (ej. `Mass|Nodule`), se transformó a lista de strings.
- **Salida**: `data/processed/chest_xray_validated.parquet`


## Estructura del proyecto

```
chestdata-pipeline/
├── data/
│   ├── raw/              # datos originales y subset (no versionado en git)
│   └── processed/        # datos validados en Parquet
├── src/
│   ├── ingestion/        # scripts de carga: upload_to_azure.py, load_to_sql.py
│   ├── validation/       # esquemas y validacion de calidad
│   └── api/              # API FastAPI de consumo de datos
├── notebooks/            # exploracion de datos
└── docs/
```

## Fase 2 — Ingenieria de datos en Azure

- **Cuenta**: Azure Free Account
- **Resource Group**: `rg-chestdata-pipeline` (region: East US)
- **Storage Account**: `chestdatastorage2026` (Standard_LRS, StorageV2)
- **Arquitectura de contenedores** (patron raw/processed, similar a un Data Lake):
  - `raw/`: datos originales sin procesar (300 imagenes .png + CSV de metadata original)
  - `processed/`: datos validados y transformados (`chest_xray_validated.parquet`)
- **Autenticacion**: manejo de credenciales via variables de entorno (`.env`, no versionado en git)
- **Herramientas usadas**: Azure CLI para aprovisionamiento y carga de datos

### Automatizacion
La carga de datos a Azure Blob Storage esta automatizada en `src/ingestion/upload_to_azure.py`, 
que usa el SDK oficial de Azure (`azure-storage-blob`) y credenciales gestionadas via variables 
de entorno (`.env`, no versionado). Para reproducir:

```
python src/ingestion/upload_to_azure.py
```

### Comandos clave utilizados
```
az group create --name rg-chestdata-pipeline --location eastus
az storage account create --name chestdatastorage2026 --resource-group rg-chestdata-pipeline --sku Standard_LRS --kind StorageV2
az storage container create --name raw --account-name chestdatastorage2026
az storage container create --name processed --account-name chestdatastorage2026
az storage blob upload-batch --destination raw/images --source data/raw/images_subset
```

## Fase 2b — Base de datos relacional (Azure SQL)

- **Servidor**: `chestdata-sqlserver-jf2026.database.windows.net` (region: Central US)
- **Base de datos**: `chestdata-db` (modo Serverless, auto-pause a los 60 min de inactividad)
- **Tabla**: `chest_xray_records` (image_index, finding_labels, patient_age, patient_gender, view_position)

### Decisiones de seguridad
- **Autenticacion**: Azure AD Authentication en vez de usuario/password SQL tradicional. 
  La conexion desde Python usa `DefaultAzureCredential` (libreria `azure-identity`), 
  sin necesidad de almacenar ni transmitir contrasenas.
- **Firewall**: restringido a la IP publica del desarrollador (no abierto a internet).
- **Cifrado en transito**: TLS 1.2+ forzado por defecto (`minimalTlsVersion: 1.2`).
- **Nota de mejora para produccion**: en un entorno real (ej. proyecto CheXVision con datos 
  clinicos sensibles), se recomendaria ademas usar Private Endpoint (para que la base no 
  tenga IP publica en absoluto) y Azure Key Vault para gestion centralizada de secretos.

### Automatizacion
La carga de datos esta automatizada en `src/ingestion/load_to_sql.py`. Para reproducir:
```
python src/ingestion/load_to_sql.py
```

## Fase 3 — API de consumo de datos

- **Framework**: FastAPI + Uvicorn
- **Fuente de datos**: `data/processed/chest_xray_validated.parquet` (cargado en memoria al iniciar)
- **Documentacion automatica**: Swagger UI disponible en `/docs` (OpenAPI generado por FastAPI)

### Endpoints disponibles

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Estado de la API y total de registros |
| GET | `/records` | Lista registros, con filtros opcionales `gender`, `finding` y `limit` |
| GET | `/records/{image_index}` | Detalle de un registro especifico por nombre de imagen |
| GET | `/stats` | Estadisticas agregadas (distribucion por genero, vista, edad) |


### Ejecutar localmente

```
uvicorn src.api.main:app --reload
```

Luego visitar `http://127.0.0.1:8000/docs` para la documentacion interactiva.

### Ejemplos de uso

```
GET /records?gender=M&limit=5
GET /records/00011065_007.png
GET /stats
```

## Proximas fases
- [x] Fase 2 - Blob Storage
- [x] Fase 2b - Azure SQL Database (Azure AD Authentication)
- [x] Fase 3 - API de consumo (FastAPI) + documentacion
- [ ] Fase 4 - Automatizacion con IA