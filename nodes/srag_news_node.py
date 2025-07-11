from utils.tool_map import tool_map
from langchain_openai import ChatOpenAI
from typing import Dict
from models.models import AgentState

def srag_news_node(state: AgentState) -> Dict:
    print("--- 📰 BUSCANDO NOTÍCIAS SOBRE SRAG ---")
    try:
        result = tool_map["search_srag_news"].invoke({})
        print(result)
        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Notícias SRAG"] = result
        updated_results = dict(state.get("results", {}))
        updated_results["Notícias SRAG"] = result
        return {"executed_steps": updated_executed, "results": updated_results}
    except Exception as e:
        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Notícias SRAG"] = f"Erro ao buscar notícias: {e}"
        updated_results = dict(state.get("results", {}))
        updated_results["Notícias SRAG"] = f"Erro ao buscar notícias: {e}"
        return {"executed_steps": updated_executed, "results": updated_results}
llm = ChatOpenAI(model="gpt-4.1", temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
sql_llm = ChatOpenAI(model="gpt-4.1", temperature=0)