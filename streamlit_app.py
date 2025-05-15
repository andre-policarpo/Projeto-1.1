import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from millify import prettify

# ----------------- CARREGAMENTO E PREPARAÇÃO DOS DADOS -----------------

st.set_page_config(page_title='Dashboard de Gastos MIDR', page_icon='📊', layout='wide')

st.title("📊 Análise de Gastos - MIDR")

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Início','Visão Geral','Análise por Intervalo de Tempo','Análise Comparativa','Sobre'])

tipo_conta = st.sidebar.selectbox(
    'Qual tipo de conta será enviada?',
    ('Conta de água(CAESB)','Conta de energia(CEB)')
)



with tab1:
    st.header('Bem Vindo(a)!')
    st.text('Este é um sistema experimental dedicado à análise de gastos do Ministério da Integração e do Desenvolvimento Regional.\n' \
    'Aqui, a ideia é simples: o site recebe seu arquivo, dentro das especificações de formatação, e exibe seus dados em diversos gráficos comparativos ' \
    'que facilitam a visualização e interpretação desses dados.\nIdealizado para receber informações de faturas de água e energia, é importante que os arquivos ' \
    'enviados sigam uma certa estrutura, afim de que a leitura seja realizada corretamente. A seguir, será abordada a maneira na qual se espera que o arquivo enviado ' \
    'esteja formatado.')
    st.badge('Em construção', icon=':material/info:', color='orange')
    st.divider()

    fl = st.file_uploader('📁 Use o botão abaixo para carregar um arquivo local, ou arraste-o até a área.', type=['csv','txt','xlsx','xls'])
    if fl is not None:
        df = pd.read_csv(fl)
    else:
        df = pd.read_csv('C:/Users/andre.policarpo/resultados_faturas.csv') # caminho padrão do arquivo local

# Confirmação de que as datas estão no formato correto
# Caso contrario, converter mes_ref para datetime (formato 'MM/AAAA')
try:
    df['data_plotly'] = pd.to_datetime(df['mes_ref'], format='%m/%Y')
except:
    # Fallback para mes e ano separados
    meses_dict = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                  'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}
    if 'mes' in df.columns and isinstance(df['mes'].iloc[0], str):
        df['mes_num'] = df['mes'].map(meses_dict)
    else:
        df['mes_num'] = df['mes']
    df['data_plotly'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes_num'].astype(str) + '-01')

df.sort_values('data_plotly', inplace=True)
anos = sorted(df['ano'].unique())

# Paleta de cores automáticas para qualquer quantidade de anos (mantendo consistencia de cor entre graficos)
paleta = px.colors.qualitative.Set1
cores = {ano: paleta[i % len(paleta)] for i, ano in enumerate(anos)}

# ----------------- 1. LINHA DO TEMPO GERAL -----------------

with tab2:
    def grafico_timeline():
        fig = go.Figure()
        anos = sorted(df['ano'].unique())
        for i, ano in enumerate(anos):
            df_ano = df[df['ano'] == ano]
            # Conexão da linha para continuidade visual
            if i > 0:
                prev = df[df['ano'] == anos[i-1]].iloc[-1]
                df_con = pd.DataFrame([prev, df_ano.iloc[0]])
                fig.add_trace(go.Scatter(
                    x=df_con['data_plotly'], y=df_con['consumo_m3'], mode='lines',
                    line=dict(width=2, color='gray', dash='dot'), showlegend=False, hoverinfo='skip'
                ))
            fig.add_trace(go.Scatter(
                x=df_ano['data_plotly'], y=df_ano['consumo_m3'],
                mode='lines+markers',
                line=dict(width=3, color=cores[ano]),
                marker=dict(size=8, color=cores[ano]),
                name=f'Ano {ano}',
                hovertemplate='<b>Mês:</b> %{x|%b/%Y}<br><b>Consumo:</b> %{y} m³<extra></extra>'
            ))
        fig.update_layout(
            title="Evolução do Consumo de Água ao Longo do Tempo",
            height=500,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date", tickformat="%b/%Y",
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

    st.header("Linha do Tempo Geral")
    st.plotly_chart(grafico_timeline(), use_container_width=True)
    st.caption("Use o gráfico secundário como rolador horizontal para visualizar a linha do tempo.")

# ----------------- 2. SEÇÃO DE INTERVALO FILTRADO -----------------

with tab3:
    st.header("Análise por Intervalo de Tempo")

    # Seletores inteligentes para ano/mes
    col1, col2 = st.columns(2)
    with col1:
        ano_inicio = st.selectbox('Ano Inicial', anos, key='ano_inicio')
        meses_do_ano_inicio = df[df['ano'] == ano_inicio]['mes'].unique()
        meses_dict = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                    'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}
        meses_do_ano_inicio = sorted(meses_do_ano_inicio, key=lambda x: meses_dict[x])
        mes_inicio = st.selectbox('Mês Inicial', meses_do_ano_inicio, key='mes_inicio')
        mes_inicio_num = meses_dict[mes_inicio]

    with col2:
        ano_fim = st.selectbox('Ano Final', anos, index=len(anos)-1, key='ano_fim')
        meses_do_ano_fim = df[df['ano'] == ano_fim]['mes'].unique()
        meses_do_ano_fim = sorted(meses_do_ano_fim, key=lambda x: meses_dict[x])
        mes_fim = st.selectbox('Mês Final', meses_do_ano_fim, index=len(meses_do_ano_fim)-1, key='mes_fim')
        mes_fim_num = meses_dict[mes_fim]

    #Criação do DataFrame relacionado ao filtro de tempo
    data_inicio = pd.Timestamp(year=ano_inicio, month=mes_inicio_num, day=1)
    data_fim = pd.Timestamp(year=ano_fim, month=mes_fim_num, day=1) + pd.offsets.MonthEnd(0)
    df_filtrado = df[(df['data_plotly'] >= data_inicio) & (df['data_plotly'] <= data_fim)]
    df_filtrado['ano_str'] = df_filtrado['ano'].astype(str)
    cores_str = {str(ano): cor for ano, cor in cores.items()}

    if not df_filtrado.empty:
        st.subheader(f"Dados filtrados: {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim}")
        st.dataframe(df_filtrado[['mes_ref', 'consumo_m3', 'valor_total']])
        valorf = str(prettify(f'{df_filtrado['valor_total'].sum():.2f}','.')).replace('.',',')
        valorf = valorf.replace(',','.',valorf.count(',')-1)
        mediaf = str(f'{df_filtrado['consumo_m3'].mean():.2f}').replace('.',',')
        colm1, colm2, colm3 = st.columns(3)
        colm1.metric("Total de Consumo (m³)", f"{prettify(df_filtrado['consumo_m3'].sum(),'.')}")
        colm2.metric("Valor Total (R$)", f"R$ {valorf}")    
        colm3.metric("Média Mensal (m³)", f"{mediaf}")

        # Gráfico de Consumo Mensal
        st.plotly_chart(
            px.bar(
                df_filtrado,
                x='mes_ref',
                y='consumo_m3',
                title='Consumo Mensal de Água (m³)',
                labels={'consumo_m3': 'Consumo (m³)', 'mes_ref': 'Mês/Ano'},
                color='ano_str',
                color_discrete_map=cores_str,
                text_auto=True
            ).update_layout(legend_title_text='Ano', height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)),
            use_container_width=True
        )
        # Gráfico de Valor Mensal
        st.plotly_chart(
            px.line(
                df_filtrado,
                x='mes_ref',
                y='valor_total',
                title='Valor Total da Fatura (R$)',
                labels={'valor_total': 'Valor (R$)', 'mes_ref': 'Mês/Ano'},
                color= 'ano_str',
                markers=True,
                color_discrete_map=cores_str
            ).update_layout(legend_title_text='Ano', height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)),
            use_container_width=True
        )

    else:
        st.warning("Nenhum dado encontrado para o período selecionado. Por favor, ajuste os filtros.")


