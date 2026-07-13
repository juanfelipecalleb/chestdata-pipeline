import os
import pandas as pd
import pyodbc
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

load_dotenv()

SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
PARQUET_PATH = Path("data/processed/chest_xray_validated.parquet")

def get_connection():
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")

    token_bytes = bytes(token.token, "utf-8")
    exptoken = b""
    for i in token_bytes:
        exptoken += bytes([i])
        exptoken += bytes(1)

    token_struct = len(exptoken).to_bytes(4, byteorder="little") + exptoken

    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{SQL_SERVER},1433;"
        f"Database={SQL_DATABASE};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    SQL_COPT_SS_ACCESS_TOKEN = 1256
    conn = pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chest_xray_records' AND xtype='U')
        CREATE TABLE chest_xray_records (
            image_index NVARCHAR(50) PRIMARY KEY,
            finding_labels NVARCHAR(500),
            patient_age INT,
            patient_gender NVARCHAR(1),
            view_position NVARCHAR(2)
        )
    """)
    conn.commit()
    print("Tabla verificada/creada: chest_xray_records")


def load_data(conn):
    df = pd.read_parquet(PARQUET_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chest_xray_records")  # limpia antes de recargar (idempotente)

    for _, row in df.iterrows():
        labels_str = "|".join(row["finding_labels"])
        cursor.execute("""
            INSERT INTO chest_xray_records (image_index, finding_labels, patient_age, patient_gender, view_position)
            VALUES (?, ?, ?, ?, ?)
        """, row["image_index"], labels_str, int(row["patient_age"]), row["patient_gender"], row["view_position"])

    conn.commit()
    print(f"{len(df)} registros cargados en Azure SQL.")


def main():
    print("Conectando a Azure SQL con autenticacion Azure AD...")
    conn = get_connection()

    print("Creando tabla si no existe...")
    create_table(conn)

    print("Cargando datos...")
    load_data(conn)

    conn.close()
    print("Proceso completo.")


if __name__ == "__main__":
    main()