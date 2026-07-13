# Arquitectura del proyecto

Flujo end-to-end: Kaggle -> Validacion (Pydantic) -> Parquet -> Azure Blob Storage 
+ Azure SQL Database -> API (FastAPI) -> Enriquecimiento (ICD-10-CM) -> Agente de IA 
(GitHub Models).

Ver diagrama completo en el README principal o solicitar version visual actualizada.