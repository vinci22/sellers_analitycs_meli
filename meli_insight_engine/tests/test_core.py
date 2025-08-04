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
    test_csv.write_text("col1,col2\n1,a\n2,b")
    
    con = conectar_duckdb()
    from core.loader import registrar_csvs_como_vistas
    registrar_csvs_como_vistas(con, str(tmp_path))
    
    vistas = con.execute("SHOW TABLES").fetchall()
    assert any('data.test' in v[0] for v in vistas)
    con.close()