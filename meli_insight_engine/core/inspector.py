import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import PercentFormatter


def resumen_columnas(con, tabla: str):
    """
    Devuelve un resumen de métricas básicas por columna: nulos, únicos, tipo.
    """
    cols =con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    resumen = []
    for col in cols:
        met = con.execute(f"""
            SELECT 
                '{col}' AS columna,
                COUNT(*) AS total,
                COUNT(DISTINCT "{col}") AS unicos,
                COUNT(*) - COUNT("{col}") AS nulos
            FROM "{tabla}"
        """).fetchdf()
        resumen.append(met)
    return pd.concat(resumen, ignore_index=True) if resumen else None

def distribucion_categoria(con, tabla: str, columna: str = None, top_n: int = 10):
    """Top N valores más frecuentes de columnas categóricas o de una columna específica"""
    if columna:
        # Análisis para una columna específica
        return con.execute(f"""
            SELECT 
                '{columna}' AS columna,
                "{columna}" AS valor,
                COUNT(*) AS frecuencia
            FROM "{tabla}"
            GROUP BY "{columna}"
            ORDER BY frecuencia DESC
            LIMIT {top_n}
        """).fetchdf()
    else:
        # Análisis para todas las columnas categóricas
        cols = tipos_datos(con, tabla)
        categoricas = cols[
            ~cols['type'].str.upper().isin(['INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC'])
        ]['column_name'].tolist()
        
        resultados = []
        for col in categoricas:
            try:
                df = con.execute(f"""
                    SELECT 
                        '{col}' AS columna,
                        "{col}" AS valor,
                        COUNT(*) AS frecuencia
                    FROM "{tabla}"
                    GROUP BY "{col}"
                    ORDER BY frecuencia DESC
                    LIMIT {top_n}
                """).fetchdf()
                resultados.append(df)
            except Exception as e:
                print(f"⚠️ Error al procesar columna {col}: {str(e)}")
        
        return pd.concat(resultados, ignore_index=True) if resultados else None

def info_tabla(con, tabla: str):
    """Devuelve el esquema (columnas y tipos) de una tabla."""
    return con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()

import pandas as pd

def dimensiones_tabla(con, tabla: str):
    """Devuelve el número de filas y columnas de una tabla"""
    return con.execute(f'SELECT COUNT(*) AS num_filas FROM "{tabla}"').fetchdf().merge(
           con.execute(f'SELECT COUNT(*) AS num_columnas FROM (DESCRIBE TABLE "{tabla}")').fetchdf(),
           how='cross')

def tipos_datos(con, tabla: str):
    """Devuelve el tipo de datos por columna de forma robusta"""
    try:
        # Intentamos con DESCRIBE primero
        schema_df = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()
        
        # Mapeo de nombres de columnas posibles
        col_name = next((col for col in schema_df.columns 
                        if col.lower() in ['column_name', 'name', 'field']), None)
        type_name = next((col for col in schema_df.columns 
                         if col.lower() in ['type', 'data_type']), None)
        
        if col_name and type_name:
            return schema_df[[col_name, type_name]].rename(
                columns={col_name: 'column_name', type_name: 'type'})
        
        # Si DESCRIBE no funciona, probamos con PRAGMA
        schema_df = con.execute(f'PRAGMA table_info("{tabla}")').fetchdf()
        return schema_df[['name', 'type']].rename(
            columns={'name': 'column_name'})
            
    except Exception as e:
        # Como último recurso, usamos information_schema
        return con.execute(f"""
            SELECT column_name, data_type AS type 
            FROM information_schema.columns 
            WHERE table_name = '{tabla}'
        """).fetchdf()

def estadisticos_numericos(con, tabla: str):
    """Calcula estadísticos básicos para columnas numéricas"""
    # Primero obtenemos los nombres y tipos de todas las columnas
    schema_df = tipos_datos(con, tabla)  # Reutilizamos nuestra función robusta
    
    # Filtramos las columnas numéricas
    numeric_types = ['INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC']
    cols = schema_df[
        schema_df['type'].str.upper().isin(numeric_types)
    ]['column_name'].tolist()
    
    if not cols:
        return None
        
    # Construimos la consulta dinámica
    select_parts = []
    for col in cols:
        select_parts.extend([
            f"MIN({col}) AS {col}_min",
            f"MAX({col}) AS {col}_max",
            f"AVG({col}) AS {col}_avg",
            f"STDDEV({col}) AS {col}_std"
        ])
    
    query = f"SELECT {', '.join(select_parts)} FROM \"{tabla}\""
    
    try:
        result = con.execute(query).fetchdf().transpose()
        result.columns = ['valor']  # Renombrar la columna para mejor presentación
        return result
    except Exception as e:
        print(f"Error al calcular estadísticos: {str(e)}")
        return None

