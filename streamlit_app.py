import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import plotly.io as pio
from datetime import datetime
from millify import prettify
import io

# Configurar o locale para português brasileiro
pio.templates.default = "plotly"
pio.templates["plotly"]["layout"]["font"]["family"] = "Arial, sans-serif"

# Configuração específica para números no formato brasileiro
config_locale = {
    "locale": "pt-BR",
    "separators": ",.",  # vírgula para decimal, ponto para milhar
    "currency": ["R$", ""]
}
# Aplicar configuração
pio.templates["plotly"]["layout"]["separators"] = config_locale["separators"]

MESES_PT = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

MESES_ABREV_PT = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
            5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}


# Função para gerar dicionário de cores por ano
def gerar_cores_por_ano(anos):
    """
    Atribui uma cor consistente para cada ano usando uma paleta qualitativa
    """
    paleta = px.colors.qualitative.Set1
    return {ano: paleta[i % len(paleta)] for i, ano in enumerate(sorted(anos))}

# Configuração da página
st.set_page_config(page_title='Dashboard de Análise de Faturas', page_icon='📊', layout='wide')

if 'dados_carregados' not in st.session_state:
    st.session_state.dados_carregados = False

# Função para carregar e processar dados
@st.cache_data
def processar_dados(file, tipo_conta):
    try:
        # Determinar o tipo de arquivo e carregá-lo
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            st.error("Formato de arquivo não suportado. Por favor, use CSV ou Excel.")
            return None
        
        # Verificar colunas necessárias
        colunas_necessarias = ['mes', 'ano', 'valor', 'consumo']
        colunas_presentes = [col for col in colunas_necessarias if col in df.columns]
        
        if len(colunas_presentes) < len(colunas_necessarias):
            # Tentar mapear colunas se os nomes forem diferentes
            mapeamento = {
                'mes': ['mes', 'mês', 'month', 'mes_ref'],
                'ano': ['ano', 'year', 'exercicio'],
                'valor': ['valor', 'valor_mensal', 'value', 'custo'],
                'consumo': ['consumo', 'consumo_mensal', 'consumption', 'gasto']
            }
            
            for col_necessaria, alternativas in mapeamento.items():
                if col_necessaria not in df.columns:
                    for alt in alternativas:
                        if alt in df.columns:
                            df.rename(columns={alt: col_necessaria}, inplace=True)
                            break
        
        # Verificar novamente após o mapeamento
        colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
        if colunas_faltantes:
            st.error(f"Colunas obrigatórias ausentes: {', '.join(colunas_faltantes)}")
            return None
        
        # Garantir que mês e ano sejam numéricos
        df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
        
        # Remover linhas com valores inválidos
        df = df.dropna(subset=['mes', 'ano', 'valor', 'consumo'])
        
        # Criar coluna de data para ordenação
        df['data'] = pd.to_datetime(df['ano'].astype(int).astype(str) + '-' + 
                                   df['mes'].astype(int).astype(str).str.zfill(2) + '-01')
        
        # Adicionar nome do mês para exibição
        df['nome_mes'] = df['mes'].apply(lambda x: MESES_PT[int(x)])
        
        # Adicionar coluna de mês/ano para exibição
        df['mes_ano'] = df['data'].dt.month.apply(lambda m: MESES_ABREV_PT[m]) + '/' + df['data'].dt.year.astype(str)
        
        # Ordenar por data
        df = df.sort_values('data')
        
        # Definir unidade de medida com base no tipo de conta
        if tipo_conta == 'Conta de água(CAESB)':
            df['unidade'] = 'm³'
            df['tipo_medicao'] = 'água'
        else:
            df['unidade'] = 'KWh'
            df['tipo_medicao'] = 'energia'
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None

