
from models.models import AgentState
from typing import Dict
from utils.tool_map import tool_map
from langchain_openai import ChatOpenAI

def synthesizer_node(state: AgentState) -> Dict:
    """Nó Sintetizador: Gera o relatório final com base em todos os dados coletados."""
    print("---SINTETIZANDO O RELATÓRIO FINAL ---")
    user_request = state["messages"][0].content

    sql_llm = ChatOpenAI(model="gpt-4.1", temperature=0)

    max_steps = 10
    max_result_len = 10000

    # Preferencialmente use 'results', se existir, senão caia para executed_steps
    results_dict = state.get('results') or state.get('executed_steps', {})
    results_items = list(results_dict.items())[:max_steps]
    collected_data_str = "\n\n".join(
        f"### Pergunta Analítica: {task}\n\n**Resultado:**\n{str(result)[:max_result_len]}{'... [cortado]' if len(str(result)) > max_result_len else ''}"
        for task, result in results_items
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
