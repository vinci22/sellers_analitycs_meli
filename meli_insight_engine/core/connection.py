import duckdb

def conectar_duckdb(path_db: str = ":memory:"):
    """Establece una conexión a DuckDB (por defecto, en memoria)."""
    return duckdb.connect(path_db)