# Função para gerar dados de exemplo
@st.cache_data
def gerar_dados_exemplo(tipo_conta):
    # Determinar unidade e tipo de medição
    if tipo_conta == 'Conta de água(CAESB)':
        unidade = 'm³'
        tipo_medicao = 'água'
        min_consumo, max_consumo = 10, 50
        min_valor, max_valor = 50, 300
    else:
        unidade = 'KWh'
        tipo_medicao = 'energia'
        min_consumo, max_consumo = 150, 550
        min_valor, max_valor = 100, 500
    
    # Gerar dados aleatórios para 2-3 anos
    anos = sorted(np.random.choice(range(2020, 2024), size=np.random.randint(2, 4), replace=False))
    
    dados = []
    for ano in anos:
        for mes in range(1, 13):
            # Simular sazonalidade
            fator_sazonal = 1 + 0.3 * np.sin((mes - 1) * np.pi / 6)
            
            # Gerar consumo com tendência crescente leve e sazonalidade
            base_consumo = np.random.randint(min_consumo, max_consumo)
            consumo = int(base_consumo * fator_sazonal * (1 + 0.05 * (ano - anos[0])))
            
            # Valor com alguma correlação ao consumo, mas não perfeita
            valor = round(consumo * np.random.uniform(1.5, 2.5) + np.random.randint(-20, 20), 2)
            
            dados.append([mes, ano, valor, consumo, unidade, tipo_medicao])
    
    # Criar DataFrame
    df = pd.DataFrame(dados, columns=['mes', 'ano', 'valor', 'consumo', 'unidade', 'tipo_medicao'])
    
    # Adicionar colunas de data e nome do mês
    df['data'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2) + '-01')
    df['nome_mes'] = df['mes'].apply(lambda x: MESES_PT[int(x)])
    df['mes_ano'] = df['data'].dt.month.apply(lambda m: MESES_ABREV_PT[m]) + '/' + df['data'].dt.year.astype(str)
    
    # Ordenar por data
    df = df.sort_values('data')
    
    return df

# Função para criar gráfico de linha do tempo
def criar_grafico_timeline(df, y_column, title, y_label, cores_por_ano):
    fig = px.line(
        df, 
        x='data', 
        y=y_column,
        color='ano',
        title=title,
        labels={y_column: y_label, 'data': 'Data', 'ano': 'Ano'},
        markers=True,
        color_discrete_map=cores_por_ano 
    )
    fig.update_traces(
    hovertemplate='<b>Data:</b> %{x}<br><b>' + y_label + ':</b> %{y:,.2f}<extra></extra>'
    )
    fig.update_layout(
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date", 
            tickmode="array",
            tickvals=df['data'].tolist(), # Usar as datas exatas como valores
            ticktext=df['mes_ano'].tolist(), # Usar os textos 'mes_ano' formatados em portugues
            tickangle=45,
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1a", step="year", stepmode="backward"),
                    dict(step="all", label="Tudo")
                ])
            )
        )
    )
    
    return fig

