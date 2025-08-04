import os

def registrar_csvs_como_vistas(con, folder_path: str, schema: str = "data"):
    """
    Registra todos los archivos .csv de una carpeta como vistas en DuckDB.
    """
    for file in os.listdir(folder_path):
        if file.endswith('.csv'):
            nombre_archivo = file.replace('.csv', '').replace('-', '_')
            table_name = f"{schema}.{nombre_archivo}"
            file_path = os.path.join(folder_path, file)
            con.execute(f"""
                CREATE VIEW "{table_name}" AS 
                SELECT * FROM read_csv_auto('{file_path}')
            """)

def verificar_vistas(con, schema="data"):
    """Lista las vistas registradas con el prefijo del esquema dado."""
    return con.execute(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type = 'VIEW'
          AND table_name LIKE '{schema}.%'
    """).fetchdf()