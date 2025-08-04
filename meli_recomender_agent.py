import argparse
import json
import os
from datetime import date
import numpy as np
import pandas as pd
import joblib
from meli_insight_engine.llm.agents import rasoner_meli

# ------------- INFERENCIA DE CLUSTER ----------------

print("🔄 [1] Cargando artefactos de cluster...")
pre_pipe = joblib.load("models/pre_pipe.pkl")
kmeans   = joblib.load("models/kmeans.pkl")

FEATURES = list(pre_pipe.feature_names_in_)

CLUSTER_NAME = {
    1: "Power Sellers",
    2: "Sellers en Crecimiento",
    0: "Sellers Ocasionales",
    3: "Cazadores de Oferta",
    4: "Liquidadores / Outlet",
}

def clasificar_seller(metrics: dict) -> dict:
    print("🔎 [2] Realizando inferencia de cluster para el seller...")
    X = pd.DataFrame([metrics])[FEATURES]
    X_prep = pre_pipe.transform(X)
    cid    = int(kmeans.predict(X_prep)[0])
    print(f"✅   Seller clasificado en cluster {cid}: {CLUSTER_NAME.get(cid, 'Desconocido')}")
    return {"cluster_id": cid, "cluster_name": CLUSTER_NAME.get(cid, "Desconocido")}

# ------------------ CLI PRINCIPAL --------------------

def main():
    print("🚀 [0] Iniciando CLI de recomendación Mercado Libre.")
    parser = argparse.ArgumentParser(description="Estrategia personalizada Mercado Libre según temporada.")
    parser.add_argument("--input_json", type=str, help="Ruta al archivo JSON con métricas del seller.")
    parser.add_argument("--api_key", type=str, default=os.getenv("DEEPSEEK_API_KEY", ""), help="API KEY Deepseek")
    args = parser.parse_args()

    if args.input_json:
        print(f"📂 [0.1] Leyendo métricas del seller desde {args.input_json}")
        with open(args.input_json, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        input_payload = metrics.copy()
    else:
        print("⚠️  [0.2] No se pasó archivo, usando datos de ejemplo.")
        metrics = {
            "categorias_distintas": 15,
            "log_price_avg":       11.55,
            "log_stock_avg":       4.82,
            "num_publicaciones":   120,
            "porc_descuento":      0.27,
            "proporcion_refurb":   0.0,
            "proporcion_usados":   0.0,
            "rep_score":           4.1,
            "titulo_length_avg":   30,
        }
        input_payload = {
            "fecha_actual":         date.today().isoformat(),
            "cluster_name":         "",
            "publicaciones":        120,
            "categorias_distintas": 15,
            "stock_promedio":       124,
            "precio_medio_cop":     105_000,
            "descuento_pct":        0.27,
            "rep_score":            4.1,
            "tasa_cancelacion":     0.8,
        }

    # Inferencia del cluster
    print("🧠 [3] Haciendo inferencia de cluster...")
    cluster_info = clasificar_seller(metrics)
    input_payload["cluster_name"] = cluster_info["cluster_name"]  # Lo agrega automáticamente

    print(f"📦 [4] Payload para LLM:\n{json.dumps(input_payload, indent=2, ensure_ascii=False)}")

    print("🤖 [5] Llamando al agente generativo de recomendaciones (LLM)...")
    output = rasoner_meli.cot_chain(input_payload)
    print("\n✨ [RESULTADOS]")
    print("Contexto de temporada detectado:", output["temporada"])
    print("\nRecomendación personalizada:\n", output["estrategia"])

if __name__ == "__main__":
    main()
