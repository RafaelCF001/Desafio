from pydantic import BaseModel, Field
from typing import TypedDict, List, Dict
from langchain_core.messages import BaseMessage

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
