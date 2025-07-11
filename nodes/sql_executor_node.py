from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map

def sql_executor_node(state: AgentState) -> Dict:
    
    print("--- 🚀 EXECUTANDO QUERY SQL ---")
    print(f"[sql_executor_node] executed_steps antes: {state.get('executed_steps', {})}")
    
    query = state["current_query"]
    executed_step = None
    
    for step in state["plan"]:
        if step["tarefa"] not in state.get("executed_steps", {}):
            executed_step = step["tarefa"]
            break
    
    print(f"[sql_executor_node] Step a marcar como executado: {executed_step}")
    
    try:
        result = tool_map["execute_srag_query"].invoke(query)
        print(f"Resultado obtido: {result[:200]}...") 

        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed[executed_step] = result

        updated_results = dict(state.get("results", {}))
        updated_results[executed_step] = result

        return {"executed_steps": updated_executed, "results": updated_results}
    except Exception as e:
        print(f"[sql_executor_node] Erro ao executar query: {e}")

        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed[executed_step] = f"Erro ao executar a query: {e}"

        updated_results = dict(state.get("results", {}))
        updated_results[executed_step] = f"Erro ao executar a query: {e}"

        return {"executed_steps": updated_executed, "results": updated_results}

