import os
from pathlib import Path

def crear_estructura_paquete():
    base_path = Path("meli_insight_engine")  # nombre del paquete instalable
    
    encoding = 'utf-8'
    
    # Crear estructura base
    (base_path / "core").mkdir(parents=True, exist_ok=True)  # carpeta de código fuente (renombrada)
    (base_path / "tests").mkdir(exist_ok=True)

    archivos = {
        "core/__init__.py": """
from .connection import conectar_duckdb
from .loader import registrar_csvs_como_vistas, verificar_vistas
from .inspector import resumen_columnas, distribucion_categoria, info_tabla

__all__ = [
    "conectar_duckdb",
    "registrar_csvs_como_vistas",
    "verificar_vistas",
    "resumen_columnas",
    "distribucion_categoria",
    "info_tabla"
]
""",
        "core/connection.py": """
import duckdb

def conectar_duckdb(path_db: str = ":memory:"):
    \"\"\"Establece una conexión a DuckDB (por defecto, en memoria).\"\"\"
    return duckdb.connect(path_db)
""",
        "core/loader.py": """
import os

def registrar_csvs_como_vistas(con, folder_path: str, schema: str = "data"):
    \"\"\"
    Registra todos los archivos .csv de una carpeta como vistas en DuckDB.
    \"\"\"
    for file in os.listdir(folder_path):
        if file.endswith('.csv'):
            nombre_archivo = file.replace('.csv', '').replace('-', '_')
            table_name = f"{schema}.{nombre_archivo}"
            file_path = os.path.join(folder_path, file)
            con.execute(f\"\"\"
                CREATE VIEW "{table_name}" AS 
                SELECT * FROM read_csv_auto('{file_path}')
            \"\"\")

def verificar_vistas(con, schema="data"):
    \"\"\"Lista las vistas registradas con el prefijo del esquema dado.\"\"\"
    return con.execute(f\"\"\"
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type = 'VIEW'
          AND table_name LIKE '{schema}.%'
    \"\"\").fetchdf()
""",
        "core/inspector.py": """
def resumen_columnas(con, tabla: str):
    \"\"\"
    Devuelve un resumen de métricas básicas por columna: nulos, únicos, tipo.
    \"\"\"
    cols = con.execute(f"PRAGMA table_info('{tabla}')").fetchdf()['name'].tolist()
    resumen = []
    for col in cols:
        met = con.execute(f\"\"\"
            SELECT 
                '{col}' AS columna,
                COUNT(*) AS total,
                COUNT(DISTINCT {col}) AS unicos,
                COUNT(*) - COUNT({col}) AS nulos
            FROM "{tabla}"
        \"\"\").fetchdf()
        resumen.append(met)
    if resumen:
        union_sql = " UNION ALL ".join([f"SELECT * FROM met_{i}" for i in range(len(resumen))])
        return con.sql(union_sql).fetchdf()
    return None

def distribucion_categoria(con, tabla: str, columna: str, top_n: int = 10):
    \"\"\"Top N valores más frecuentes de una columna.\"\"\"
    return con.execute(f\"\"\"
        SELECT {columna}, COUNT(*) AS frecuencia
        FROM "{tabla}"
        GROUP BY {columna}
        ORDER BY frecuencia DESC
        LIMIT {top_n}
    \"\"\").fetchdf()

def info_tabla(con, tabla: str):
    \"\"\"Devuelve el esquema (columnas y tipos) de una tabla.\"\"\"
    return con.execute(f"PRAGMA table_info('{tabla}')").fetchdf()
""",
        "core/llm_utils.py": """
# Módulo para integración con LLMs (futuro desarrollo)
pass
""",
        "tests/test_core.py": """
from core import conectar_duckdb
import duckdb
import os
import pytest

def test_conexion():
    con = conectar_duckdb()
    assert isinstance(con, duckdb.DuckDBPyConnection)
    con.close()

def test_registro_vistas(tmp_path):
    test_csv = tmp_path / "test.csv"
    test_csv.write_text("col1,col2\\n1,a\\n2,b")
    
    con = conectar_duckdb()
    from core.loader import registrar_csvs_como_vistas
    registrar_csvs_como_vistas(con, str(tmp_path))
    
    vistas = con.execute("SHOW TABLES").fetchall()
    assert any('data.test' in v[0] for v in vistas)
    con.close()
""",
        "pyproject.toml": """
[project]
name = "meli_insight_engine"
version = "0.1.0"
description = "Toolkit para analisis de datos de sellers en MELI con LLMs y DuckDB"
authors = [
    { name = "Tu Nombre", email = "tu@email.com" }
]
license = "MIT"
readme = "README.md"
requires-python = ">=3.8"
dependencies = ["duckdb"]

[tool.setuptools.packages.find]
where = ["core"]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
""",
        "README.md": """
# meli_insight_engine

Este paquete permite analizar archivos CSV de vendedores de Mercado Libre usando DuckDB como motor SQL.

## Instalación
```bash
pip install -e ."""
    }


    # Escribir todos los archivos con codificación UTF-8
    for path, content in archivos.items():
        file_path = base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content.strip())

    print(f"Estructura creada correctamente en {base_path.resolve()}")

crear_estructura_paquete()