# Função para criar gráfico de barras
def criar_grafico_barras(df, y_column, title, y_label, cores_por_ano):
    # Converter ano para string para compatibilidade com o color_discrete_map
    df = df.copy()
    df['ano_str']=df['ano'].astype(str)

    # Criar mapa de cores com chaves em string
    cores_str = {str(ano):cor for ano,cor in cores_por_ano.items()}

    fig = px.bar(
        df,  
        x='mes_ano', 
        y=y_column,
        color='ano_str', # Usar versão string do ano
        title=title,
        labels={y_column: y_label, 'mes_ano': 'Mês/Ano', 'ano_str': 'Ano'},
        text_auto=False,
        color_discrete_map=cores_str # Usar o mapa de cores por ano
    )
    if 'valor' in y_column:
        fig.update_traces(
            texttemplate='%{y:,.2f}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' + y_label + ':%{y:,.2f}<extra></extra>'
        )
    else:
        fig.update_traces(
        texttemplate='%{y}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' + y_label + ': %{y}<extra></extra>'
        )
    if 'valor' in y_column:
        fig.update_layout(
            yaxis=dict(
                tickprefix='R$ ',
                tickformat=',.2f',
            )
        )

    fig.update_layout(
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

# Função para criar gráfico comparativo
def criar_grafico_comparativo(df, anos_selecionados, y_column, title, y_label, cores_por_ano):
    df_filtrado = df[df['ano'].isin(anos_selecionados)].copy()
    
    fig = go.Figure()
    
    for ano in sorted(anos_selecionados):
        df_ano = df_filtrado[df_filtrado['ano'] == ano]
        
        # Ordenar por mês
        df_ano = df_ano.sort_values('mes')
        
        fig.add_trace(go.Scatter(
            x=df_ano['mes'],
            y=df_ano[y_column],
            mode='lines+markers',
            name=f"Ano {ano}",
            line=dict(width=3, color=cores_por_ano[ano]),
            marker=dict(size=8, color=cores_por_ano[ano]),
            hovertemplate='<b>Data:</b> %{x}<br><b>' + y_label + ':</b> %{y:,.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=[MESES_PT[i] for i in range(1, 13)],
            title='Mês'
        ),
        yaxis_title=y_label,
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x'
    )

    return fig

# Função para formatar valores monetários
def formatar_valor(valor):
    return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Interface principal
def main():
    st.title("📊 Análise de Gastos - MIDR")
    
    # Criação das abas
    tab1, tab2, tab3, tab4 = st.tabs(['📋 Introdução', '📊 Visão Geral', '🔍 Análise por Período', '🔄 Comparações'])
    
    # Aba 1: Introdução
    with tab1:
        st.header("Bem vindo ao Sistema de Análise de Faturas!")
        
        st.markdown("""
        Este aplicativo permite analisar e visualizar seus dados de faturas de água ou energia, 
        ajudando você a entender melhor seus padrões de consumo e gastos ao longo do tempo.
        
        ### Como usar:
        1. Selecione o tipo de fatura(água ou energia) com o botão abaixo;
        2. Faça upload do seu arquivo de dados, ou use dados de exemplo para testar o sistema;
        3. Navegue pelas abas acima para visualizar diferentes análises;
        4. Dúvidas sobre como manejar os gráficos? Cada página possui uma nota de rodapé detalhando seu funcionamento!             
        """)
        
        # Seleção do tipo de conta
        select_conta = st.selectbox(
            "Qual tipo de fatura será analisada?",
            ('Conta de água(CAESB)', 'Conta de energia(CEB/Neoenergia)'),
            index=None,
            placeholder="Selecione o tipo de conta...",
        )
        
        if select_conta is None:
            st.info('👆 Escolha um tipo de conta para prosseguir.')
            st.stop()
        
        st.write(f'Você está analisando: {select_conta}')
        
        # Opções para carregar dados
        col1, col2 = st.columns(2)
        
        with col1:
            exemplo_ativado = st.button("📊 Carregar dados de exemplo")
        
        with col2:
            uploaded_file = st.file_uploader("📁 Carregar arquivo (CSV ou Excel)", type=['csv', 'xlsx', 'xls'])
        
        st.markdown("""
        ### Estrutura esperada do arquivo:
        - **Coluna 'mes'**: número correspondente ao mês (1-12)
        - **Coluna 'ano'**: ano de referência 
        - **Coluna 'valor'**: valor total da fatura a ser paga (é importante que o numero contenha apenas um ponto separador de valores decimais)
        - **Coluna 'consumo'**: valor do consumo faturado
        """)
        
        # Processamento dos dados
        if 'dados_carregados' not in st.session_state:
            st.session_state.dados_carregados = False

        if exemplo_ativado:
            df = gerar_dados_exemplo(select_conta)
            st.session_state.df = df
            st.session_state.tipo_conta = select_conta
            st.session_state.dados_carregados = True
            st.session_state.fonte_dados = "exemplo"
            st.success("✅ Dados de exemplo carregados com sucesso!")
        elif uploaded_file is not None:
            df = processar_dados(uploaded_file, select_conta)
            if df is not None:
                st.session_state.df = df
                st.session_state.tipo_conta = select_conta
                st.session_state.dados_carregados = True
                st.session_state.fonte_dados = "arquivo"
                st.success(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")
            else:
                st.error("❌ Erro ao processar o arquivo.")
                st.stop()
        elif st.session_state.dados_carregados:
            # Recuperar dados da sessão
            df = st.session_state.df
            select_conta = st.session_state.tipo_conta
            st.success(f"✅ Usando dados {'de exemplo' if st.session_state.fonte_dados == 'exemplo' else 'do arquivo'} carregados anteriormente.")

        else:
            st.info('👆 Carregue um arquivo ou use dados de exemplo para começar a análise.')
            st.stop()
        
        # Armazenar dados na sessão
        if df is not None:
            # Exibir amostra dos dados
            with st.expander("Visualizar dados carregados (tabela bruta)"):
                st.dataframe(df[['nome_mes', 'ano', 'valor', 'consumo']])
        else:
            st.stop()
    
    # Verificar se os dados foram carregados
    if 'df' not in st.session_state:
        return
    
    df = st.session_state['df']
    tipo_conta = st.session_state['tipo_conta']
    
    # Extrair metadados
    unidade = df['unidade'].iloc[0]
    tipo_medicao = df['tipo_medicao'].iloc[0]
    anos = sorted(df['ano'].unique())
    cores_por_ano = gerar_cores_por_ano(anos)
    
    # Aba 2: Visão Geral
    with tab2:
        # Confirmação de que os dados estão carregados corretamente
        if 'dados_carregados' not in st.session_state or not st.session_state.dados_carregados:
            st.warning("⚠️ Nenhum dado carregado. Por favor, volte à aba 'Introdução' para carregar dados.")
            st.stop()
        df = st.session_state.df
        tipo_conta = st.session_state.tipo_conta
        
        st.header("Visão Geral dos Dados")
        
        # Estatísticas gerais
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de registros", len(df))
            st.metric("Período analisado", f"{df['mes_ano'].iloc[0]} a {df['mes_ano'].iloc[-1]}")
            st.metric(f"Total consumido ({unidade})", f"{formatar_valor(df['consumo'].sum())}")
        
        with col2:
            st.metric("Valor total (R$)", formatar_valor(df['valor'].sum()))
            st.metric(f"Consumo médio mensal ({unidade})", f"{formatar_valor(df['consumo'].mean())}")
            st.metric("Valor médio mensal (R$)", formatar_valor(df['valor'].mean()))
        
        # Slider para selecionar intervalo de datas
        min_date = df['data'].min().date()
        max_date = df['data'].max().date()
        
        st.subheader("Filtrar período na linha do tempo")
        date_range = st.slider(
            "Selecione o período a visualizar:",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="MM/YYYY"
        )
        
        # Filtrar dados pelo intervalo selecionado
        filtered_df = df[(df['data'].dt.date >= date_range[0]) & (df['data'].dt.date <= date_range[1])]
        
        if not filtered_df.empty:
            # Gráficos de linha do tempo
            st.subheader(f"Evolução do Consumo de {tipo_medicao.capitalize()} ao Longo do Tempo")
            consumo_fig = criar_grafico_timeline(
                filtered_df, 
                'consumo', 
                f"Consumo de {tipo_medicao.capitalize()} ({unidade})", 
                f"Consumo ({unidade})",
                cores_por_ano
            )
            st.plotly_chart(consumo_fig, use_container_width=True)
            st.caption("Use o controle deslizante abaixo do gráfico para zoom ou os botões para selecionar períodos específicos.")

            st.subheader("Evolução do Valor das Faturas ao Longo do Tempo")
            valor_fig = criar_grafico_timeline(
                filtered_df, 
                'valor', 
                "Valor das Faturas (R$)", 
                "Valor (R$)",
                cores_por_ano
            )
            st.plotly_chart(valor_fig, use_container_width=True)
            st.caption("Use o controle deslizante abaixo do gráfico para zoom ou os botões para selecionar períodos específicos.")
            st.markdown("""
            #### Recursos interativos:

            - **Passe o mouse** sobre qualquer ponto para ver detalhes da fatura específica
            - **Clique e arraste** para ampliar uma área específica do gráfico
            - **Clique duplo** para restaurar a visualização original
            - **Clique na legenda** para mostrar/ocultar anos específicos

            """)
        else:
            st.warning("Nenhum dado encontrado para o período selecionado.")
    
    # Aba 3: Análise por Período
    with tab3:
        # Confirmação de que os dados estão carregados corretamente
        if 'dados_carregados' not in st.session_state or not st.session_state.dados_carregados:
            st.warning("⚠️ Nenhum dado carregado. Por favor, volte à aba 'Introdução' para carregar dados.")
            st.stop()
        df = st.session_state.df
        tipo_conta = st.session_state.tipo_conta
        
        st.header("Análise por Período Específico")
        
        # Seletores de período
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Período Inicial")
            ano_inicial = st.selectbox("Ano inicial", anos, index=0, key="ano_inicial")
            
            meses_disponiveis_inicial = sorted(df[df['ano'] == ano_inicial]['mes'].unique())
            mes_inicial = st.selectbox(
                "Mês inicial", 
                meses_disponiveis_inicial,
                format_func=lambda x: MESES_PT[int(x)],
                index=0,
                key="mes_inicial"
            )
        
        with col2:
            st.subheader("Período Final")
            ano_final = st.selectbox("Ano final", anos, index=len(anos)-1, key="ano_final")
            
            meses_disponiveis_final = sorted(df[df['ano'] == ano_final]['mes'].unique())
            mes_final = st.selectbox(
                "Mês final", 
                meses_disponiveis_final,
                format_func=lambda x: MESES_PT[int(x)],
                index=len(meses_disponiveis_final)-1,
                key="mes_final"
            )
        
        # Converter para datas para comparação
        data_inicial = pd.Timestamp(year=ano_inicial, month=mes_inicial, day=1)
        data_final = pd.Timestamp(year=ano_final, month=mes_final, day=1)
        
        if data_inicial > data_final:
            st.error("O período inicial não pode ser posterior ao período final.")
        else:
            # Filtrar dados
            periodo_df = df[(df['data'] >= data_inicial) & (df['data'] <= data_final)]
            
            if len(periodo_df) == 0:
                st.warning("Não há dados disponíveis para o período selecionado.")
            else:
                st.success(f"Analisando {len(periodo_df)} meses entre {MESES_ABREV_PT[mes_inicial]}/{ano_inicial} e {MESES_ABREV_PT[mes_final]}/{ano_final}")
                
                # Métricas do período
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(f"Total consumido ({unidade})", f"{formatar_valor(periodo_df['consumo'].sum())}")
                    
                with col2:
                    st.metric("Valor total (R$)", formatar_valor(periodo_df['valor'].sum()))
                    
                with col3:
                    st.metric(f"Média mensal ({unidade})", f"{formatar_valor(periodo_df['consumo'].mean())}")
                
                # Gráficos do período
                st.subheader(f"Consumo de {tipo_medicao.capitalize()} no Período Selecionado")
                consumo_periodo_fig = criar_grafico_barras(
                    periodo_df,
                    'consumo',
                    f"Consumo de {tipo_medicao.capitalize()} ({unidade})",
                    f"Consumo ({unidade})",
                    cores_por_ano
                )
                st.plotly_chart(consumo_periodo_fig, use_container_width=True)
                
                st.subheader("Valor das Faturas no Período Selecionado")
                valor_periodo_fig = criar_grafico_barras(
                    periodo_df,
                    'valor',
                    "Valor das Faturas (R$)",
                    "Valor (R$)",
                    cores_por_ano
                )
                st.plotly_chart(valor_periodo_fig, use_container_width=True)
                st.markdown("""
                #### Recursos interativos:

                - **Passe o mouse** sobre qualquer ponto para ver detalhes da fatura específica
                - **Clique e arraste** para ampliar uma área específica do gráfico
                - **Clique duplo** para restaurar a visualização original
                - **Clique na legenda** para ocultar/mostrar anos específicos

                """)

                # Dados detalhados
                with st.expander("Visualizar dados detalhados do período (tabela bruta)"):
                    st.dataframe(periodo_df[['mes_ano','consumo', 'valor']])

    # Aba 4: Comparações
    with tab4:
        # Confirmação de que os dados estão carregados corretamente
        if 'dados_carregados' not in st.session_state or not st.session_state.dados_carregados:
            st.warning("⚠️ Nenhum dado carregado. Por favor, volte à aba 'Introdução' para carregar dados.")
            st.stop()
        df = st.session_state.df
        tipo_conta = st.session_state.tipo_conta

        st.header("Comparações de Consumo e Valores")
        
        # Opções de visualização
        visualization_type = st.radio(
            "Escolha o tipo de visualização:",
            ["Comparação de Consumo por Ano", "Comparação de Valores por Ano", "Consumo x Valor"],
            horizontal=True
        )
        
        if visualization_type in ["Comparação de Consumo por Ano", "Comparação de Valores por Ano"]:
            # Seleção de anos para comparar
            anos_para_comparar = st.multiselect(
                "Selecione anos para comparação:",
                anos,
                default=anos[-2:] if len(anos) >= 2 else anos
            )
            
            if len(anos_para_comparar) < 2:
                st.info("Selecione pelo menos dois anos para visualização comparativa.")
            else:
                if visualization_type == "Comparação de Consumo por Ano":
                    st.subheader(f"Comparativo de Consumo de {tipo_medicao.capitalize()} ({unidade})")
                    fig_comp = criar_grafico_comparativo(
                        df,
                        anos_para_comparar,
                        'consumo',
                        f"Comparativo de Consumo de {tipo_medicao.capitalize()} Mensal ({unidade})",
                        f"Consumo ({unidade})",
                        cores_por_ano
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                else:
                    st.subheader("Comparativo de Valores das Faturas (R$)")
                    fig_comp = criar_grafico_comparativo(
                        df,
                        anos_para_comparar,
                        'valor',
                        "Comparativo de Valor das Faturas Mensal (R$)",
                        "Valor (R$)",
                        cores_por_ano
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                
                # Tabela comparativa por mês
                with st.expander("Visualizar tabela comparativa"):
                    comp_data = []
                    for mes in range(1, 13):
                        row = {'Mês': MESES_PT[mes]}
                        for ano in anos_para_comparar:
                            filtered = df[(df['ano'] == ano) & (df['mes'] == mes)]
                            if visualization_type == "Comparação de Consumo por Ano":
                                if not filtered.empty:
                                    row[f'Consumo {ano}'] = f"{filtered['consumo'].values[0]:,.1f} {unidade}".replace(',', '.')
                                else:
                                    row[f'Consumo {ano}'] = "N/A"
                            else:
                                if not filtered.empty:
                                    row[f'Valor {ano}'] = formatar_valor(filtered['valor'].values[0])
                                else:
                                    row[f'Valor {ano}'] = "N/A"
                        comp_data.append(row)
                    
                    comp_df = pd.DataFrame(comp_data)
                    st.dataframe(comp_df, use_container_width=True)
        
        else:  # Consumo x Valor
            st.subheader("Relação entre Consumo e Valor")
            
            # Criar gráfico de dispersão
            df_scatter = df.copy()
            df_scatter['ano_str'] = df_scatter['ano'].astype(str)
            cores_str = {str(ano): cor for ano, cor in cores_por_ano.items()}

            scatter_fig = px.scatter(
                df_scatter,
                x='consumo',
                y='valor',
                color='ano_str',
                title=f"Relação entre Consumo e Valor das Faturas",
                labels={'consumo': f'Consumo({unidade})','valor':'Valor(R$)','ano_str':'Ano'},
                trendline='ols',
                hover_data=['mes_ano'],
                color_discrete_map=cores_str
            )
            scatter_fig.update_layout(
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(scatter_fig, use_container_width=True)
            
            # Calcular e exibir correlação
            correlacao = df['consumo'].corr(df['valor'])
            st.metric("Correlação entre Consumo e Valor", f"{correlacao:.2f}")
            
            if correlacao > 0.7:
                st.success("Há uma forte correlação positiva entre consumo e valor. Isso indica que os valores das faturas são fortemente influenciados pelo seu consumo.")
            elif correlacao > 0.4:
                st.info("Há uma correlação moderada entre consumo e valor. Outros fatores além do consumo também influenciam significativamente o valor da fatura.")
            else:
                st.warning("A correlação entre consumo e valor é fraca. O valor da sua fatura parece ser mais influenciado por outros fatores além do consumo.")
            
            st.markdown("""
            ### Como interpretar este gráfico

            Este gráfico de dispersão mostra a relação entre o consumo e o valor das faturas ao longo do tempo. Cada ponto representa uma fatura mensal, onde:

            - O eixo horizontal (X) representa o consumo em unidades (KWh ou m³)
            - O eixo vertical (Y) representa o valor pago em reais (R$)
            - Cada cor representa um ano diferente, permitindo identificar padrões ao longo do tempo
            - A linha de tendência (tracejada) mostra a relação geral entre consumo e valor

            #### O que observar:

            1. **Correlação**: O valor numérico da correlação indica a força da relação entre consumo e valor:
            - Próximo a 1.0: forte relação (o valor aumenta proporcionalmente ao consumo)
            - Próximo a 0.5: relação moderada (outros fatores também influenciam o valor)
            - Próximo a 0.0: relação fraca (consumo e valor variam independentemente)

            2. **Dispersão dos pontos**:
            - Pontos agrupados próximos à linha de tendência: relação consistente
            - Pontos muito dispersos: variabilidade nas tarifas ou presença de cobranças adicionais
            - Pontos afastados (outliers): possíveis cobranças excepcionais ou erros de medição

            3. **Agrupamentos por cor**:
            - Pontos da mesma cor agrupados: padrão de consumo/valor consistente naquele ano
            - Separação clara entre cores: possível mudança de tarifas entre anos

            #### Recursos interativos:

            - **Passe o mouse** sobre qualquer ponto para ver detalhes da fatura específica
            - **Clique e arraste** para ampliar uma área específica do gráfico
            - **Clique duplo** para restaurar a visualização original
            - **Clique na legenda** para mostrar/ocultar anos específicos

            Este gráfico é especialmente útil para identificar se aumentos nas faturas são proporcionais ao consumo ou se outros fatores (como reajustes tarifários) estão influenciando seus gastos.
            """)
            
            st.info("""
            **Nota sobre custo por unidade:** 
            Uma análise de custo por unidade não está sendo mostrada porque faturas de serviços públicos 
            geralmente incluem tarifas fixas, impostos e outros componentes que não são diretamente 
            proporcionais ao consumo. Sem separar esses componentes, o cálculo de custo por unidade 
            poderia levar a conclusões imprecisas.
            """)

# Executar o aplicativo
if __name__ == "__main__":
    main()