def valores_constantes(con, tabla: str, umbral=1):
    """Identifica columnas con un único valor (o por debajo de un umbral)"""
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    
    resultados = []
    for col in cols:
        df = con.execute(f"""
            SELECT 
                '{col}' AS columna,
                COUNT(DISTINCT "{col}") AS valores_unicos
            FROM "{tabla}"
        """).fetchdf()
        resultados.append(df)
    
    res = pd.concat(resultados, ignore_index=True)
    return res[res['valores_unicos'] <= umbral]

def porcentaje_nulos(con, tabla: str):
    """Calcula el porcentaje de valores nulos por columna"""
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    
    resultados = []
    for col in cols:
        df = con.execute(f"""
            SELECT 
                '{col}' AS columna,
                (COUNT(*) - COUNT("{col}")) * 100.0 / COUNT(*) AS porcentaje_nulos
            FROM "{tabla}"
        """).fetchdf()
        resultados.append(df)
    
    return pd.concat(resultados, ignore_index=True).sort_values('porcentaje_nulos', ascending=False)

def analisis_inicial_completo(con, tabla: str, top_categorias: int = 5):
    """
    Realiza un análisis inicial completo del dataset y devuelve un diccionario con todos los resultados.

    Args:
        con: Conexión a la base de datos
        tabla: Nombre de la tabla a analizar
        top_categorias: Número de categorías a mostrar en el análisis de distribución

    Returns:
        Dict con todos los resultados del análisis inicial
    """
    resultados = {
        'dimensiones': dimensiones_tabla(con, tabla),
        'esquema': info_tabla(con, tabla),
        'tipos_datos': tipos_datos(con, tabla),
        'resumen_columnas': resumen_columnas(con, tabla),
        'estadisticos_numericos': estadisticos_numericos(con, tabla),
        'valores_constantes': valores_constantes(con, tabla),
        'porcentaje_nulos': porcentaje_nulos(con, tabla),
        'distribuciones': distribucion_categoria(con, tabla, top_n=top_categorias),
        'dominancia_categoria': skew_categorico(con, tabla),
        'entropia': entropia_columna(con, tabla),
        'booleanas': columnas_booleanas(con, tabla),
        'fechas_invalidas': columnas_fecha_invalida(con, tabla),
        'correlacion_numerica': correlaciones_numericas(con, tabla),

        # Nuevas métricas por seller_nickname
        'indice_variedad': indice_variedad(con, tabla),
        # 'tasa_renovacion': tasa_renovacion(con, tabla),
        'desviacion_precio': desviacion_precio(con, tabla),
        'proporcion_premium': proporcion_premium(con, tabla),
        'densidad_categoria': densidad_categoria(con, tabla),
        # 'frecuencia_temporal': frecuencia_temporal(con, tabla),
        'relacion_publicaciones_stock': relacion_publicaciones_stock(con, tabla),
        'ratio_nuevos_vs_reacondicionados': ratio_nuevos_vs_reacondicionados(con, tabla),
        'proporcion_precios_bajos': proporcion_precios_bajos(con, tabla)
    }


    # Análisis adicional consolidado
    resumen = resultados['resumen_columnas'].merge(
        resultados['tipos_datos'], 
        left_on='columna', 
        right_on='column_name'
    ).drop(columns=['column_name'])

    resumen = resumen.merge(
        resultados['porcentaje_nulos'],
        on='columna'
    )

    # Score de calidad de columna (bonus)
    resumen['score_calidad'] = resumen.apply(lambda row: calcular_score_calidad(row), axis=1)

    resultados['resumen_consolidado'] = resumen

    return resultados

# Puedes definir esta función para calcular el score según reglas simples:
def calcular_score_calidad(row):
    score = 1.0
    if row['nulos'] > 0:
        score -= 0.2
    if row['unicos'] == 1:
        score -= 0.5
    if 'char' in row['column_type'].lower() and row['unicos'] > 100:
        score -= 0.1
    return max(score, 0)

