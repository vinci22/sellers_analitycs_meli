from langchain.prompts import PromptTemplate
BASIC_RECOMMENDATION_PROMPT_JSON = """
Basado en el siguiente análisis estadístico detallado, genera un reporte JSON estructurado que:

{contenido}

1. Clasifique exactamente cada variable según su tipo y características únicas
2. Identifique todos los problemas de calidad de datos con acciones específicas por tipo
3. Recomiende transformaciones técnicas adecuadas para cada caso
4. Señale relaciones clave a investigar

El JSON DEBE seguir ESTE FORMATO exactamente, adaptando las soluciones al tipo específico de cada variable:

{{
  "dataset_overview": {{
    "total_records": {{total_records}},
    "total_columns": {{total_columns}},
    "columns_by_type": {{
      "numeric": {{
        "continuous": [
          {{
            "column": "{{numeric_continuous_column}}",
            "stats": {{
              "min": {{min_value}},
              "max": {{max_value}},
              "mean": {{mean_value}},
              "freq_values": ["{{frequent_value}} ({{frequency}})"],
              "outlier_analysis": "{{outlier_description}}"
            }}
          }}
        ],
        "discrete": [
          {{
            "column": "{{numeric_discrete_column}}",
            "stats": {{
              "min": {{min_value}},
              "max": {{max_value}},
              "mean": {{mean_value}},
              "freq_values": ["{{frequent_value}} ({{frequency}})"],
              "distribution_analysis": "{{distribution_description}}"
            }}
          }}
        ]
      }},
      "categorical": {{
        "ordinal": [
          {{
            "column": "{{ordinal_column}}",
            "stats": {{
              "values": ["{{category}} ({{count}})"],
              "hierarchy": "{{hierarchy_description}}",
              "balance_analysis": "{{balance_description}}"
            }}
          }}
        ],
        "nominal": [
          {{
            "column": "{{nominal_column}}",
            "stats": {{
              "values": ["{{category}} ({{count}})"],
              "dominance_analysis": "{{dominance_description}}"
            }}
          }}
        ]
      }},
      "boolean": [
        {{
          "column": "{{boolean_column}}",
          "stats": {{
            "true_count": {{true_count}},
            "false_count": {{false_count}},
            "imbalance_ratio": "{{ratio}}",
            "business_impact": "{{impact_description}}"
          }}
        }}
      ],
      "text": [
        {{
          "column": "{{text_column}}",
          "stats": {{
            "unique_count": {{unique_count}},
            "most_common": ["{{sample_text}} ({{count}})"],
            "length_analysis": "{{length_description}}"
          }}
        }}
      ],
      "id": [
        {{
          "column": "{{id_column}}",
          "stats": {{
            "unique_count": {{unique_count}},
            "top_values": ["{{sample_value}} ({{count}})"],
            "concentration_analysis": "{{concentration_description}}"
          }}
        }}
      ]
    }}
  }},
  "detailed_metrics_analysis": {{
    "{{numeric_variable}}": {{
      "value_range": "{{range_description}}",
      "suspicious_values": {{
        "{{value_type}}": "{{description}}"
      }},
      "recommended_handling": {{
        "cleaning": "{{cleaning_method}}",
        "transformation": "{{transformation_method}}"
      }}
    }},
    "{{categorical_variable}}": {{
      "distribution_insights": {{
        "{{insight_name}}": "{{insight_description}}"
      }},
      "business_interpretation": "{{business_meaning}}"
    }}
  }},
  "advanced_metrics": {{
    "{{metric_group}}": {{
      "{{specific_metric}}": {{
        "analysis": "{{analysis_description}}",
        "business_implication": "{{business_impact}}"
      }}
    }}
  }},
  "transformations_recommended": {{
    "priority_actions": [
      {{
        "action": "{{action_name}}",
        "parameters": {{
          "{{param_name}}": {{param_value}}
        }},
        "reason": "{{justification}}"
      }}
    ]
  }}
}}

Instrucciones críticas:
1. Mapear CADA columna del dataset a su tipo específico (no genérico)
2. Para problemas de calidad: considerar COMBINACIÓN de tipo de dato + estadísticas únicas
3. Las transformaciones deben ser TÉCNICAMENTE APROPIADAS para cada tipo de problema
4. Incluir TODAS las columnas en la clasificación inicial
5. Las relaciones a investigar deben basarse en patrones observables en los datos

"""

