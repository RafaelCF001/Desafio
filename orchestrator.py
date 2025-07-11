
from nodes.daily_cases_plot_node import daily_cases_plot_node
from nodes.monthly_cases_plot_node import monthly_cases_plot_node
from nodes.planner_node import planner_node
from nodes.srag_news_node import srag_news_node
from nodes.sql_executor_node import sql_executor_node
from nodes.sql_generator_node import sql_generator_node
from nodes.synthesizer_node import synthesizer_node
from nodes.final_review_node import final_review_node


from pydantic import BaseModel, Field
from typing import TypedDict, List, Dict
from langchain_core.messages import BaseMessage

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

class Step(BaseModel):
    passo: int
    tarefa: str = Field(description="Descrição clara da tarefa a ser executada.")
    ferramenta: str = Field(description="O nome exato da ferramenta a ser usada.")

class Plan(BaseModel):
    plano: List[Step]

class AgentState(TypedDict):
    messages: List[BaseMessage]
    plan: List[Dict]
    current_query: str
    executed_steps: Dict[str, str]
    results: Dict[str, str]

load_dotenv()


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

def router(state: AgentState) -> str:
    plan = state.get("plan", [])
    executed = state.get("executed_steps", {})
    if not plan or (isinstance(plan, list) and len(plan) == 0):
        return "synthesizer"
    if len(executed) >= len(plan):
        return "synthesizer"
    if state.get("no_more_steps"):
        return "synthesizer"
    next_step = None
    for step in plan:
        if step not in executed:
            next_step = step
            break
    if next_step is None:
        return "synthesizer"
    return "sql_generator"


app = workflow.compile()