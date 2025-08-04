# meli_insight_engine/llm/agent_template.py

import os
import json
import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class TemplateAgent:
    def __init__(self, prompt_template: str, template_name: str):
        self.template_name = template_name
        self.prompt = PromptTemplate.from_template(prompt_template)

        self.llm = ChatOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.3
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def run(self, input_path: str, output_dir: str = "../data/outputs_prompts") -> str:
        with open(input_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        respuesta = self.chain.run(contenido=contenido)

        os.makedirs(output_dir, exist_ok=True)

        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{self.template_name}.txt"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(respuesta)

        return output_path