BASIC_RECOMMENDATION_PROMPT_HIPOTESIS = """
### Analiza el siguiente resumen estadístico de un dataset (en formato JSON) y genera un reporte de comprensión inicial que responda a estos objetivos clave:

{contenido}

### 🔍 **Secciones Requeridas en la Respuesta:**

#### 1. **Estructura Básica**
- Total registros: 
- Total variables: 
- Variables clave identificadas (máx. 5): 
  - [Tipo] [Nombre]: [Breve descripción de utilidad]

#### 2. **Hallazgos de Calidad**  
Para cada problema identificado:
- `[Nombre de columna]`:
  - Tipo de problema: [missing/outliers/cardinalidad/etc.]
  - Severidad: [alta/media/baja] (justificar con métrica)
  - Acción sugerida: [eliminar/imputar/transformar] + [técnica específica según tipo de variable]

#### 3. **Relaciones Potenciales**  
Listar pares de variables prometedoras para análisis:
- `[Var1]` ↔ `[Var2]`: [Tipo de relación hipotética] + [Método sugerido para validar]

#### 4. **Recomendaciones para EDA**  
- Variables prioritarias para análisis: 
  - [Grupo 1]: Para responder [objetivo X]
  - [Grupo 2]: Para explorar [relación Y]
- Transformaciones necesarias previas:
  - `[Columna]`: [Transformación] + [Motivo técnico]

#### 5. **Advertencias Clave**  
- [Limitación 1]: Impactará en [parte del análisis]
- [Limitación 2]: Requiere [acción específica]

#### 6. **Conclusión Ejecutiva**
- Resumen breve de la calidad del dataset (buena/aceptable/deficiente), con argumentos técnicos.
- Variables más prometedoras para modelado o análisis exploratorio.
- Riesgos principales a controlar antes de seguir con clustering o modelos.
- Valor potencial del dataset si se aplican las transformaciones sugeridas.

### ✨ **Requisitos Formales:**
- Usar lenguaje técnico pero claro
- Priorizar hallazgos por impacto analítico
- Vincular cada recomendación al tipo de variable afectada
- Incluir métricas cuantitativas para justificar decisiones
"""



BASE_PROMPT_PSA_CORELATIO = """
# ──────────────────────────────────────────────────────────────────────────

Eres asesor comercial senior de Mercado Libre.

El vendedor pertenece al segmento **{{cluster_name}}**.
Su objetivo comercial es:

{{#if (eq cluster_name "Power Seller")}}
• Retenerlo y aumentar GMV con beneficios exclusivos (comisión preferencial, logística premium).
{{/if}}
{{#if (eq cluster_name "Seller en Crecimiento")}}
• Impulsar crecimiento para que ascienda a Power (más ventas, mejor reputación).
{{/if}}
{{#if (eq cluster_name "Ocasional")}}
• Capacitarlo y mejorar calidad para reducir reclamos y subir ventas.
{{/if}}

Métricas del vendedor
─────────────────────
• Publicaciones        : {{publicaciones}}
• Categorías distintas : {{categorias_distintas}}
• Stock medio (uds)    : {{stock_promedio}}
• Precio medio         : ${{precio_medio_cop:,}}
• Descuento medio      : {{descuento_pct:.0%}}
• Reputación           : {{rep_score}} / 5
• Cancelación          : {{tasa_cancelacion:.1%}}

### Instrucciones
1. Propón **una** acción concreta y prioritaria (≤150 palabras).
2. Justifica brevemente por qué funcionará para este segmento.
3. Sé claro, directo y orientado a negocio; no repitas las métricas textualmente.

"""

season_prompt = PromptTemplate(
    template="""
Actúa como analista comercial experto en e-commerce LATAM.

Pregunta: ¿Qué contexto de temporada afecta hoy la venta en Mercado Libre Colombia?
Tienes acceso al calendario y sabes si hay campañas activas, vacaciones escolares, festivales o eventos masivos.

Fecha de hoy: {fecha_actual}

Responde SOLO una de estas opciones, de manera concisa:
- Black Sale
- Hot Sale
- Cyberlunes
- Fin de año / Navidad
- Vacaciones mitad de año
- Día del Padre/Madre
- Temporada baja
- Otra campaña: [nómbrala]
- Ninguna campaña

Explica en una frase tu razonamiento.
""",
    input_variables=["fecha_actual"]
)

strategy_prompt = PromptTemplate(
    template="""
Eres asesor comercial de Mercado Libre.

Hoy es: {fecha_actual} | Temporada: {temporada}

El vendedor es del segmento **{cluster_name}**.
Tu objetivo es proponer UNA acción prioritaria para aumentar ventas y margen, considerando:
– El segmento del vendedor.
– Las métricas clave.
– El contexto de temporada (ej: Black Sale, vacaciones, etc).

Métricas:
• Publicaciones        : {publicaciones}
• Categorías distintas : {categorias_distintas}
• Stock medio (uds)    : {stock_promedio}
• Precio medio         : ${precio_medio_cop:,}
• Descuento medio      : {descuento_pct:.0%}
• Reputación           : {rep_score}/5
• Cancelación          : {tasa_cancelacion:.1%}

# Instrucción
- Sé específico: si hay Black Sale, sugiere un boost fuerte, si es temporada baja, aconseja conservar margen.
- No repitas las métricas textualmente; sé breve y orientado a negocio.

### Estrategia
""",
    input_variables=[
        "fecha_actual", "temporada", "cluster_name", "publicaciones",
        "categorias_distintas", "stock_promedio", "precio_medio_cop",
        "descuento_pct", "rep_score", "tasa_cancelacion"
    ]
)
