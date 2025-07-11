from tools.data_analysis import generate_daily_cases_plot, generate_monthly_cases_plot
from tools.srag_news import search_srag_news
from db import execute_srag_query

tool_map = {
    "execute_srag_query": execute_srag_query,
    "generate_daily_cases_plot": generate_daily_cases_plot,
    "generate_monthly_cases_plot": generate_monthly_cases_plot,
    "search_srag_news": search_srag_news,
}