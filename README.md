# Desafio: Geração Automatizada de Relatórios com IA Generativa

## Descrição Geral

Este repositório apresenta uma solução baseada em Inteligência Artificial Generativa capaz de consultar dados epidemiológicos e notícias, sintetizando relatórios automatizados com métricas relevantes e explicações detalhadas sobre o cenário analisado. O sistema utiliza LLMs (Large Language Models) integrados a ferramentas de consulta de dados e geração de gráficos, promovendo transparência, governança e auditabilidade em cada etapa do processo.

## Objetivo

Automatizar a análise de dados e a geração de relatórios técnicos, respondendo a perguntas analíticas sobre o cenário de SRAG (Síndrome Respiratória Aguda Grave) a partir de dados estruturados e notícias recentes, utilizando agentes inteligentes, LangChain, LangGraph e ferramentas customizadas.

## Arquitetura

- **LangGraph**: Orquestra o fluxo de execução entre os agentes (nós), cada um responsável por uma etapa do pipeline (planejamento, geração de queries, execução, síntese, etc).
- **LangChain**: Utilizado para integração com LLMs e ferramentas customizadas.
- **Agentes/Nós**: Cada nó executa uma função específica, como planejamento, geração de SQL, execução de queries, busca de notícias, geração de gráficos e síntese do relatório final.
- **Tools**: Funções customizadas para consulta ao banco de dados, geração de gráficos e busca de notícias.
- **Banco de Dados**: Utiliza DuckDB para consultas rápidas sobre dados epidemiológicos em formato Parquet.
- **Governança e Transparência**: Todas as decisões dos agentes, queries executadas e resultados intermediários são registrados no estado global, permitindo auditoria completa do processo.
- **Guardrails**: O sistema implementa validações de segurança para evitar queries perigosas e tratamento de erros em todas as etapas.

## Como Funciona

1. **Planejamento**: O agente planner interpreta a solicitação do usuário e gera um plano de ação detalhado, dividido em etapas (steps), cada uma com a ferramenta apropriada.
2. **Geração de SQL**: O agente sql_generator cria queries SQL para responder às perguntas analíticas do plano.
3. **Execução de SQL**: O agente sql_executor executa as queries no banco de dados DuckDB e armazena os resultados.
4. **Busca de Notícias**: O agente srag_news_node busca notícias relevantes sobre SRAG.
5. **Geração de Gráficos**: Os agentes daily_cases_plot_node e monthly_cases_plot_node geram gráficos de casos diários e mensais.
6. **Síntese**: O agente synthesizer_node compila todos os resultados e gera um relatório técnico em Markdown, interpretando os dados e referenciando os gráficos gerados.
7. **Revisão Final**: O relatório é revisado automaticamente para garantir ausência de conteúdo sensível ou inadequado.


## Detalhamento do Tratamento de Dados

O dataset original apresenta alta incidência de valores ausentes e inconsistências. O pré-processamento realizado consiste em:
- Remoção de registros com valores nulos nas colunas essenciais para as análises (ex: datas, desfecho, hospitalização, UTI, vacinação).
- Seleção apenas das colunas estritamente necessárias para o cálculo das métricas e geração dos gráficos, reduzindo ruído e complexidade.
- Conversão e padronização de tipos de dados (ex: datas para formato DATE).
- Não foi realizada imputação de valores devido à natureza dos dados e ao risco de enviesamento; registros incompletos são descartados.
- Não foram criadas flags de confiança, mas a abordagem pode ser estendida para tal.

## Justificativa das Escolhas Técnicas

- **DuckDB**: Escolhido por ser um banco de dados analítico em memória, open-source, com performance superior para workloads analíticos e integração nativa com arquivos Parquet. Permite consultas SQL eficientes sem a complexidade de um SGBD tradicional.
- **Parquet**: Formato colunar eficiente para leitura seletiva e compressão, reduzindo o tempo de I/O e uso de memória.
- **LangGraph/LangChain**: Permitem orquestração modular de agentes, integração transparente com LLMs e ferramentas customizadas, além de facilitar logging e governança.
- **googlesearch + Gemini**: Devido a limitações de APIs públicas para busca de notícias, optou-se por um agente Gemini que utiliza googlesearch, eliminando a necessidade de infraestrutura de banco vetorial e vetorização de textos para RAG.

## Busca de Notícias e RAG

O agente de busca de notícias utiliza scraping via googlesearch integrado a um LLM (Gemini) para sumarização e filtragem dos resultados. Não é utilizado banco vetorial ou embeddings para recall semântico, pois a abordagem prioriza simplicidade e robustez frente às limitações de APIs públicas. Todo o contexto externo é incorporado via scraping e análise textual direta pelo LLM.

## Observações sobre Diagrama Conceitual

O diagrama conceitual do fluxo de agentes, estados e ferramentas deve ser consultado no PDF anexo ao repositório. Ele detalha as transições entre nós, contratos de entrada/saída e pontos de logging/auditoria, sendo fundamental para compreensão e avaliação do sistema.

1. **Pré-requisitos**:
   - Python 3.10+
   - Instalar dependências: `pip install -r requirements.txt`
   - Arquivo de dados Parquet em `data/srag_limpo.parquet`
   - Configurar variáveis de ambiente (ex: chave da OpenAI) em `.env`

2. **Execução**:
   - Execute o arquivo principal (`main.py` ou `teste.py`) para iniciar o fluxo.
   - O sistema irá processar a solicitação do usuário, consultar os dados, gerar gráficos e produzir o relatório final em `relatorio_final.md`.

## Estrutura dos Principais Arquivos

- `main.py` / `teste.py`: Inicialização do fluxo e definição do grafo de agentes.
- `nodes/`: Implementação dos agentes (nós) do fluxo.
- `tools/`: Ferramentas customizadas para análise de dados, geração de gráficos e busca de notícias.
- `models/`: Definição dos modelos de dados e estado global.
- `data/`: Dados de entrada em formato Parquet.
- `graficos/`: Gráficos gerados automaticamente.


## Governança, Transparência e Auditoria

- Toda a orquestração e rastreabilidade do pipeline é realizada via LangSmith, que registra logs detalhados de cada agente, suas decisões, entradas e saídas, permitindo auditoria completa do fluxo.
- O estado global (`AgentState`) mantém o histórico de decisões, queries executadas e resultados intermediários, promovendo transparência e rastreabilidade.


## Guardrails e Tratamento de Dados Sensíveis

- Todas as queries SQL são validadas para impedir execução de comandos DDL/DML destrutivos (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE), restringindo o sistema a operações de leitura (SELECT).
- O relatório final é submetido a uma etapa de avaliação automática por LLM (AI as a Judge), que verifica a presença de conteúdo sensível, inadequado ou vazamento de dados, bloqueando a publicação caso qualquer violação seja detectada.
- Todos os erros e exceções são capturados e registrados, garantindo robustez e rastreabilidade para auditoria posterior.
