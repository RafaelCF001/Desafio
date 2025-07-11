
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from langchain_core.tools import tool

DATA_PATH = "data\srag_limpo.parquet" 

def _load_data() -> pd.DataFrame:
    try:
        df = pd.read_parquet(DATA_PATH)
        df['DT_SIN_PRI'] = pd.to_datetime(df['DT_SIN_PRI'], errors='coerce')
        df['DT_EVOLUCA'] = pd.to_datetime(df['DT_EVOLUCA'], errors='coerce') # Data do óbito/cura
        return df.dropna(subset=['DT_SIN_PRI'])
    except FileNotFoundError:
        raise ValueError(f"Arquivo de dados não encontrado em {DATA_PATH}. Verifique o caminho.")

@tool
def get_srag_key_metrics() -> dict:
    """
    Calcula as métricas chave de SRAG a partir do banco de dados.
    Use esta ferramenta para obter os números principais como taxa de aumento,
    mortalidade, ocupação de UTI e vacinação.
    Retorna: Um dicionário com as métricas calculadas.
    """
    df = _load_data()
    metricas = {}

    casos_diarios = df[df['DT_SIN_PRI'].notna()].groupby('DT_SIN_PRI').size()
    metricas["taxa_aumento_7d"] = casos_diarios.pct_change().fillna(0)[-7:].mean() * 100

    confirmados = df[df['CLASSI_FIN'].isin([1, 2, 5])]
    obitos = confirmados[confirmados['EVOLUCAO'] == 2]
    metricas["taxa_mortalidade"] = (len(obitos) / len(confirmados)) * 100

    internados = df[df['HOSPITAL'] == 1]
    uti = internados[internados['UTI'] == 1]
    metricas["taxa_uti"] = (len(uti) / len(internados)) * 100

    com_vac = df[df['VACINA_COV'].isin([1, 2])]
    vacinados = com_vac[com_vac['VACINA_COV'] == 1]
    metricas["taxa_vacinacao"] = (len(vacinados) / len(com_vac)) * 100

    return {"metricas": metricas}

@tool
def generate_daily_cases_plot() -> str:
    """
    Gera um gráfico de barras com o número de casos diários de SRAG nos últimos 30 dias.
    Esta ferramenta salva o gráfico como um arquivo PNG e retorna o caminho para o arquivo.
    """
    df = _load_data()
    end_date = df['DT_SIN_PRI'].max()
    start_date = end_date - pd.Timedelta(days=30)
    
    daily_cases = df[df['DT_SIN_PRI'] >= start_date].groupby('DT_SIN_PRI').size().sort_index()
    
    plt.figure(figsize=(14, 6))
    plt.bar(daily_cases.index, daily_cases.values, color='skyblue')

    plt.title('Casos Diários de SRAG (Últimos 30 Dias)')
    plt.xlabel('Data')
    plt.ylabel('Número de Casos')
    plt.grid(axis='y', linestyle='--')

    # Formatando o eixo X com datas mais legíveis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.xticks(rotation=45)

    plt.tight_layout()

    filename = "graficos/daily_cases.png"
    plt.savefig(filename)
    plt.close()
    return f"Gráfico de casos diários salvo em: {filename}"

@tool
def generate_monthly_cases_plot() -> str:
    """
    Gera um gráfico de barras com o número de casos mensais de SRAG nos últimos 12 meses.
    Esta ferramenta salva o gráfico como um arquivo PNG e retorna o caminho para o arquivo.
    """
    df = _load_data()
    df['mes_ano'] = df['DT_SIN_PRI'].dt.to_period('M')
    
    end_period = df['mes_ano'].max()
    start_period = end_period - 11
    
    monthly_cases = df[df['mes_ano'] >= start_period].groupby('mes_ano').size()
    monthly_cases.index = monthly_cases.index.to_timestamp()

    plt.figure(figsize=(12, 6))
    monthly_cases.plot(kind='line', marker='o', color='royalblue')
    plt.title('Casos Mensais de SRAG (Últimos 12 Meses)')
    plt.xlabel('Mês')
    plt.ylabel('Número de Casos')
    plt.grid(True, linestyle='--')
    plt.tight_layout()

    filename = "graficos\monthly_cases.png"
    plt.savefig(filename)
    plt.close()
    return f"Gráfico de casos mensais salvo em: {filename}"