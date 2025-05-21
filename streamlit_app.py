import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import calendar
from datetime import datetime
import io

# Função para gerar dicionário de cores por ano
def gerar_cores_por_ano(anos):
    """
    Atribui uma cor consistente para cada ano usando uma paleta qualitativa
    """
    paleta = px.colors.qualitative.Set1
    return {ano: paleta[i % len(paleta)] for i, ano in enumerate(sorted(anos))}

# Configuração da página
st.set_page_config(page_title='Dashboard de Análise de Faturas', page_icon='📊', layout='wide')


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
        df['nome_mes'] = df['mes'].apply(lambda x: calendar.month_name[int(x)])
        
        # Adicionar coluna de mês/ano para exibição
        df['mes_ano'] = df['data'].dt.strftime('%b/%Y')
        
        # Ordenar por data
        df = df.sort_values('data')
        
        # Definir unidade de medida com base no tipo de conta
        if tipo_conta == 'Conta de água(CAESB)':
            df['unidade'] = 'm³'
            df['tipo_medicao'] = 'água'
        else:
            df['unidade'] = 'kWh'
            df['tipo_medicao'] = 'energia'
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None

# Função para gerar dados de exemplo
def gerar_dados_exemplo(tipo_conta):
    # Determinar unidade e tipo de medição
    if tipo_conta == 'Conta de água(CAESB)':
        unidade = 'm³'
        tipo_medicao = 'água'
        min_consumo, max_consumo = 10, 50
        min_valor, max_valor = 50, 300
    else:
        unidade = 'kWh'
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
    df['nome_mes'] = df['mes'].apply(lambda x: calendar.month_name[int(x)])
    df['mes_ano'] = df['data'].dt.strftime('%b/%Y')
    
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
    
    fig.update_layout(
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date", 
            tickformat="%b/%Y",
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
        text_auto=True,
        color_discrete_map=cores_str # Usar o mapa de cores por ano
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
            hovertemplate=f'<b>Mês:</b> %{{x}}<br><b>{y_label}:</b> %{{y}}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=[calendar.month_name[i] for i in range(1, 13)],
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
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Interface principal
def main():
    st.title("📊 Análise de Faturas de Água e Energia")
    
    # Criação das abas
    tab1, tab2, tab3, tab4 = st.tabs(['📋 Introdução', '📊 Visão Geral', '🔍 Análise por Período', '🔄 Comparações'])
    
    # Aba 1: Introdução
    with tab1:
        st.header("Bem-vindo ao Dashboard de Análise de Faturas")
        
        st.markdown("""
        Este aplicativo permite analisar e visualizar seus dados de faturas de água ou energia, 
        ajudando você a entender melhor seus padrões de consumo e gastos ao longo do tempo.
        
        ### Como usar:
        1. Selecione o tipo de fatura (água ou energia)
        2. Faça upload do seu arquivo de dados ou use dados de exemplo
        3. Navegue pelas abas para visualizar diferentes análises
        """)
        
        # Seleção do tipo de conta
        select_conta = st.selectbox(
            "Qual tipo de fatura será analisada?",
            ('Conta de água(CAESB)', 'Conta de energia(CEB)'),
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
        - **mes**: número do mês (1-12)
        - **ano**: ano de referência 
        - **valor**: valor da fatura (em R$)
        - **consumo**: consumo medido (em kWh ou m³)
        """)
        
        # Processamento dos dados
        if exemplo_ativado:
            df = gerar_dados_exemplo(select_conta)
            st.success("✅ Dados de exemplo carregados com sucesso!")
        elif uploaded_file is not None:
            df = processar_dados(uploaded_file, select_conta)
            if df is not None:
                st.success(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")
        else:
            st.info('👆 Carregue um arquivo ou use dados de exemplo para começar a análise.')
            st.stop()
        
        # Armazenar dados na sessão
        if df is not None:
            st.session_state['df'] = df
            st.session_state['tipo_conta'] = select_conta
            
            # Exibir amostra dos dados
            with st.expander("Visualizar dados carregados"):
                st.dataframe(df[['mes', 'ano', 'nome_mes', 'valor', 'consumo']])
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
        st.header("Visão Geral dos Dados")
        
        # Estatísticas gerais
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de registros", len(df))
            st.metric("Período analisado", f"{df['mes_ano'].iloc[0]} a {df['mes_ano'].iloc[-1]}")
            st.metric(f"Total consumido ({unidade})", f"{df['consumo'].sum():,.1f}".replace(',', '.'))
        
        with col2:
            st.metric("Valor total", formatar_valor(df['valor'].sum()))
            st.metric(f"Consumo médio mensal ({unidade})", f"{df['consumo'].mean():,.1f}".replace(',', '.'))
            st.metric("Valor médio mensal", formatar_valor(df['valor'].mean()))
        
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
        else:
            st.warning("Nenhum dado encontrado para o período selecionado.")
    
    # Aba 3: Análise por Período
    with tab3:
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
                format_func=lambda x: calendar.month_name[int(x)],
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
                format_func=lambda x: calendar.month_name[int(x)],
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
                st.success(f"Analisando {len(periodo_df)} meses entre {calendar.month_name[mes_inicial]}/{ano_inicial} e {calendar.month_name[mes_final]}/{ano_final}")
                
                # Métricas do período
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(f"Total consumido ({unidade})", f"{periodo_df['consumo'].sum():,.1f}".replace(',', '.'))
                    
                with col2:
                    st.metric("Valor total", formatar_valor(periodo_df['valor'].sum()))
                    
                with col3:
                    st.metric(f"Média mensal ({unidade})", f"{periodo_df['consumo'].mean():,.1f}".replace(',', '.'))
                
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
                
                # Dados detalhados
                with st.expander("Visualizar dados detalhados do período"):
                    st.dataframe(periodo_df[['mes_ano', 'nome_mes', 'ano', 'consumo', 'valor']])
    
    # Aba 4: Comparações
    with tab4:
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
                        row = {'Mês': calendar.month_name[mes]}
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
            
            # Eficiência econômica (custo por unidade)
            st.subheader("Análise de Eficiência (Custo por Unidade)")
            
            df_eficiencia = df.copy()
            df_eficiencia['custo_por_unidade'] = df_eficiencia['valor'] / df_eficiencia['consumo']
            
            df_eficiencia['ano_str'] = df_eficiencia['ano'].astype(str)
            cores_str = {str(ano): cor for ano, cor in cores_por_ano.items()}

            efic_fig = px.line(
                df_eficiencia,
                x='mes_ano',
                y='custo_por_unidade',
                color='ano_str',
                title=f"Custo por Unidade Consumida (R$/{unidade})",
                labels={'mes_ano': 'Período', 'custo_por_unidade': f'R$/{unidade}','ano_str':'Ano'},
                markers=True,
                color_discrete_sequence=cores_str
            )
            
            efic_fig.update_layout(
                height=400,
                hovermode="x unified"
            )
            
            st.plotly_chart(efic_fig, use_container_width=True)
            
            # Estatísticas de eficiência
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Custo médio por unidade", formatar_valor(df_eficiencia['custo_por_unidade'].mean()))
                
            with col2:
                st.metric("Menor custo por unidade", formatar_valor(df_eficiencia['custo_por_unidade'].min()))

# Executar o aplicativo
if __name__ == "__main__":
    main()
