# Bibliotecas necessárias
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
import plotly.express as px
from millify import prettify

# Inicialização da página
df = pd.DataFrame()

st.set_page_config(page_title='Dashboard de Gastos MIDR', page_icon='📊', layout='wide')
st.title("📊 Análise de Gastos - MIDR")

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Início','Visão Geral','Análise por Intervalo de Tempo','Análise Comparativa','Sobre'])


# 1. Introdução e Carregamento de Arquivos
with tab1:
    # Texto de início
    st.header('Bem Vindo(a)!')
    st.text('Este é um sistema experimental dedicado à análise de gastos do Ministério da Integração e do Desenvolvimento Regional.\n' \
    'Aqui, a ideia é simples: o site recebe seu arquivo, dentro das especificações de formatação, e exibe seus dados em diversos gráficos comparativos ' \
    'que facilitam a visualização e interpretação desses dados.\nIdealizado para receber informações de faturas de água e energia, é importante que os arquivos ' \
    'enviados sigam uma certa estrutura, afim de que a leitura seja realizada corretamente. A seguir, será abordada a maneira na qual se espera que o arquivo enviado ' \
    'esteja formatado.')
    st.badge('Em construção', icon=':material/info:', color='orange')
    st.divider()
    st.header('Atenção!')
    st.text('Para garantir que a leitura do arquivo enviado seja feita sem erros pelo sistema,')
    st.divider()
    
    # Botão seletor de tipo de fatura para análise
    select_conta = st.selectbox(
        "Qual tipo de fatura será enviada?",
        ('Conta de água(CAESB)','Conta de energia(CEB)'),
         index=None,
         placeholder="Selecione o tipo de conta...",
    )
    st.write('Você está analisando:', select_conta)
    
    # Checar se o tipo de conta foi selecionada antes de prosseguir para envio
    if select_conta is None:
        st.info('👆 Escolha um tipo de conta para prosseguir com o envio.')
        st.stop()
    elif select_conta == 'Conta de água(CAESB)':
        metrica = 'm³'
        medicao = 'água'
    elif select_conta == 'Conta de energia(CEB)':
        metrica = 'KW/h'
        medicao = 'energia'
    
    # Carregar um exemplo de DataFrame aleatório como DEMO do site
    exemplo_ativado = st.button("📊 Carregar arquivo de exemplo")

    if exemplo_ativado:
        anos_exemplo = random.sample(range(2020, 2031), random.randint(2, 4))
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        dados_exemplo = []
        for ano in anos_exemplo:
            for mes in meses:
                consumo = np.random.randint(150, 550)
                valor = np.random.randint(7000, 20000)
                dados_exemplo.append([mes, ano, consumo, valor])
        
        df_exemplo = pd.DataFrame(dados_exemplo, columns=['mes', 'ano', 'consumo_mensal', 'valor_mensal'])
        
        # Definindo 'data_plotly' para garantir compatibilidade com os gráficos
        df_exemplo['mes_num'] = df_exemplo['mes'].map({'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 
                                                    'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8, 
                                                    'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12})
        df_exemplo['data_plotly'] = pd.to_datetime(df_exemplo['ano'].astype(str) + '-' + df_exemplo['mes_num'].astype(str) + '-01')
        df_exemplo.drop(columns='mes_num', inplace=True)
        
        df = df_exemplo
        st.success("Dados de exemplo carregados com sucesso!")
        
        # Atualiza as variáveis globais para funcionamento do restante do código
        df.sort_values('data_plotly', inplace=True)
        anos = sorted(df['ano'].unique())
        paleta = px.colors.qualitative.Set1
        cores = {ano: paleta[i % len(paleta)] for i, ano in enumerate(anos)}

    # Seção de envio de arquivo local
    fl = st.file_uploader('📁 Use o botão abaixo para carregar um arquivo local, ou arraste-o até a área.', type=['csv','txt','xlsx'])
    
    if not exemplo_ativado and fl is None:
        st.info("👆 Carregue um arquivo para visualizar seus dados.")
        st.stop()
    
    # Tratamento do arquivo enviado com base no formato de documento
    if not exemplo_ativado and fl is not None:
        file_extension = fl.name.split('.')[-1].lower()
        if file_extension in ['csv','txt']:
            try:
                if file_extension in ['csv','txt']:
                    df = pd.read_csv(fl, sep=None, engine='python')
                elif file_extension in ['xlsx','xls']:
                    df = pd.read_excel(fl)
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {e}")
                st.stop()

        if df.empty:
            st.error("O arquivo carregado não contém dados. Por favor, verifique o arquivo e tente novamente.")
            st.stop()
        st.success(f"✅ Arquivo '{fl.name}' carregado com sucesso!")

        # Tratamento da organização de datas no documento
        if 'mes_ref' in df.columns:
            # Confirmação de que as datas estão no formato correto
            try:
                df['data_plotly'] = pd.to_datetime(df['mes_ref'], format='%m/%Y')
            except:
                st.error("Erro ao processar 'mes_ref'.")
                st.stop()
        elif 'mes' in df.columns and 'ano' in df.columns:
            meses_dict = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                        'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}
            df['mes_num'] = df['mes'].map(meses_dict)
            df['data_plotly'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes_num'].astype(str) + '-01')
        else:
            st.error("As colunas 'mes_ref' ou 'mes' e 'ano' não foram encontradas.")
            st.stop()

        # Organização do DataFrame de datas
        df.sort_values('data_plotly', inplace=True)
        anos = sorted(df['ano'].unique())

        # Criação de paleta de cores unificada para todos os gráficos
        paleta = px.colors.qualitative.Set1
        cores = {ano: paleta[i % len(paleta)] for i, ano in enumerate(anos)}

# 2. Seção de Visualização de Linha do Tempo (todos os dados do DF original, com scroller horizontal para visualização seletiva)
with tab2:
    def grafico_timeline():
        fig = go.Figure()
        anos = sorted(df['ano'].unique())
        for i, ano in enumerate(anos):
            df_ano = df[df['ano'] == ano]
            if i > 0:
                prev = df[df['ano'] == anos[i-1]].iloc[-1]
                df_con = pd.DataFrame([prev, df_ano.iloc[0]])
                fig.add_trace(go.Scatter(
                    x=df_con['data_plotly'], y=df_con['consumo_mensal'], mode='lines',
                    line=dict(width=2, color='gray', dash='dot'), showlegend=False, hoverinfo='skip'
                ))
            fig.add_trace(go.Scatter(
                x=df_ano['data_plotly'], y=df_ano['consumo_mensal'],
                mode='lines+markers',
                line=dict(width=3, color=cores[ano]),
                marker=dict(size=8, color=cores[ano]),
                name=f'Ano {ano}',
                hovertemplate='<b>Mês:</b> %{x|%b/%Y}<br><b>Consumo:</b> %{y}<extra></extra>'
            ))
        fig.update_layout(
            title= f"Evolução do Consumo de {medicao} ao Longo do Tempo",
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
    
    # Plot do gráfico de linha do tempo, scroller horizontal e legendas
    st.header("Linha do Tempo Geral")
    st.plotly_chart(grafico_timeline(), use_container_width=True)
    st.caption("Use o gráfico secundário como rolador horizontal para visualizar a linha do tempo.")

# 3. Seção de Análise dos Dados por Intervalo de Tempo (gráficos de consumo e custo, exibição dos dados filtrados no intervalo, como somatório do valor, consumo e média de gasto)
with tab3:
    st.header("Análise por Intervalo de Tempo")

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

    # Criação do DataFrame filtrado pelo intervalo de tempo selecionado com botões interativos
    data_inicio = pd.Timestamp(year=ano_inicio, month=mes_inicio_num, day=1)
    data_fim = pd.Timestamp(year=ano_fim, month=mes_fim_num, day=1) + pd.offsets.MonthEnd(0)
    df_filtrado = df[(df['data_plotly'] >= data_inicio) & (df['data_plotly'] <= data_fim)]
    df_filtrado['ano_str'] = df_filtrado['ano'].astype(str)
    cores_str = {str(ano): cor for ano, cor in cores.items()}

    if not df_filtrado.empty:
        st.subheader(f"Dados filtrados: {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim}")
        st.dataframe(df_filtrado[['mes', 'ano', 'consumo_mensal', 'valor_mensal']] if 'mes_ref' not in df_filtrado.columns else df_filtrado[['mes_ref', 'consumo_mensal', 'valor_mensal']])
        valor_intervalo = str(prettify(f"{df_filtrado['valor_mensal'].sum():.2f}",'.')).replace('.',',')
        valor_intervalo = valor_intervalo.replace(',','.',valor_intervalo.count(',')-1)
        media_intervalo = str(f"{df_filtrado['consumo_mensal'].mean():.2f}").replace('.',',')
        colm1, colm2, colm3 = st.columns(3)
        colm1.metric(f"Total de Consumo ({metrica})", f"{prettify(df_filtrado['consumo_mensal'].sum(),'.')}")
        colm2.metric("Valor Total (R$)", f"R$ {valor_intervalo}")    
        colm3.metric(f"Média Mensal ({metrica})", f"{media_intervalo}")

        eixo_x = 'data_plotly'
        if 'mes_ref' in df_filtrado.columns:
            eixo_x = 'mes_ref'

        st.plotly_chart(
            px.bar(
                df_filtrado,
                x=eixo_x,
                y='consumo_mensal',
                title=f"Consumo Mensal de {medicao} ({metrica})",
                labels={'consumo_mensal': f'Consumo ({metrica})', eixo_x: 'Mês/Ano'},
                color='ano_str',
                color_discrete_map=cores_str,
                text_auto=True
            ).update_layout(legend_title_text='Ano', height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)),
            use_container_width=True
        )
        
        st.plotly_chart(
            px.line(
                df_filtrado,
                x=eixo_x,
                y='valor_mensal',
                title='Valor Mensal da Fatura (R$)',
                labels={'valor_mensal': 'Valor (R$)', eixo_x: 'Mês/Ano'},
                color='ano_str',
                markers=True,
                color_discrete_map=cores_str
            ).update_layout(legend_title_text='Ano', height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)),
            use_container_width=True
        )

    else:
        st.warning("Nenhum dado encontrado para o período selecionado. Por favor, ajuste os filtros.")

with tab4:
    st.header("Comparativo Ano a Ano")

    anos_para_comparar = st.multiselect(
        "Selecione um ou mais anos para comparação:",
        anos,
        default=anos if len(anos) <= 3 else anos[-2:]
    )
    if len(anos_para_comparar) < 2:
        st.info("Selecione pelo menos dois anos para visualização comparativa.")
    else:
        df_comp = df[df['ano'].isin(anos_para_comparar)].copy()
    
        if 'mes_num' not in df_comp.columns:
            if 'mes' in df_comp.columns and isinstance(df_comp['mes'].iloc[0], str):
                df_comp['mes_num'] = df_comp['mes'].map(meses_dict)
            else:
                df_comp['mes_num'] = df_comp['mes']
    
        df_comp.sort_values(['ano', 'mes_num'], inplace=True)
    
        fig_comp1 = go.Figure()
        for ano in anos_para_comparar:
            df_ano = df_comp[df_comp['ano'] == ano]
            fig_comp1.add_trace(go.Scatter(
                x=df_ano['mes_num'],
                y=df_ano['consumo_mensal'],
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
                y=df_ano['valor_mensal'],
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