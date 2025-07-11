from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map

def daily_cases_plot_node(state: AgentState) -> Dict:
    
    print("--- GERANDO GRÁFICO DE CASOS DIÁRIOS ---")
    
    try:
        result = tool_map["generate_daily_cases_plot"].invoke({})
        print(result)
        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Gráfico de casos diários"] = result
        updated_results = dict(state.get("results", {}))
        updated_results["Gráfico de casos diários"] = result
        return {"executed_steps": updated_executed, "results": updated_results}
    except Exception as e:
        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Gráfico de casos diários"] = f"Erro ao gerar gráfico diário: {e}"
        updated_results = dict(state.get("results", {}))
        updated_results["Gráfico de casos diários"] = f"Erro ao gerar gráfico diário: {e}"
        return {"executed_steps": updated_executed, "results": updated_results}
