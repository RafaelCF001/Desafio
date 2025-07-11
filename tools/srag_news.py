from langchain_core.tools import tool
from dotenv import load_dotenv
import os 
from litellm import completion

@tool
def search_srag_news(query: str = "últimas notícias sobre Síndrome Respiratória Aguda Grave no Brasil"):
    """
    Busca notícias recentes na internet sobre SRAG, gripe, ou COVID-19 no Brasil
    para fornecer contexto atual ao relatório.
    Use esta ferramenta para entender os fatores externos que podem estar
    influenciando as métricas, como novas variantes ou campanhas de vacinação.
    """
   
    load_dotenv()
    tools = [{"googleSearch": {}}]
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY")
    response = completion(
        model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": query}],
    tools=tools,
    )

    return response.choices[0].message.content

