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
chestdata-pipeline/
├── data/
│   ├── raw/              # datos originales y subset (no versionado en git)
│   └── processed/        # datos validados en Parquet
├── src/
│   ├── ingestion/         # scripts de descarga/armado de subset
│   ├── validation/        # esquemas y validación de calidad
│   └── api/                # (próximamente) API de consumo de datos
├── notebooks/              # exploración de datos
└── docs/

## Próximas fases
- [ ] Fase 2 — Subida a Azure Blob Storage + Azure SQL
- [ ] Fase 3 — API de consumo (FastAPI) + documentación
- [ ] Fase 4 — Automatización con IA