# ----------------- 3. SEÇÃO COMPARATIVA ENTRE ANOS -----------------

with tab4:
    st.header("Comparativo Ano a Ano")

    # Usuário seleciona anos para comparar (mínimo 2)
    anos_para_comparar = st.multiselect(
        "Selecione um ou mais anos para comparação:",
        anos,
        default=anos if len(anos) <= 3 else anos[-2:]
    )
    if len(anos_para_comparar) < 2:
        st.info("Selecione pelo menos dois anos para visualização comparativa.")
    else:
        # Preparar dados padronizados para sobreposição dos meses
        df_comp = df[df['ano'].isin(anos_para_comparar)].copy()
    
        # Garantir que existe a coluna do número do mês
        if 'mes_num' not in df_comp.columns:
            if 'mes' in df_comp.columns and isinstance(df_comp['mes'].iloc[0], str):
                df_comp['mes_num'] = df_comp['mes'].map(meses_dict)
            else:
                df_comp['mes_num'] = df_comp['mes']
    
        # Ordenar para garantir a correta sobreposição
        df_comp.sort_values(['ano', 'mes_num'], inplace=True)
    
        # Criar um gráfico de linhas: eixo x = mês (1-12), uma linha para cada ano
        fig_comp1 = go.Figure()
        for ano in anos_para_comparar:
            df_ano = df_comp[df_comp['ano'] == ano]
            fig_comp1.add_trace(go.Scatter(
                x=df_ano['mes_num'],
                y=df_ano['consumo_m3'],
                mode='lines+markers',
                name=f"Ano {ano}",
                line=dict(width=3, color=cores[ano]),
                marker=dict(size=8, color=cores[ano]),
                hovertemplate='<b>Mês:</b> %{x}<br><b>Consumo:</b> %{y} m³<extra></extra>'
            ))
        fig_comp1.update_layout(
            xaxis = dict(
                tickmode='array',
                tickvals=list(meses_dict.values()),
                ticktext=list(meses_dict.keys()),
                title='Mês'
            ),
            yaxis_title='Consumo(m³)',
            title="Comparativo de Consumo Mensal: Anos Selecionados",
            height=500,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            hovermode='x'
        )
        fig_comp2 = go.Figure()
        for ano in anos_para_comparar:
            df_ano = df_comp[df_comp['ano'] == ano]
            fig_comp2.add_trace(go.Scatter(
                x=df_ano['mes_num'],
                y=df_ano['valor_total'],
                mode='lines+markers',
                name=f"Ano {ano}",
                line=dict(width=3, color=cores[ano]),
                marker=dict(size=8, color=cores[ano]),
                hovertemplate='<b>Mês:</b> %{x}<br><b>Valor:</b> R$ %{y}<extra></extra>' 
            ))
        fig_comp2.update_layout(
            xaxis = dict(
                tickmode='array',
                tickvals=list(meses_dict.values()),
                ticktext=list(meses_dict.keys()),
                title='Mês'
            ),
            yaxis_title='Valor(R$)',
            title="Comparativo de Valor Mensal: Anos Selecionados",
            height=500,
            legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1),
            hovermode='x'
        )
        
        st.plotly_chart(fig_comp1, use_container_width=True)
        st.plotly_chart(fig_comp2, use_container_width=True)


#-------------- 4. DOCUMENTAÇÃO E SOURCE CODE (TRANSPARENCIA)-------------------------

with tab5:
    st.header("Sobre o projeto")
