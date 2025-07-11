
from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map
from langchain_openai import ChatOpenAI
import json


def final_review_node(state: AgentState) -> Dict:
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
    final_report = state['messages'][-1]
    prompt = f"""Avalie o seguinte relatório gerado por IA:\n---\n{final_report}\n---\nO relatório contém alguma informação ofensiva, inadequada ou dados sensíveis? Responda apenas com um JSON: {{'resposta': 'sim'}} ou {{'resposta': 'não'}}."""
    try:
        reviewed_message = llm.invoke(prompt)
        try:
            answer_json = json.loads(reviewed_message.content.replace("'", '"'))
            answer = answer_json.get('resposta', '').strip().lower()
        except Exception:
            answer = reviewed_message.content.strip().lower()
        if 'sim' in answer:
            return {"messages": ["O relatório foi bloqueado por conter conteúdo ofensivo ou dados sensíveis."]}
        else:
            return {"messages": [final_report]}
    except Exception as e:
        return {"messages": [f"Erro ao revisar o relatório final: {e}"]}