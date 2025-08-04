
import duckdb as dck 
import os

"""
    Registra automáticamente todos los archivos .csv de una carpeta como vistas en DuckDB.

    Esta función permite trabajar con los archivos CSV como si fueran tablas dentro de una base de datos, 
    usando una sintaxis tipo 'data.nombre_archivo'. Es una forma personalizada (custom) de simular una 
    base de datos basada en archivos planos.

    Parámetros:
    - con: conexión activa a DuckDB (en memoria o persistente).
    - folder_path: ruta a la carpeta que contiene los archivos CSV.

    Ejemplo:
        registrar_csvs_como_vistas(con, 'data')
        con.execute("SELECT * FROM 'data.ventas_junio'").fetchdf()
"""

# Crear conexión (puede ser en memoria o a archivo .duckdb si quieres persistencia)
con = dck.connect()

# Carpeta donde están los archivos
folder_path = '../data'

# Registrar automáticamente cada archivo .csv como una vista
for file in os.listdir(folder_path):
    if file.endswith('.csv'):
        nombre_archivo = file.replace('.csv', '').replace('-', '_')
        table_name = f"data.{nombre_archivo}"
        file_path = os.path.join(folder_path, file)
        con.execute(f"""
            CREATE VIEW "{table_name}" AS 
            SELECT * FROM read_csv_auto('{file_path}')
        """)
def verificar_vistas_registradas(con):
    """
    Verifica que las vistas creadas a partir de archivos CSV se hayan registrado correctamente en DuckDB.
    
    Devuelve un DataFrame con los nombres de las vistas que comienzan con el prefijo 'data.'.
    Esto permite confirmar que los archivos fueron cargados exitosamente y están listos para consultas SQL.
    """
    return con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type = 'VIEW'
          AND table_name LIKE 'data.%'
    """).fetchdf()