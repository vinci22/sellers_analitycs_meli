# Mercado Libre – **Seller Segmentation Challenge**

Este repositorio contiene la solución técnica solicitada:
identificar vendedores relevantes, agruparlos en segmentos accionables
y proponer extensiones basadas en IA generativa.

---

## 1. 🔍 Pregunta de negocio

> ¿Cómo podrías ayudar al equipo comercial a identificar estos sellers y generar segmentaciones útiles?

1. **Ponerles una “etiqueta” diaria a todos los vendedores**
   * Con el modelo de *k-means* ya sabemos a qué grupo pertenece cada uno.
   * Guardamos esa etiqueta en la base de datos:  **`Power Seller`** , **`En Crecimiento`** u  **`Ocasional`** .
   * Así, cuando el comercial abre su panel, ya ve el rótulo junto al nombre del vendedor.
2. **Mostrar en un solo gráfico por qué están donde están**
   * El PCA resume las 9 métricas en dos ejes muy intuitivos:
     * **PC1 → “Tamaño del catálogo”** (cuántos productos y stock).
     * **PC2 → “Estrategia de precios”** (qué tanto descuentan).
   * Pintamos los puntos con el color del cluster:
     * Arriba a la derecha aparecen los **Power Sellers** (grandes y sin rebajas locas).
     * En el medio, los  **En Crecimiento** .
     * Abajo, los  **Ocasionales** .
   * Un vistazo basta para explicarle a cualquier colega (sin fórmulas) por qué un vendedor es Power y otro no.
3. **Crear filtros y playbooks listos para usar**| Segmento                        | Cómo lo filtra el comercial        | Acción inmediata recomendada                               |
   | ------------------------------- | ----------------------------------- | ----------------------------------------------------------- |
   | **Power Seller**          | `cluster_name = "Power Seller"`   | Ofrecer comisión preferencial y logística premium.        |
   | **Seller en Crecimiento** | `cluster_name = "En Crecimiento"` | Enviar “Pack de Ads + asesoría” para que suban de nivel. |
   | **Ocasional**             | `cluster_name = "Ocasional"`      | Invitarlos a Seller University y darles alertas de calidad. |
4. **Alertas automáticas**
   * Si un Seller en Crecimiento supera 50 k USD de GMV y mantiene reputación ≥ 4, el sistema lanza una alerta: “🎉 Candidato a Power Seller”.
   * Si un Power Seller baja su reputación, alerta “⚠️ Riesgo de churn”.
5. **Medir el impacto sin complicaciones**
   * **Power Seller:** ver si su GMV crece mes a mes.
   * **Crecimiento:** cuántos escalan a Power en el trimestre.
   * **Ocasional:** caída de reclamos y subida de ventas tras el onboarding.

Con la etiqueta diaria, el gráfico PCA que lo explica todo y tres playbooks pre-armados, el equipo comercial sabrá **a quién mimar, a quién impulsar y a quién entrenar** sin necesidad de mirar una sola línea de código.


## 2. ✔️ Respuesta en una frase

Tres segmentos bien definidos (Premium, Consolidados, Ocasionales) explican > 80 % del GMV con métricas internas sólidas (Silhouette ≈ 0.49, DB ≈ 1.13).
Cada uno recibe acciones comerciales concretas (comisiones, Ads, logística).

---

## 3. 📑 Entregables de la prueba

