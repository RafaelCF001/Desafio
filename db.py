import duckdb
import pandas as pd
from langchain_core.tools import tool

DATA_PATH = "data\srag_limpo.parquet"

con = duckdb.connect(database=':memory:', read_only=False)


try:
    con.execute(f"CREATE TABLE srag AS SELECT * FROM read_parquet('{DATA_PATH}')")
    # Fazendo algumas conversões de tipo de dados para garantir que o SQL funcione bem
    con.execute("ALTER TABLE srag ALTER COLUMN DT_SIN_PRI TYPE DATE;")
    con.execute("ALTER TABLE srag ALTER COLUMN DT_EVOLUCA TYPE DATE;")
    con.execute("""CREATE OR REPLACE TABLE srag_diario AS
SELECT
  DT_SIN_PRI::DATE AS data,
  COUNT(*) AS total_casos,
  COUNT(CASE WHEN EVOLUCAO = 2 THEN 1 END) AS obitos,
  COUNT(CASE WHEN HOSPITAL = 1 THEN 1 END) AS hospitalizados,
  COUNT(CASE WHEN UTI = 1 THEN 1 END) AS uti,
  COUNT(CASE WHEN VACINA_COV = 1 THEN 1 END) AS vacinados
FROM srag
GROUP BY data;
""")
    con.execute("""CREATE OR REPLACE TABLE srag_movel AS
SELECT
  data,
  total_casos,
  AVG(total_casos) OVER (ORDER BY data ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS media_movel_7d
FROM srag_diario;
""")
    print("Banco de dados DuckDB inicializado com sucesso.")
except Exception as e:
    print(f"Erro ao inicializar o banco de dados DuckDB: {e}")
    con = None 


@tool
def execute_srag_query(query: str) -> str:
    """
    Executa uma consulta SQL no banco de dados de SRAG para obter métricas, contagens ou outros dados.
    Sempre use esta ferramenta para responder a qualquer pergunta que envolva números, taxas ou tendências dos dados.
    A tabela principal se chama 'srag'.
    Retorna os resultados da consulta como uma string formatada em Markdown.
    """
    if not con:
        return "Erro: A conexão com o banco de dados não foi inicializada."

    # verifica se a consulta é segura 
    query_lower = query.lower()
    print(query)
    if any(keyword in query_lower for keyword in ['drop', 'delete', 'update', 'insert', 'alter', 'create']):
        return "Erro de segurança: Apenas consultas SELECT são permitidas."

    try:
        result_df = con.execute(query).fetchdf()
        print(result_df)
        return result_df.to_markdown()
    except Exception as e:
        return f"Erro ao executar a consulta: {e}. Por favor, verifique a sintaxe da sua consulta SQL e os nomes das colunas."