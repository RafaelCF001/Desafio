from pydantic import BaseModel, Field, ValidationError
import json
import operator
from typing import TypedDict, Annotated, List, Dict
import os 
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from tools.data_analysis import get_srag_key_metrics
from tools.data_analysis import generate_daily_cases_plot, generate_monthly_cases_plot
from tools.srag_news import search_srag_news
from langgraph.graph import StateGraph, END
from db import execute_srag_query
from dotenv import load_dotenv



load_dotenv()


class Step(BaseModel):
    passo: int
    tarefa: str = Field(description="Descrição clara da tarefa a ser executada.")
    ferramenta: str = Field(description="O nome exato da ferramenta a ser usada.")

class Plan(BaseModel):
    plano: list[Step]

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    plan: List[str]  
    current_query: str 
    executed_steps: Annotated[Dict[str, str], operator.ior] 




tool_map = {
    "execute_srag_query": execute_srag_query,
    "generate_daily_cases_plot": generate_daily_cases_plot,
    "generate_monthly_cases_plot": generate_monthly_cases_plot,
    "search_srag_news": search_srag_news,
}
def srag_news_node(state: AgentState) -> Dict:
    print("--- 📰 BUSCANDO NOTÍCIAS SOBRE SRAG ---")
    try:
        result = tool_map["search_srag_news"].invoke({})
        print(result)
        return {"executed_steps": {"Notícias SRAG": result}}
    except Exception as e:
        return {"executed_steps": {"Notícias SRAG": f"Erro ao buscar notícias: {e}"}}
