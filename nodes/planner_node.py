from models.models import AgentState
from typing import Dict
from pydantic import ValidationError
from models.models import Plan
import json
from utils.tool_map import tool_map
from langchain_openai import ChatOpenAI

def planner_node(state: AgentState) -> Dict:
    print("--- 🧠 EXECUTANDO O PLANEJADOR ---")
    
    user_request = state["messages"][0].content
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
    schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'srag_diario';"
    try:
        schema = tool_map["execute_srag_query"].invoke(schema_query)
        prompt = f"""Você é um analista de dados sênior. Sua tarefa é criar um plano de ação para responder a uma solicitação do usuário.\nA solicitação é: \"{user_request}\".\n\nVocê tem acesso a uma tabela 'srag_diario' com o seguinte esquema:\n{schema}\n\nCrie um plano passo a passo para responder à solicitação. Cada passo deve ser um objeto JSON com as chaves: 'passo' (número do passo), 'tarefa' (descrição clara da tarefa) e 'ferramenta' (nome exato da ferramenta a ser usada).\nResponda APENAS com um objeto JSON contendo uma chave \"plano\" com uma lista desses objetos.\nExemplo: {{\"plano\": [{{\"passo\": 1, \"tarefa\": \"Calcular a taxa de mortalidade total por COVID (CLASSI_FIN = 5).\", \"ferramenta\": \"execute_srag_query\"}}]}}\n"""
        print(f"Enviando prompt para o modelo: {prompt}")
        response = llm.invoke(prompt)
        print("Resposta recebida do modelo.")
        print(response) 
        try:
            plan_data = json.loads(response.content)
            validated = Plan(**plan_data)
            return {"plan": [step.model_dump() for step in validated.plano]}
        except (ValidationError, Exception) as e:
            print(f"Erro de validação do plano: {e}")
            return {"plan": [], "error": f"Erro ao validar o plano: {e}"}
    except Exception as e:
        print(f"Erro ao executar o planner_node: {e}")
        return {"plan": [], "error": f"Erro ao executar o planner_node: {e}"}