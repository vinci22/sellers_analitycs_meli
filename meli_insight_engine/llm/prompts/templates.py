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
# 📝 Prompt-template para interpretar PCA + Clusters  
*(sustituye sólo las llaves {{…}} con tu información)*

Eres un **data scientist senior**.  
A continuación tendrás dos bloques de entrada:

**🔹 PCA**  
{pca_valores}

**🔹 Resumen/tabla de clusters u otra información contextual**  
{contenido}

## Tareas que debes realizar
1. **Explica, en lenguaje claro para negocio, qué representan PC1 y PC2** según las cargas mostradas.  
2. **Relaciona los clusters con el plano PC1-PC2**: indica dónde se ubican y qué significa su posición.  
3. **Asigna o valida etiquetas intuitivas** para cada cluster (máx. 6 palabras por etiqueta).  
4. **Extrae 3-5 insights accionables** que ayuden a Mercado Libre a diseñar estrategias comerciales personalizadas (pricing, promociones, soporte, etc.).  
5. Si detectas **riesgos o limitaciones** metodológicas, menciónalos brevemente.

### Formato de salida esperado
- **Resumen de PC1 / PC2** (2-3 frases cada uno)  
- **Tabla “Cluster – Etiqueta – Rasgos clave”**  
- **Lista numerada de insights**  
- **Alerta de riesgos (opcional, ≤3 líneas)**

"""