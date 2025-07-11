from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map
from langchain_openai import ChatOpenAI

def sql_generator_node(state: AgentState) -> Dict:
    print("--- 💻 GERANDO QUERY SQL ---")
    print(f"[sql_generator_node] executed_steps: {state.get('executed_steps', {})}")
    sql_llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    # Identifica a próxima tarefa não executada
    next_step = None
    for step in state["plan"]:
        if step["tarefa"] not in state.get("executed_steps", {}):
            next_step = step
            break

    print(f"[sql_generator_node] Próximo step: {next_step}")

    if not next_step:
        print("[sql_generator_node] Não há mais steps a executar.")
        return {"no_more_steps": True}

    try:
        schema_srag_diario = tool_map["execute_srag_query"].invoke("DESCRIBE srag_diario;")
        prompt = f"""Você é um especialista em SQL que escreve queries para DuckDB.
Dada a tarefa analítica a seguir, escreva a consulta SQL correspondente.
Lembre-se que as datas (ex: DT_SIN_PRI) estão no formato DATE.

Tarefa: "{next_step['tarefa']}"

Esquema da tabela 'srag_diario'
{schema_srag_diario}

Uso: Base intermediária para todas as métricas temporais.

Exemplos de tarefas:

Passo 1: Calcular média móvel e taxa de aumento de casos.

Passo 2: Taxa de mortalidade diária.

Passo 3: Taxa de ocupação de UTI.

Passo 4: Taxa de vacinação.



Responda APENAS com o código SQL. Não adicione explicações ou formatação. sem ´´´´ ou outros caracteres especiais.
"""
        response = sql_llm.invoke(prompt)
        return {"current_query": response.content}
    except Exception as e:
        print(f"[sql_generator_node] Erro ao gerar SQL: {e}")
        return {"current_query": "", "error": f"Erro ao gerar SQL: {e}"}