# Funciones auxiliares necesarias

def dimensiones_tabla(con, tabla: str):
    return con.execute(f"SELECT COUNT(*) AS filas FROM \"{tabla}\"").fetchdf().assign(columnas=len(info_tabla(con, tabla)))

def info_tabla(con, tabla: str):
    return con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()

def tipos_datos(con, tabla: str):
    return info_tabla(con, tabla)[['column_name', 'column_type']]

def resumen_columnas(con, tabla: str):
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    resumen = []
    for col in cols:
        met = con.execute(f'''
            SELECT 
                '{col}' AS columna,
                COUNT(*) AS total,
                COUNT(DISTINCT "{col}") AS unicos,
                COUNT(*) - COUNT("{col}") AS nulos
            FROM "{tabla}"
        ''').fetchdf()
        resumen.append(met)
    return pd.concat(resumen, ignore_index=True) if resumen else None

def porcentaje_nulos(con, tabla: str):
    df = resumen_columnas(con, tabla)
    df['porcentaje_nulos'] = df['nulos'] / df['total']
    return df[['columna', 'porcentaje_nulos']]

def valores_constantes(con, tabla: str):
    df = resumen_columnas(con, tabla)
    return df[df['unicos'] == 1][['columna']]

def estadisticos_numericos(con, tabla: str):
    cols = info_tabla(con, tabla)
    num_cols = cols[cols['column_type'].str.contains('INT|DOUBLE|FLOAT', case=False)]['column_name'].tolist()
    if not num_cols:
        return None

    partes = []
    for c in num_cols:
        partes.append(f'MIN("{c}") AS min_{c}')
        partes.append(f'MAX("{c}") AS max_{c}')
        partes.append(f'AVG("{c}") AS avg_{c}')
    
    query = f'SELECT {", ".join(partes)} FROM "{tabla}"'
    return con.execute(query).fetchdf()

def distribucion_categoria(con, tabla: str, top_n: int = 10):
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    resultados = []
    for col in cols:
        df = con.execute(f'''
            SELECT 
                '{col}' AS columna,
                "{col}" AS valor,
                COUNT(*) AS frecuencia
            FROM "{tabla}"
            GROUP BY "{col}"
            ORDER BY frecuencia DESC
            LIMIT {top_n}
        ''').fetchdf()
        resultados.append(df)
    return pd.concat(resultados, ignore_index=True) if resultados else None

def skew_categorico(con, tabla: str, umbral: float = 0.95):
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    resultados = []
    total = con.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]

    for col in cols:
        top = con.execute(f'''
            SELECT COUNT(*) AS freq
            FROM "{tabla}"
            GROUP BY "{col}"
            ORDER BY freq DESC
            LIMIT 1
        ''').fetchone()
        if top and top[0] / total >= umbral:
            resultados.append({'columna': col, 'dominancia': round(top[0] / total, 3)})
    return pd.DataFrame(resultados)

def entropia_columna(con, tabla: str):
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    resultados = []
    for col in cols:
        df = con.execute(f'''
            SELECT "{col}" AS valor, COUNT(*) AS freq
            FROM "{tabla}"
            GROUP BY "{col}"
        ''').fetchdf()
        total = df["freq"].sum()
        probs = df["freq"] / total
        entropia = -np.sum(probs * np.log2(probs + 1e-9))
        resultados.append({'columna': col, 'entropia': round(entropia, 3)})
    return pd.DataFrame(resultados)

def columnas_booleanas(con, tabla: str):
    cols = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()['column_name'].tolist()
    booleanas = []
    for col in cols:
        unicos = con.execute(f'SELECT DISTINCT "{col}" FROM "{tabla}"').fetchdf()
        if 1 <= len(unicos) <= 2:
            booleanas.append({'columna': col, 'valores': unicos[unicos.columns[0]].tolist()})
    return pd.DataFrame(booleanas)