| Ruta / archivo                                             | Descripción                                                                                                                                                                                       |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`notebooks/01_LMEDA_LLM_4_DATA_ANALYSIS.ipynb`** | Notebook de**EDA asistido por IA generativa**. Limpia, enriquece y explica el conjunto de datos, combinando pandas con prompts de LLM.                                                       |
| **`notebooks/02_clusters.ipynb`**                  | Ejecución íntegra del**modelo de clustering**: selección de *k* (codo + métricas internas), entrenamiento de MiniBatch K-Means, validación, perfiles numéricos y visualización PCA. |
| **`data/`**                                        | Carpeta de datasets.                                                                                                                                                                               |
| ├──**`df_challenge_meli.csv`**                  | Dataset**crudo** suministrado en la prueba.                                                                                                                                                  |
| ├──**`df_challenge_meli_limpio.csv`**           | Dataset**depurado y enriquecido** a nivel seller (feature-store).                                                                                                                            |
| ├──**`df_challenge_meli_cluster.csv`**          | Matriz final con la etiqueta **`cluster_id`** asignada a cada vendedor.                                                                                                                    |
| ├──**`pca_loadings.csv`**                       | Pesos de las variables en PC1 y PC2 para interpretar el PCA.                                                                                                                                       |
| └──**`meli_insight_engine/`**                   | Librería**custom** con utilidades de EDA y agentes LangChain reutilizables.                                                                                                                 |
| **`outputs/`**                                     | Resultados intermedios (tablas agregadas, perfiles, métricas…).                                                                                                                                  |
| **`outputs_prompts/`**                             | Salidas generadas por LLM:`<br> `•  `BASIC_RECOMMENDATION_PROMPT_HIPOTESIS.txt<br>`• `BASIC_RECOMMENDATION_PROMPT_JSON.json<br>`• `inspector_stats.json`                              |
| **`models/pre_pipe.pkl`**                          | Pipeline de**imputación + escalado robusto** (persistido con joblib).                                                                                                                       |
| **`models/kmeans.pkl`**                            | Modelo**MiniBatch K-Means** entrenado con *k = 3*.                                                                                                                                         |
| **`scripts/score_seller.py`**                      | Script CLI que recibe las métricas de un vendedor y devuelve su `cluster_id`.                                                                                                                   |
| **`llm/strategy_agent.py`**                        | Extensión (opción B): agente LangChain que redacta una**estrategia comercial personalizada** para cada seller.                                                                             |
| **`README.md`**                                    | Este documento de referencia.                                                                                                                                                                      |

## 4. 🛠️ Stack usado

| Tipo              | Herramientas                             |
| ----------------- | ---------------------------------------- |
| Análisis y ML    | Python 3.11, pandas, scikit-learn, numpy |
| Visualización    | matplotlib, seaborn                      |
| Persistencia      | joblib, CSV                              |
| GenAI (opción B) | LangChain + OpenAI embeddings / chat     |

---

## 5. 🧪 Metodología resumida

1. **Calidad de datos** – clipping de outliers, imputación mediana, eliminación de constantes.
2. **Feature engineering** – 9 métricas numéricas por seller (*stock, publicaciones, descuento, reputación…*).
3. **Escalado robusto** – resistente a outliers.
4. **Clustering** – MiniBatch K-Means

   * Selección *k* con codo, Silhouette, Davies-Bouldin.
   * Métricas finales: Silhouette 0.49, DB 1.13, CH 5 864.
5. **Interpretación** – perfiles (media, mediana, z-score) + PCA PC1/PC2.
6. **Uso en negocio** – tabla de acciones por cluster (ver Notebook).
7. **Extensión GenAI** – agente que, dado el perfil, sugiere la mejor palanca comercial.

---

## 6. 🚀 Ejecución rápida

```bash
# crear entorno y dependencias
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 1) reproducir clustering (guardará modelos)
python scripts/build_clusters.py --input data/df_challenge_meli.csv

# 2) etiquetar un nuevo seller
python scripts/score_seller.py --json sample_seller.json
# ⇒ {"cluster_id":1,"cluster_name":"Power Sellers Premium"}

# 3) (opción B) generar estrategia con GenAI
OPENAI_API_KEY=sk-... python llm/strategy_agent.py --json sample_seller.json
```

---

## 7. 📈 Métricas clave de calidad

| k           | Silhouette ↑   | DB ↓          | CH ↑           |
| ----------- | --------------- | -------------- | --------------- |
| **2** | **0.515** | **0.86** | 4 718           |
| **3** | 0.493           | 1.13           | **5 864** |
| 4+          | < 0.27          | > 1.21         | –              |

*k = 3* mantiene buena separación y ofrece granularidad accionable.

---

## 8. ⚙️ Reglas de negocio sugeridas

| Cluster       | Acción principal                    | KPI                         |
| ------------- | ------------------------------------ | --------------------------- |
| Power Sellers | Comisión preferencial + Fulfillment | ↑ GMV, retención          |
| Consolidados  | Bundle Ads + asesor                  | % migración a Premium      |
| Ocasionales   | Onboarding guiado + micro-crédito   | Reclamos < 2 %, crecimiento |

(Ver Notebook *Clustering* sección “Conclusiones”.)

---

## 9. Próximos pasos (si hubiera más tiempo)

* Afinar clusters con métricas de rentabilidad neta.
* Validación A/B en campañas de Ads.
* Dashboard Looker con funnel de migración entre segmentos.

---

**Autor:** Dario Arteaga – *versión 1.0 (Jul 2025)*
