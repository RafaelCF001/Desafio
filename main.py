import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from teste import app


def run_report():
    initial_prompt = (
        "Gere um relatório completo sobre o cenário atual da SRAG no Brasil. "
        "Você deve: "
        "1. Calcular as métricas chave (taxa de aumento de casos geral , taxa de mortalidade geral , taxa de ocupação de UTI considerando o periodo total ,e taxa de vacinação geral ). "
        "2. Buscar notícias recentes para contextualizar os dados. "
        "3. Gerar um gráfico de casos diários dos últimos 30 dias. "
        "4. Gerar um gráfico de casos mensais dos últimos 12 meses. "
        "5. Com base em TUDO isso, escreva uma análise técnica concisa sobre a situação."
    )

    inputs = {"messages": [HumanMessage(content=initial_prompt)]}
    final_state = app.invoke(inputs, {"recursion_limit": 100})
    final_response = final_state['messages'][-1]

    print("\n\n=============================================")
    print("--- RELATÓRIO FINAL GERADO PELO AGENTE ---")
    print("=============================================\n")
    print(final_response)

   
if __name__ == "__main__":
    load_dotenv()
    print(os.environ.get("OPENAI_API_KEY", "Chave"))
    run_report()