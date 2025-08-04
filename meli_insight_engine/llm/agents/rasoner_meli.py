import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from ..prompts.templates import season_prompt,strategy_prompt

# --- Inicializa el modelo Deepseek ---
llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    temperature=0.3
)

# --- Define las cadenas LangChain ---
season_chain = LLMChain(llm=llm, prompt=season_prompt, output_key="temporada")
strategy_chain = LLMChain(llm=llm, prompt=strategy_prompt, output_key="estrategia")

cot_chain = SequentialChain(
    chains=[season_chain, strategy_chain],
    input_variables=[
        "fecha_actual", "cluster_name", "publicaciones",
        "categorias_distintas", "stock_promedio", "precio_medio_cop",
        "descuento_pct", "rep_score", "tasa_cancelacion"
    ],
    output_variables=["temporada", "estrategia"]
)
