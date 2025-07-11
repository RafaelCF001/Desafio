from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map

def monthly_cases_plot_node(state: AgentState) -> Dict:
    
    print("--- 📉 GERANDO GRÁFICO DE CASOS MENSAIS ---")
    
    try:
        result = tool_map["generate_monthly_cases_plot"].invoke({})

        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Gráfico de casos mensais"] = result

        updated_results = dict(state.get("results", {}))
        updated_results["Gráfico de casos mensais"] = result

        return {"executed_steps": updated_executed, "results": updated_results}
    except Exception as e:
        updated_executed = dict(state.get("executed_steps", {}))
        updated_executed["Gráfico de casos mensais"] = f"Erro ao gerar gráfico mensal: {e}"

        updated_results = dict(state.get("results", {}))
        updated_results["Gráfico de casos mensais"] = f"Erro ao gerar gráfico mensal: {e}"

        return {"executed_steps": updated_executed, "results": updated_results}