llm = ChatOpenAI(model="gpt-4.1", temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
sql_llm = ChatOpenAI(model="gpt-4.1", temperature=0)


def planner_node(state: AgentState) -> Dict:
    print("--- 🧠 EXECUTANDO O PLANEJADOR ---")
    
    user_request = state["messages"][0].content
    
    schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'srag';"
    try:
        schema = tool_map["execute_srag_query"].invoke(schema_query)
        prompt = f"""Você é um analista de dados sênior. Sua tarefa é criar um plano de ação para responder a uma solicitação do usuário.\nA solicitação é: \"{user_request}\".\n\nVocê tem acesso a uma tabela 'srag' com o seguinte esquema:\n{schema}\n\nCrie um plano passo a passo para responder à solicitação. Cada passo deve ser um objeto JSON com as chaves: 'passo' (número do passo), 'tarefa' (descrição clara da tarefa) e 'ferramenta' (nome exato da ferramenta a ser usada).\nResponda APENAS com um objeto JSON contendo uma chave \"plano\" com uma lista desses objetos.\nExemplo: {{\"plano\": [{{\"passo\": 1, \"tarefa\": \"Calcular a taxa de mortalidade total por COVID (CLASSI_FIN = 5).\", \"ferramenta\": \"execute_srag_query\"}}]}}\n"""
        response = llm.invoke(prompt)
        print(response.content) 
        try:
            plan_data = json.loads(response.content)
            validated = Plan(**plan_data)
            return {"plan": [step.model_dump() for step in validated.plano]}
        except (ValidationError, Exception) as e:
            print(f"Erro de validação do plano: {e}")
            return {"plan": [], "error": f"Erro ao validar o plano: {e}"}
    except Exception as e:
        return {"plan": [], "error": f"Erro ao executar o planner_node: {e}"}


def sql_generator_node(state: AgentState) -> Dict:
    print("--- 💻 GERANDO QUERY SQL ---")

    # Identifica a próxima tarefa não executada
    for step in state["plan"]:
        if step["tarefa"] not in state.get("executed_steps", {}):
            next_step = step
            break

    if not next_step:
        return {"no_more_steps": True}

    try:
        schema_srag_diario = tool_map["execute_srag_query"].invoke("DESCRIBE srag_diario;")
        print(f"Esquema da tabela 'srag_diario': {schema_srag_diario}")
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
        return {"current_query": "", "error": f"Erro ao gerar SQL: {e}"}

def metrics_node(state: AgentState) -> Dict:
    print("--- 📊 GERANDO MÉTRICAS CHAVE DE SRAG ---")
    try:
        metrics = tool_map["get_srag_key_metrics"].invoke({})
        return {"executed_steps": {"Métricas chave de SRAG": str(metrics)}}
    except Exception as e:
        return {"executed_steps": {"Métricas chave de SRAG": f"Erro ao obter métricas: {e}"}}



def sql_executor_node(state: AgentState) -> Dict:
    print("--- 🚀 EXECUTANDO QUERY SQL ---")
    
    query = state["current_query"]
    print(query)
    try:
        result = tool_map["execute_srag_query"].invoke(query)
        print(f"Resultado obtido: {result[:200]}...") 
        executed_step = None
        for step in state["plan"]:
            if step["tarefa"] not in state.get("executed_steps", {}):
                executed_step = step["tarefa"]
                break
        return {"executed_steps": {executed_step: result}}
    except Exception as e:
        executed_step = None
        for step in state["plan"]:
            if step["tarefa"] not in state.get("executed_steps", {}):
                executed_step = step["tarefa"]
                break
        return {"executed_steps": {executed_step: f"Erro ao executar a query: {e}"}}

def daily_cases_plot_node(state: AgentState) -> Dict:
    print("--- 📈 GERANDO GRÁFICO DE CASOS DIÁRIOS ---")
    try:
        result = tool_map["generate_daily_cases_plot"].invoke({})
        print(result)
        return {"executed_steps": {"Gráfico de casos diários": result}}
    except Exception as e:
        return {"executed_steps": {"Gráfico de casos diários": f"Erro ao gerar gráfico diário: {e}"}}

def monthly_cases_plot_node(state: AgentState) -> Dict:
    print("--- 📉 GERANDO GRÁFICO DE CASOS MENSAIS ---")
    try:
        result = tool_map["generate_monthly_cases_plot"].invoke({})
        print(result)
        return {"executed_steps": {"Gráfico de casos mensais": result}}
    except Exception as e:
        return {"executed_steps": {"Gráfico de casos mensais": f"Erro ao gerar gráfico mensal: {e}"}}


def synthesizer_node(state: AgentState) -> Dict:
    """Nó Sintetizador: Gera o relatório final com base em todos os dados coletados."""
    print("--- ✍️  SINTETIZANDO O RELATÓRIO FINAL ---")
    user_request = state["messages"][0].content
    print(f"Solicitação original: {user_request}")
    print(f"Executed steps: {list(state['executed_steps'].keys())}")

    max_steps = 10
    max_result_len = 1000
    executed_items = list(state['executed_steps'].items())[:max_steps]
    collected_data_str = "\n\n".join(
        f"### Pergunta Analítica: {task}\n\n**Resultado:**\n{str(result)[:max_result_len]}{'... [cortado]' if len(str(result)) > max_result_len else ''}"
        for task, result in executed_items
    )
    print(f"Dados coletados para síntese (limitados):\n{collected_data_str}")
    prompt = f"""Você é um especialista em epidemiologia. Sua tarefa é escrever um relatório técnico claro respondendo à solicitação original do usuário.\nSolicitação: "{user_request}"\n\nA seguir estão os dados coletados do banco de dados em resposta a uma série de perguntas analíticas (limitados a 10 perguntas e 1000 caracteres por resultado):\n---\n{collected_data_str}\n---\nCom base exclusivamente nos dados fornecidos, escreva um relatório coeso e bem estruturado em formato markdown.\nSe citar algum gráfico, referencie o arquivo como /graficos/nome_do_grafico.png.\nInterprete os resultados, identifique padrões e forneça uma conclusão clara.\n os gráficos est]ao disponiveis em /graficos/daily_cases.png e /graficos/monthly_cases.png.
    A resposta deve estar obrigatoriamente em markdown válido, com títulos, listas e imagens se necessário"""
    print("Enviando prompt para o modelo...")
    response = sql_llm.invoke(prompt)
    print("Resposta recebida do modelo.")


    if hasattr(response, "content"):
        content = response.content
    else:
        content = str(response)
    print(f"Relatório final (primeiros 500 chars):\n{content[:500]}{'...' if len(content) > 500 else ''}")
    
    with open("relatorio_final.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("Relatório salvo em relatorio_final.md")
    return {"messages": [content]}

def final_review_node(state: AgentState) -> Dict:
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


workflow = StateGraph(AgentState)




workflow.add_node("planner", planner_node)
workflow.add_node("sql_generator", sql_generator_node)
workflow.add_node("sql_executor", sql_executor_node)
workflow.add_node("srag_news", srag_news_node)
workflow.add_node("daily_cases_plot", daily_cases_plot_node)
workflow.add_node("monthly_cases_plot", monthly_cases_plot_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("final_review", final_review_node)

workflow.set_entry_point("planner")



workflow.add_edge("planner", "sql_generator")
workflow.add_edge("sql_generator", "sql_executor")

def sql_router(state: AgentState) -> str:
    plan = state.get("plan", [])
    executed = state.get("executed_steps", {})
    next_sql = None
    for step in plan:
        if step["tarefa"] not in executed and step.get("ferramenta", "") == "execute_srag_query":
            next_sql = step
            break
    if next_sql:
        return "sql_generator"
    return "srag_news"

workflow.add_conditional_edges(
    "sql_executor",
    sql_router,
    {
        "sql_generator": "sql_generator",
        "srag_news": "srag_news"
    }
)
workflow.add_edge("srag_news", "daily_cases_plot")
workflow.add_edge("daily_cases_plot", "monthly_cases_plot")
workflow.add_edge("monthly_cases_plot", "synthesizer")
workflow.add_edge("synthesizer", "final_review")
workflow.add_edge("final_review", END)

# Lógica de roteamento: após executar uma query, ou gera a próxima ou sintetiza o resultado final.
def router(state: AgentState) -> str:
    # Se não há plano ou plano vazio, encerra
    plan = state.get("plan", [])
    executed = state.get("executed_steps", {})
    # Se houve erro no plano, encerra
    if not plan or (isinstance(plan, list) and len(plan) == 0):
        return "synthesizer"
    # Se todos os passos foram executados, encerra
    if len(executed) >= len(plan):
        return "synthesizer"
    # Se o sql_generator_node sinalizou que não há mais passos, encerra
    if state.get("no_more_steps"):
        return "synthesizer"
    # Se não há próximo passo executável, encerra
    next_step = None
    for step in plan:
        if step not in executed:
            next_step = step
            break
    if next_step is None:
        return "synthesizer"
    # Caso contrário, segue normalmente
    return "sql_generator"

# O roteador não é mais necessário pois o fluxo é linear

app = workflow.compile()