def columnas_fecha_invalida(con, tabla: str):
    tipos = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()
    posibles_fechas = tipos[tipos['column_type'].str.contains("CHAR|TEXT", case=False)]['column_name'].tolist()
    resultados = []
    for col in posibles_fechas:
        try:
            df = con.execute(f'SELECT "{col}" FROM "{tabla}" WHERE "{col}" IS NOT NULL LIMIT 100').fetchdf()
            fechas_parseadas = pd.to_datetime(df[col], errors='coerce')
            parse_ratio = fechas_parseadas.notna().mean()
            if 0 < parse_ratio < 1:
                resultados.append({'columna': col, 'parseables': round(parse_ratio, 2)})
        except:
            continue
    return pd.DataFrame(resultados)

def tasa_rotacion(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        SUM(ventas) AS ventas_totales,
        SUM(stock) AS stock_total,
        CASE 
            WHEN SUM(stock) > 0 THEN CAST(SUM(ventas) AS DOUBLE) / SUM(stock)
            ELSE NULL 
        END AS tasa_rotacion
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()

def indice_variedad(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        COUNT(*) AS total_publicaciones,
        COUNT(DISTINCT titulo) AS titulos_unicos,
        CAST(COUNT(DISTINCT titulo) AS DOUBLE) / COUNT(*) AS indice_variedad
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()



# def tasa_renovacion(con, tabla: str):
#     query = f"""
#     SELECT 
#         seller_nickname,
#         COUNT(*) AS total_publicaciones,
#         SUM(CASE WHEN fecha_publicacion >= CURRENT_DATE - INTERVAL 30 DAY THEN 1 ELSE 0 END) AS publicaciones_recientes,
#         CAST(SUM(CASE WHEN fecha_publicacion >= CURRENT_DATE - INTERVAL 30 DAY THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) AS tasa_renovacion
#     FROM "{tabla}"
#     GROUP BY seller_nickname
#     """
#     return con.execute(query).fetchdf()


def desviacion_precio(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        STDDEV_SAMP(price) AS std_precio
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()

def proporcion_premium(con, tabla: str):
    p75 = con.execute(f"SELECT approx_quantile(price, 0.75) AS p75 FROM '{tabla}'").fetchdf().iloc[0]['p75']
    query = f"""
    SELECT 
        seller_nickname,
        COUNT(*) AS total,
        SUM(CASE WHEN price > {p75} THEN 1 ELSE 0 END) AS premium,
        CAST(SUM(CASE WHEN price > {p75} THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) AS proporcion_premium
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()

def densidad_categoria(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        COUNT(*) AS total_publicaciones,
        COUNT(DISTINCT category_id) AS total_categorias,
        CAST(COUNT(*) AS DOUBLE) / COUNT(DISTINCT category_id) AS densidad_categoria
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()


# def frecuencia_temporal(con, tabla: str):
#     query = f"""
#     SELECT 
#         seller_nickname,
#         COUNT(*) AS publicaciones,
#         MIN(fecha_publicacion) AS fecha_min,
#         MAX(fecha_publicacion) AS fecha_max,
#         CASE 
#             WHEN DATE_DIFF('day', MIN(fecha_publicacion), MAX(fecha_publicacion)) > 0 THEN
#                 COUNT(*) * 7.0 / DATE_DIFF('day', MIN(fecha_publicacion), MAX(fecha_publicacion))
#             ELSE NULL
#         END AS publicaciones_por_semana
#     FROM "{tabla}"
#     GROUP BY seller_nickname
#     """
#     return con.execute(query).fetchdf()


def relacion_publicaciones_stock(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        AVG(stock) AS promedio_stock,
        COUNT(*) AS total_publicaciones,
        CASE 
            WHEN COUNT(*) > 0 THEN AVG(stock) / COUNT(*)
            ELSE NULL
        END AS relacion_publicaciones_stock
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()

def ratio_nuevos_vs_reacondicionados(con, tabla: str):
    query = f"""
    SELECT 
        seller_nickname,
        SUM(CASE WHEN lower(condition) = 'new' THEN 1 ELSE 0 END) AS nuevos,
        SUM(CASE WHEN lower(condition) = 'used' THEN 1 ELSE 0 END) AS usados,
        CASE 
            WHEN SUM(CASE WHEN lower(condition) = 'used' THEN 1 ELSE 0 END) > 0 THEN 
                CAST(SUM(CASE WHEN lower(condition) = 'new' THEN 1 ELSE 0 END) AS DOUBLE) / 
                SUM(CASE WHEN lower(condition) = 'used' THEN 1 ELSE 0 END)
            ELSE NULL
        END AS ratio_nuevo_usado
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()


def proporcion_precios_bajos(con, tabla: str):
    avg_precio = con.execute(f"SELECT AVG(price) AS avg_precio FROM '{tabla}'").fetchdf().iloc[0]['avg_precio']
    query = f"""
    SELECT 
        seller_nickname,
        COUNT(*) AS total,
        SUM(CASE WHEN price < {avg_precio} THEN 1 ELSE 0 END) AS bajo_promedio,
        CAST(SUM(CASE WHEN price < {avg_precio} THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) AS proporcion_bajo_promedio
    FROM "{tabla}"
    GROUP BY seller_nickname
    """
    return con.execute(query).fetchdf()


def correlaciones_numericas(con, tabla: str):
    tipos = con.execute(f'DESCRIBE TABLE "{tabla}"').fetchdf()
    numeric_cols = tipos[tipos['column_type'].str.contains("INT|DOUBLE|FLOAT", case=False)]['column_name'].tolist()
    if not numeric_cols:
        return None

    columnas_str = ", ".join(f'"{col}"' for col in numeric_cols)
    query = f'SELECT {columnas_str} FROM "{tabla}"'
    df = con.execute(query).fetchdf()
    return df.corr().round(2)


def guardar_resultados_como_txt(resultados, nombre_archivo="analisis_datos"):
    """
    Guarda los resultados del análisis inicial en un archivo de texto formateado
    (Versión que no requiere tabulate)
    """
    from datetime import datetime
    import pandas as pd
    
    # Nombre del archivo con timestamp
    nombre_completo = f"../data/outputs_prompts/inspector_stats.txt"
    
    def df_to_text(df):
        """Convierte un DataFrame a texto formateado sin usar markdown"""
        return df.to_string(index=False) if isinstance(df, pd.DataFrame) else str(df)
    
    with open(nombre_completo, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("="*80 + "\n")
        f.write(f"ANÁLISIS INICIAL DE DATOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # 1. Dimensiones
        f.write("📊 DIMENSIONES DEL DATASET\n")
        f.write(f"• Filas: {resultados['dimensiones']['filas'].values[0]}\n")
        f.write(f"• Columnas: {resultados['dimensiones']['columnas'].values[0]}\n\n")
        
        # 2. Resumen consolidado
        f.write("📝 RESUMEN CONSOLIDADO POR COLUMNA\n")
        f.write(df_to_text(resultados.get('resumen_consolidado', 'No disponible'))) 
        f.write("\n\n")
        
        # 3. Estadísticos numéricos
        f.write("📈 ESTADÍSTICOS NUMÉRICOS\n")
        f.write(df_to_text(resultados.get('estadisticos_numericos', 'No se encontraron columnas numéricas')))
        f.write("\n\n")
        
        # 4. Distribuciones categóricas
        f.write("🏷️ DISTRIBUCIÓN DE CATEGORÍAS (TOP 5)\n")
        if 'distribuciones' in resultados and isinstance(resultados['distribuciones'], pd.DataFrame):
            for col in resultados['distribuciones']['columna'].unique():
                df_col = resultados['distribuciones'][resultados['distribuciones']['columna'] == col]
                f.write(f"\n• {col}:\n")
                f.write(df_to_text(df_col.head()))
        else:
            f.write("No se encontraron columnas categóricas\n")
        
        # 5. Problemas identificados
        f.write("\n\n⚠️ PROBLEMAS IDENTIFICADOS\n")
        if 'porcentaje_nulos' in resultados and isinstance(resultados['porcentaje_nulos'], pd.DataFrame):
            nulos_altos = resultados['porcentaje_nulos'][resultados['porcentaje_nulos']['porcentaje_nulos'] > 20]
            if not nulos_altos.empty:
                f.write("\n• Columnas con >20% de nulos:\n")
                f.write(df_to_text(nulos_altos))
        
        if 'valores_constantes' in resultados and isinstance(resultados['valores_constantes'], pd.DataFrame):
            f.write("\n• Columnas con valores constantes:\n")
            f.write(df_to_text(resultados['valores_constantes']))
        
        # 6. Métricas por seller
        f.write("\n\n📊 MÉTRICAS DESCRIPTIVAS POR SELLER\n")
        metricas_seller = [
            'indice_variedad',
            # 'tasa_renovacion',
            'desviacion_precio',
            'proporcion_premium',
            'densidad_categoria',
            # 'frecuencia_temporal',
            'relacion_publicaciones_stock',
            'ratio_nuevos_vs_reacondicionados',
            'proporcion_precios_bajos'
        ]

        for metrica in metricas_seller:
            if metrica in resultados and isinstance(resultados[metrica], pd.DataFrame):
                f.write(f"\n🔹 {metrica.upper().replace('_', ' ')}\n")
                f.write(df_to_text(resultados[metrica].head(10)))  # Muestra top 10 por métrica
                f.write("\n")
            else:
                f.write(f"\n🔹 {metrica}: No disponible o no es DataFrame\n")
    
    print(f"✅ Resultados guardados en: {nombre_completo}")



def plot_analisis_inicial(resultados, titulo="Análisis Inicial del Dataset"):
    """
    Genera visualizaciones para todas las métricas del análisis inicial.
    
    Args:
        resultados: Diccionario con los resultados de analisis_inicial_completo()
        titulo: Título general para el reporte
    """
    plt.figure(figsize=(16, 20))
    
    # Configuración general
    sns.set_style("whitegrid")
    plt.suptitle(titulo, y=1.02, fontsize=16)
    
    # 1. Dimensiones del dataset
    plt.subplot(4, 2, 1)
    dims = resultados['dimensiones']
    plt.barh(['Filas', 'Columnas'], [dims.iloc[0]['filas'], dims.iloc[0]['columnas']], color=['#1f77b4', '#ff7f0e'])
    plt.title('Dimensiones del Dataset')
    for i, v in enumerate([dims.iloc[0]['filas'], dims.iloc[0]['columnas']]):
        plt.text(v, i, f" {v:,}", color='black', va='center')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 2. Tipos de datos
    plt.subplot(4, 2, 2)
    tipos = resultados['tipos_datos']['type'].value_counts().reset_index()
    tipos.columns = ['Tipo', 'Cantidad']
    sns.barplot(x='Cantidad', y='Tipo', data=tipos, palette='viridis')
    plt.title('Distribución de Tipos de Datos')
    for i, v in enumerate(tipos['Cantidad']):
        plt.text(v, i, f" {v}", color='black', va='center')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 3. Porcentaje de nulos
    plt.subplot(4, 2, 3)
    nulos = resultados['porcentaje_nulos'].sort_values('porcentaje_nulos', ascending=False)
    nulos = nulos[nulos['porcentaje_nulos'] > 0]  # Solo mostrar columnas con nulos
    if not nulos.empty:
        sns.barplot(x='porcentaje_nulos', y='columna', data=nulos, palette='Reds_r')
        plt.title('Porcentaje de Valores Nulos por Columna')
        plt.xlabel('Porcentaje de nulos')
        plt.ylabel('Columna')
        plt.gca().xaxis.set_major_formatter(PercentFormatter(100))
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.text(0.5, 0.5, 'No hay valores nulos', ha='center', va='center')
        plt.title('Porcentaje de Valores Nulos por Columna')
        plt.axis('off')
    
    # 4. Valores constantes
    plt.subplot(4, 2, 4)
    constantes = resultados['valores_constantes']
    if not constantes.empty:
        plt.barh(constantes['columna'], [1]*len(constantes), color='orange')
        plt.title('Columnas con un único valor (constantes)')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.text(0.5, 0.5, 'No hay columnas constantes', ha='center', va='center')
        plt.title('Columnas con un único valor (constantes)')
        plt.axis('off')
    
    # 5. Distribución de categorías (top 5)
    plt.subplot(4, 2, 5)
    distrib = resultados['distribuciones']
    if not distrib.empty:
        top_cols = distrib['columna'].value_counts().index[:5]  # Top 5 columnas con más categorías
        for col in top_cols:
            df_col = distrib[distrib['columna'] == col].head(5)
            plt.barh(df_col['valor'], df_col['frecuencia'], alpha=0.6, label=col)
        plt.title('Distribución de Top Categorías (5 columnas)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.text(0.5, 0.5, 'No hay datos categóricos', ha='center', va='center')
        plt.title('Distribución de Top Categorías')
        plt.axis('off')
    
    # 6. Dominancia categórica
    plt.subplot(4, 2, 6)
    dominancia = resultados['dominancia_categoria']
    if not dominancia.empty:
        sns.barplot(x='dominancia', y='columna', data=dominancia, palette='Blues_r')
        plt.title('Columnas con categoría dominante (>95%)')
        plt.xlabel('Proporción de la categoría dominante')
        plt.gca().xaxis.set_major_formatter(PercentFormatter(1))
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.text(0.5, 0.5, 'No hay categorías dominantes', ha='center', va='center')
        plt.title('Columnas con categoría dominante (>95%)')
        plt.axis('off')
    
    # 7. Entropía de columnas
    plt.subplot(4, 2, 7)
    entropia = resultados['entropia']
    if not entropia.empty:
        entropia = entropia.sort_values('entropia', ascending=False)
        sns.barplot(x='entropia', y='columna', data=entropia.head(10), palette='Greens_r')
        plt.title('Top 10 Columnas con Mayor Entropía')
        plt.xlabel('Entropía (bits)')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.text(0.5, 0.5, 'No hay datos de entropía', ha='center', va='center')
        plt.title('Top 10 Columnas con Mayor Entropía')
        plt.axis('off')
    
    # 8. Correlaciones numéricas
    plt.subplot(4, 2, 8)
    corr = resultados['correlacion_numerica']
    if corr is not None and not corr.empty:
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', 
                    mask=mask, vmin=-1, vmax=1, center=0)
        plt.title('Matriz de Correlación (variables numéricas)')
    else:
        plt.text(0.5, 0.5, 'No hay variables numéricas', ha='center', va='center')
        plt.title('Matriz de Correlación (variables numéricas)')
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

def plot_metricas_vendedores(resultados, titulo="Métricas por Vendedor"):
    """
    Visualiza las métricas específicas por seller_nickname.
    """
    plt.figure(figsize=(16, 18))
    plt.suptitle(titulo, y=1.02, fontsize=16)
    
    # 1. Índice de variedad
    plt.subplot(4, 2, 1)
    variedad = resultados['indice_variedad'].sort_values('indice_variedad', ascending=False).head(10)
    sns.barplot(x='indice_variedad', y='seller_nickname', data=variedad, palette='viridis')
    plt.title('Top 10 Vendedores por Índice de Variedad')
    plt.xlabel('Índice de variedad (títulos únicos / total publicaciones)')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 2. Desviación de precios
    plt.subplot(4, 2, 2)
    desviacion = resultados['desviacion_precio'].sort_values('std_precio', ascending=False).head(10)
    sns.barplot(x='std_precio', y='seller_nickname', data=desviacion, palette='magma')
    plt.title('Top 10 Vendedores con Mayor Variabilidad de Precios')
    plt.xlabel('Desviación estándar de precios')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 3. Proporción de productos premium
    plt.subplot(4, 2, 3)
    premium = resultados['proporcion_premium'].sort_values('proporcion_premium', ascending=False).head(10)
    sns.barplot(x='proporcion_premium', y='seller_nickname', data=premium, palette='rocket')
    plt.title('Top 10 Vendedores con Mayor % de Productos Premium')
    plt.xlabel('Proporción de productos premium (precio > P75)')
    plt.gca().xaxis.set_major_formatter(PercentFormatter(1))
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 4. Densidad por categoría
    plt.subplot(4, 2, 4)
    densidad = resultados['densidad_categoria'].sort_values('densidad_categoria', ascending=False).head(10)
    sns.barplot(x='densidad_categoria', y='seller_nickname', data=densidad, palette='flare')
    plt.title('Top 10 Vendedores con Mayor Densidad por Categoría')
    plt.xlabel('Publicaciones por categoría (mayor = más especializado)')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 5. Relación publicaciones/stock
    plt.subplot(4, 2, 5)
    rel_stock = resultados['relacion_publicaciones_stock'].sort_values('relacion_publicaciones_stock', ascending=False).head(10)
    sns.barplot(x='relacion_publicaciones_stock', y='seller_nickname', data=rel_stock, palette='crest')
    plt.title('Top 10 Vendedores con Mayor Stock por Publicación')
    plt.xlabel('Stock promedio / total publicaciones')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 6. Ratio nuevos vs reacondicionados
    plt.subplot(4, 2, 6)
    ratio = resultados['ratio_nuevos_vs_reacondicionados'].sort_values('ratio_nuevo_usado', ascending=False).head(10)
    sns.barplot(x='ratio_nuevo_usado', y='seller_nickname', data=ratio, palette='mako')
    plt.title('Top 10 Vendedores con Mayor Ratio Nuevos/Usados')
    plt.xlabel('Ratio productos nuevos vs usados')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 7. Proporción de precios bajos
    plt.subplot(4, 2, 7)
    bajos = resultados['proporcion_precios_bajos'].sort_values('proporcion_bajo_promedio', ascending=False).head(10)
    sns.barplot(x='proporcion_bajo_promedio', y='seller_nickname', data=bajos, palette='viridis')
    plt.title('Top 10 Vendedores con Mayor % de Precios Bajos')
    plt.xlabel('Proporción de productos con precio < promedio')
    plt.gca().xaxis.set_major_formatter(PercentFormatter(1))
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 8. Tasa de rotación (si está disponible)
    if 'tasa_rotacion' in resultados:
        plt.subplot(4, 2, 8)
        rotacion = resultados['tasa_rotacion'].sort_values('tasa_rotacion', ascending=False).head(10)
        sns.barplot(x='tasa_rotacion', y='seller_nickname', data=rotacion, palette='rocket')
        plt.title('Top 10 Vendedores por Tasa de Rotación')
        plt.xlabel('Tasa de rotación (ventas / stock)')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
    else:
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

def plot_estadisticos_numericos(estadisticos, titulo="Estadísticos de Columnas Numéricas"):
    """
    Visualiza los estadísticos numéricos (min, max, avg, std).
    """
    if estadisticos is None or estadisticos.empty:
        print("No hay columnas numéricas para mostrar")
        return
    
    # Procesar los datos para visualización
    stats = estadisticos.reset_index()
    stats[['columna', 'metrica']] = stats['index'].str.split('_', n=1, expand=True)
    stats_pivot = stats.pivot(index='columna', columns='metrica', values='valor')
    
    # Ordenar por media descendente
    stats_pivot = stats_pivot.sort_values('avg', ascending=False)
    
    # Crear el gráfico
    plt.figure(figsize=(12, 8))
    
    # Barras para promedios
    bars = plt.barh(stats_pivot.index, stats_pivot['avg'], color='skyblue', label='Promedio')
    plt.bar_label(bars, fmt='%.2f', padding=3)
    
    # Líneas para mínimos y máximos
    for i, col in enumerate(stats_pivot.index):
        plt.plot([stats_pivot.loc[col, 'min'], stats_pivot.loc[col, 'max']], [i, i], 
                 color='black', marker='|', markersize=10, linewidth=2)
    
    # Marcadores para desviación estándar
    for i, col in enumerate(stats_pivot.index):
        avg = stats_pivot.loc[col, 'avg']
        std = stats_pivot.loc[col, 'std']
        plt.plot([avg - std, avg + std], [i, i], color='red', linewidth=3, alpha=0.7)
    
    plt.title(titulo)
    plt.xlabel('Valor')
    plt.ylabel('Columna')
    plt.legend(['Rango (min-max)', 'Desviación estándar', 'Promedio'])
    plt.gca().invert_yaxis()
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def visualizar_todo(con, tabla: str):
    """
    Ejecuta todas las funciones de análisis y visualización para una tabla.
    """
    # Obtener todos los resultados
    resultados = analisis_inicial_completo(con, tabla)
    
    # Visualizar todo
    plot_analisis_inicial(resultados, f"Análisis Completo - {tabla}")
    
    if resultados['estadisticos_numericos'] is not None:
        plot_estadisticos_numericos(resultados['estadisticos_numericos'], 
                                   f"Estadísticos Numéricos - {tabla}")
    
    plot_metricas_vendedores(resultados, f"Métricas por Vendedor - {tabla}")
    
    # Mostrar resumen consolidado como tabla
    print("\nResumen Consolidado de Calidad de Columnas:")
    
    # Try to use display if in Jupyter, otherwise print
    try:
        from IPython.display import display
        display(resultados['resumen_consolidado'].sort_values('score_calidad'))
    except ImportError:
        print(resultados['resumen_consolidado'].sort_values('score_calidad').to_string())