import pandas as pd
import os
import plotly.express as px
import math
import streamlit as st
import pandas as pd
from io import BytesIO
import os

# Função para carregar dados do arquivo Parquet
def load_data(usuario):
    parquet_file = f'dados_acumulados_{usuario}.parquet'  # Caminho completo do arquivo
    if os.path.exists(parquet_file):
        df_total = pd.read_parquet(parquet_file)
    else:
        # Caso o arquivo não exista, cria um dataframe vazio com as colunas definidas
        df_total = pd.DataFrame(columns=['Protocolo', 'Usuário', 'Status', 'Tempo de Análise', 'Próximo'])
    return df_total

# Função para salvar os dados automaticamente no arquivo Parquet
def save_data(df, usuario):
    parquet_file = f'dados_acumulados_{usuario}.parquet'  # Caminho completo do arquivo
    
    # Carregar os dados acumulados anteriores
    df_total = load_data(usuario)
    
    # Remover duplicatas dentro do dataframe do usuário (linha inteira, não apenas algumas colunas)
    df_cleaned = df.drop_duplicates(keep='first')
    
    # Concatenar os dados acumulados com os dados limpos do usuário
    df_total = pd.concat([df_total, df_cleaned], ignore_index=True)
    
    # Remover duplicatas do dataframe acumulado (linha inteira, não apenas algumas colunas)
    df_total = df_total.drop_duplicates(keep='first')

    # Remover linhas com os nomes específicos
    nomes_a_excluir = ["BERNARDO DE FREITAS COSTA LIN", "CAROLINA DE PAULA DA SILVA PER"]
    df_total = df_total[~df_total['Usuário'].isin(nomes_a_excluir)]

    # Salvar os dados no arquivo Parquet sem precisar de interação do usuário
    df_total.to_parquet(parquet_file, index=False)

def calcular_tmo_por_dia(df):
    df['Dia'] = df['Próximo'].dt.date
    df_finalizados = df[df['Status'] == 'FINALIZADO'].copy()
    df_tmo = df_finalizados.groupby('Dia').agg(
        Tempo_Total=('Tempo de Análise', 'sum'),
        Total_Protocolos=('Tempo de Análise', 'count')
    ).reset_index()
    df_tmo['TMO'] = (df_tmo['Tempo_Total'] / pd.Timedelta(minutes=1)) / df_tmo['Total_Protocolos']
    return df_tmo[['Dia', 'TMO']]

def calcular_produtividade_diaria(df):
    df['Dia'] = df['Próximo'].dt.date
    df_produtividade = df.groupby('Dia').agg(
        Andamento=('Status', lambda x: x[x == 'ANDAMENTO_PRE'].count()),
        Finalizado=('Status', lambda x: x[x == 'FINALIZADO'].count()),
        Reclassificado=('Status', lambda x: x[x == 'RECLASSIFICADO'].count())
    ).reset_index()
    df_produtividade['Produtividade'] = df_produtividade['Andamento'] + df_produtividade['Finalizado'] + df_produtividade['Reclassificado']
    return df_produtividade

def convert_to_timedelta_for_calculations(df):
    df['Tempo de Análise'] = pd.to_timedelta(df['Tempo de Análise'], errors='coerce')
    return df

def convert_to_datetime_for_calculations(df):
    df['Próximo'] = pd.to_datetime(df['Próximo'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    return df
        
def format_timedelta(td):
    if pd.isnull(td):
        return "0 min"
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} min {seconds}s"

# Função para calcular o TMO por analista
def calcular_tmo(df_total):
    # Calcula o TMO por analista
    users_tmo = df_total['Usuário'].unique()
    df_tmo_analista = df_total[df_total['Usuário'].isin(users_tmo)].groupby('Usuário').agg(
        Tempo_Total=('Tempo de Análise', 'sum'),
        Total_Protocolos=('Tempo de Análise', 'count')
    ).reset_index()
    df_tmo_analista['TMO'] = df_tmo_analista['Tempo_Total'] / df_tmo_analista['Total_Protocolos']
    df_tmo_analista['TMO_Formatado'] = df_tmo_analista['TMO'].apply(lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02}")

    return df_tmo_analista

# Função para calcular o ranking dinâmico
def calcular_ranking(df_total, selected_users):
    # Filtra o DataFrame com os usuários selecionados
    df_filtered = df_total[df_total['Usuário'].isin(selected_users)]

    df_ranking = df_filtered.groupby('Usuário').agg(
        Andamento=('Status', lambda x: x[x == 'ANDAMENTO_PRE'].count()),
        Finalizado=('Status', lambda x: x[x == 'FINALIZADO'].count()),
        Reclassificado=('Status', lambda x: x[x == 'RECLASSIFICADO'].count())
    ).reset_index()
    df_ranking['Total'] = df_ranking['Andamento'] + df_ranking['Finalizado'] + df_ranking['Reclassificado']
    df_ranking = df_ranking.sort_values(by='Total', ascending=False).reset_index(drop=True)
    df_ranking.index += 1
    df_ranking.index.name = 'Posição'

    # Define o tamanho dos quartis
    num_analistas = len(df_ranking)
    quartil_size = 4 if num_analistas > 12 else math.ceil(num_analistas / 4)

    # Função de estilo para os quartis dinâmicos
    def apply_dynamic_quartile_styles(row):
        if row.name <= quartil_size:
            color = 'rgba(135, 206, 250, 0.4)'  # Azul vibrante translúcido (primeiro quartil)
        elif quartil_size < row.name <= 2 * quartil_size:
            color = 'rgba(144, 238, 144, 0.4)'  # Verde vibrante translúcido (segundo quartil)
        elif 2 * quartil_size < row.name <= 3 * quartil_size:
            color = 'rgba(255, 255, 102, 0.4)'  # Amarelo vibrante translúcido (terceiro quartil)
        else:
            color = 'rgba(255, 99, 132, 0.4)'  # Vermelho vibrante translúcido (quarto quartil)
        return ['background-color: {}'.format(color) for _ in row]

    # Aplicar os estilos e retornar o DataFrame
    styled_df_ranking = df_ranking.style.apply(apply_dynamic_quartile_styles, axis=1).format(
        {'Andamento': '{:.0f}', 'Finalizado': '{:.0f}', 'Reclassificado': '{:.0f}', 'Total': '{:.0f}'}
    )

    return styled_df_ranking

def calcular_tempo_medio_analista(df_analista):
    # Filtra as linhas com status 'FINALIZADO', 'RECLASSIFICADO' ou 'ANDAMENTO_PRE'
    df_filtrado = df_analista[df_analista['Status'].isin(['FINALIZADO', 'RECLASSIFICADO', 'ANDAMENTO_PRE'])]
    
    # Calcula o tempo médio de análise considerando os status filtrados
    tempo_medio_analista = df_filtrado['Tempo de Análise'].mean()
    
    # Se o tempo médio for válido, formate-o
    if pd.notna(tempo_medio_analista):
        return format_timedelta(tempo_medio_analista)  # Supondo que format_timedelta já formate de acordo
    else:
        return 'Nenhum dado encontrado'

#MÉTRICAS INDIVIDUAIS
def calcular_metrica_analista(df_analista):
    # Verifica se a coluna "Carteira" está presente no DataFrame
    if 'Carteira' not in df_analista.columns:
        st.warning("A coluna 'Carteira' não está disponível nos dados. Verifique o arquivo carregado.")
        return None, None, None, None

    # Excluir os registros com "Carteira" como "Desconhecida"
    df_analista_filtrado = df_analista[df_analista['Carteira'] != "Desconhecida"]

    # Filtra os registros com status "FINALIZADO" e "RECLASSIFICADO" (desconsiderando "ANDAMENTO_PRE")
    df_filtrados = df_analista_filtrado[df_analista_filtrado['Status'].isin(['FINALIZADO', 'RECLASSIFICADO'])]

    # Calcula totais conforme os filtros de status
    total_finalizados = len(df_filtrados[df_filtrados['Status'] == 'FINALIZADO'])
    total_reclass = len(df_filtrados[df_filtrados['Status'] == 'RECLASSIFICADO'])
    total_andamento = len(df_analista[df_analista['Status'] == 'ANDAMENTO_PRE'])

    # Calcula o tempo total de análise considerando "FINALIZADO" e "RECLASSIFICADO" apenas
    tempo_total_analista = df_filtrados[df_filtrados['Status'] == 'FINALIZADO']['Tempo de Análise'].sum()
    tempo_medio_analista = tempo_total_analista / total_finalizados  if total_finalizados > 0 else 0

    return total_finalizados, total_reclass, total_andamento, tempo_medio_analista

def calcular_tmo_equipe(df_total):
    return df_total[df_total['Status'] == 'FINALIZADO']['Tempo de Análise'].mean()

def calcular_filas_analista(df_analista):
    if 'Carteira' in df_analista.columns:
        # Filtra apenas os status relevantes para o cálculo (considerando FINALIZADO e RECLASSIFICADO)
        filas_finalizadas_analista = df_analista[
            df_analista['Status'].isin(['FINALIZADO', 'RECLASSIFICADO', 'ANDAMENTO_PRE'])
        ]
        
        # Agrupa por 'Carteira' e calcula a quantidade de FINALIZADO, RECLASSIFICADO e ANDAMENTO_PRE para cada fila
        carteiras_analista = filas_finalizadas_analista.groupby('Carteira').agg(
            Finalizados=('Status', lambda x: (x == 'FINALIZADO').sum()),
            Reclassificados=('Status', lambda x: (x == 'RECLASSIFICADO').sum()),
            Andamento=('Status', lambda x: (x == 'ANDAMENTO_PRE').sum()),
            TMO_médio=('Tempo de Análise', lambda x: x[x.index.isin(df_analista[(df_analista['Status'].isin(['FINALIZADO', 'RECLASSIFICADO']))].index)].mean())
        ).reset_index()

        # Converte o TMO médio para minutos e segundos
        carteiras_analista['TMO_médio'] = carteiras_analista['TMO_médio'].apply(format_timedelta)

        # Renomeia as colunas para exibição
        carteiras_analista = carteiras_analista.rename(
            columns={'Carteira': 'Fila', 'Finalizados': 'Finalizados', 'Reclassificados': 'Reclassificados', 'Andamento': 'Andamento', 'TMO_médio': 'TMO Médio por Fila'}
        )
        
        return carteiras_analista  # Retorna o DataFrame
    
    else:
        # Caso a coluna 'Carteira' não exista
        return pd.DataFrame({'Fila': [], 'Finalizados': [], 'Reclassificados': [], 'Andamento': [], 'TMO Médio por Fila': []})

def calcular_tmo_por_dia(df_analista):
    # Lógica para calcular o TMO por dia
    df_analista['Dia'] = df_analista['Próximo'].dt.date
    tmo_por_dia = df_analista.groupby('Dia').agg(TMO=('Tempo de Análise', 'mean')).reset_index()
    return tmo_por_dia

def calcular_carteiras_analista(df_analista):
    if 'Carteira' in df_analista.columns:
        filas_finalizadas = df_analista[(df_analista['Status'] == 'FINALIZADO') |
                                        (df_analista['Status'] == 'RECLASSIFICADO') |
                                        (df_analista['Status'] == 'ANDAMENTO_PRE')]

        carteiras_analista = filas_finalizadas.groupby('Carteira').agg(
            Quantidade=('Carteira', 'size'),
            TMO_médio=('Tempo de Análise', 'mean')
        ).reset_index()

        # Renomeando a coluna 'Carteira' para 'Fila' para manter consistência
        carteiras_analista = carteiras_analista.rename(columns={'Carteira': 'Fila'})

        return carteiras_analista
    else:
        return pd.DataFrame({'Fila': [], 'Quantidade': [], 'TMO Médio por Fila': []})
    
def get_points_of_attention(df):
    # Verifica se a coluna 'Carteira' existe no DataFrame
    if 'Carteira' not in df.columns:
        return "A coluna 'Carteira' não foi encontrada no DataFrame."
    
    # Filtra os dados para 'JV ITAU BMG' e outras carteiras
    dfJV = df[df['Carteira'] == 'JV ITAU BMG'].copy()
    dfOutras = df[df['Carteira'] != 'JV ITAU BMG'].copy()
    
    # Filtra os pontos de atenção com base no tempo de análise
    pontos_de_atencao_JV = dfJV[dfJV['Tempo de Análise'] > pd.Timedelta(minutes=2)]
    pontos_de_atencao_outros = dfOutras[dfOutras['Tempo de Análise'] > pd.Timedelta(minutes=5)]
    
    # Combina os dados filtrados
    pontos_de_atencao = pd.concat([pontos_de_atencao_JV, pontos_de_atencao_outros])

    # Verifica se o DataFrame está vazio
    if pontos_de_atencao.empty:
        return "Não existem dados a serem exibidos."

    # Cria o dataframe com as colunas 'PROTOCOLO', 'CARTEIRA' e 'TEMPO'
    pontos_de_atencao = pontos_de_atencao[['Protocolo', 'Carteira', 'Tempo de Análise']].copy()

    # Renomeia a coluna 'Tempo de Análise' para 'TEMPO'
    pontos_de_atencao = pontos_de_atencao.rename(columns={'Tempo de Análise': 'TEMPO'})

    # Converte a coluna 'TEMPO' para formato de minutos
    pontos_de_atencao['TEMPO'] = pontos_de_atencao['TEMPO'].apply(lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}")

    # Remove qualquer protocolo com valores vazios ou NaN
    pontos_de_atencao = pontos_de_atencao.dropna(subset=['Protocolo'])

    # Remove as vírgulas e a parte ".0" do protocolo
    pontos_de_atencao['Protocolo'] = pontos_de_atencao['Protocolo'].astype(str).str.replace(',', '', regex=False)
    
    # Garantir que o número do protocolo não tenha ".0"
    pontos_de_atencao['Protocolo'] = pontos_de_atencao['Protocolo'].str.replace(r'\.0$', '', regex=True)

    return pontos_de_atencao

def calcular_tmo_por_carteira(df):
    # Verifica se as colunas 'Carteira' e 'Tempo de Análise' estão no DataFrame
    if 'Carteira' not in df.columns or 'Tempo de Análise' not in df.columns:
        return "As colunas 'Carteira' e/ou 'Tempo de Análise' não foram encontradas no DataFrame."

    # Agrupa os dados por carteira e calcula o tempo médio de análise para cada grupo
    tmo_por_carteira = df.groupby('Carteira')['Tempo de Análise'].mean().reset_index()

    # Converte o tempo médio de análise para minutos e segundos
    tmo_por_carteira['TMO'] = tmo_por_carteira['Tempo de Análise'].apply(
        lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}"
    )

    # Adiciona uma coluna para o tempo total em segundos (necessário para comparação)
    tmo_por_carteira['Tempo_total_segundos'] = tmo_por_carteira['Tempo de Análise'].apply(lambda x: x.total_seconds())

    # Identifica a carteira com o maior TMO (com base no tempo total em segundos)
    carteira_max_tmo = tmo_por_carteira.loc[
        tmo_por_carteira['Tempo_total_segundos'] == tmo_por_carteira['Tempo_total_segundos'].max()
    ]

    # Identifica a carteira com o menor TMO (com base no tempo total em segundos)
    carteira_min_tmo = tmo_por_carteira.loc[
        tmo_por_carteira['Tempo_total_segundos'] == tmo_por_carteira['Tempo_total_segundos'].min()
    ]

    # Exibe a métrica no Streamlit
    with st.container():
        col1, col2 = st.columns(2)
        with col1.container(border=True):
            st.metric(
                label="Maior TMO",
                value=carteira_max_tmo.iloc[0]['Carteira'],
                delta=f"TMO: {carteira_max_tmo.iloc[0]['TMO']}", delta_color='inverse'
            )
        with col2.container(border=True):
            st.metric(
                label="Menor TMO",
                value=carteira_min_tmo.iloc[0]['Carteira'],
                delta=f"TMO: {carteira_min_tmo.iloc[0]['TMO']}",
                delta_color='normal'
            )

    # Retorna o DataFrame com o TMO formatado
    return tmo_por_carteira[['Carteira', 'TMO']]

def calcular_tmo_por_mes(df):
    # Converter coluna de tempo de análise para timedelta, se necessário
    if df['Tempo de Análise'].dtype != 'timedelta64[ns]':
        df['Tempo de Análise'] = pd.to_timedelta(df['Tempo de Análise'], errors='coerce')
    
    # Adicionar coluna com ano e mês extraído da coluna 'Próximo'
    df['AnoMes'] = df['Próximo'].dt.to_period('M')
    
    # Filtrar apenas os protocolos com status 'FINALIZADO'
    df_finalizados = df[df['Status'] == 'FINALIZADO']
    
    # Agrupar por AnoMes e calcular o TMO
    df_tmo_mes = df_finalizados.groupby('AnoMes').agg(
        Tempo_Total=('Tempo de Análise', 'sum'),
        Total_Protocolos=('Tempo de Análise', 'count')
    ).reset_index()
    
    # Calcular o TMO em minutos
    df_tmo_mes['TMO'] = (df_tmo_mes['Tempo_Total'] / pd.Timedelta(minutes=1)) / df_tmo_mes['Total_Protocolos']
    
    # Converter a coluna AnoMes para datetime e formatar como "Mês XX de Ano"
    df_tmo_mes['AnoMes'] = df_tmo_mes['AnoMes'].dt.to_timestamp().dt.strftime('%B de %Y').str.capitalize()
    
    return df_tmo_mes[['AnoMes', 'TMO']]

# Função de formatação
def format_timedelta_mes(minutes):
    """Formata um valor em minutos (float) como 'X min Ys'."""
    minutes_int = int(minutes)  # arredondar para minutos inteiros
    seconds = (minutes - minutes_int) * 60  # calcular os segundos restantes
    seconds_int = round(seconds)  # arredondar para o inteiro mais próximo
    return f"{minutes_int} min {seconds_int}s"

def exibir_tmo_por_mes(df):
    # Calcule o TMO mensal usando a função importada
    df_tmo_mes = calcular_tmo_por_mes(df)
    
    # Verifique se há dados para exibir
    if df_tmo_mes.empty:
        st.warning("Nenhum dado finalizado disponível para calcular o TMO mensal.")
    else:
        # Formatar a coluna TMO como "X min Ys"
        df_tmo_mes['TMO_Formatado'] = df_tmo_mes['TMO'].apply(format_timedelta_mes)
        
        st.subheader("TMO por Mês")        
        # Crie e exiba o gráfico de barras do TMO mensal
        fig = px.bar(
            df_tmo_mes, 
            x='AnoMes', 
            y='TMO', 
            labels={'AnoMes': 'Mês', 'TMO': 'TMO (minutos)'},
            text=df_tmo_mes['TMO_Formatado'], # Usar o TMO formatado como rótulo
            color_discrete_sequence=['#ff571c', '#7f2b0e', '#4c1908', '#ff884d', '#a34b28', '#331309']  # Cor azul
        )
        # Garantir que o eixo X seja tratado como categórico
        fig.update_xaxes(type='category')
        
        # Configurar o layout do gráfico
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
def exibir_dataframe_tmo_formatado(df):
    # Calcule o TMO mensal usando a função `calcular_tmo_por_mes`
    df_tmo_mes = calcular_tmo_por_mes(df)
    
    # Verifique se há dados para exibir
    if df_tmo_mes.empty:
        st.warning("Nenhum dado finalizado disponível para calcular o TMO mensal.")
        return None
    
    # Adicionar a coluna "Tempo Médio Operacional" com base no TMO calculado
    df_tmo_mes['Tempo Médio Operacional'] = df_tmo_mes['TMO'].apply(format_timedelta_mes)
    df_tmo_mes['Mês'] = df_tmo_mes['AnoMes']
    
    # Selecionar as colunas para exibição
    df_tmo_formatado = df_tmo_mes[['Mês', 'Tempo Médio Operacional']]
    
    st.dataframe(df_tmo_formatado, use_container_width=True, hide_index=True)
    
    return df_tmo_formatado

def export_dataframe(df):
    st.subheader("Exportar Dados")
    
    # Seleção de colunas
    colunas_disponiveis = list(df.columns)
    colunas_selecionadas = st.multiselect(
        "Selecione as colunas que deseja exportar:", colunas_disponiveis, default=[]
    )
    
    # Filtrar o DataFrame pelas colunas selecionadas
    if colunas_selecionadas:
        df_filtrado = df[colunas_selecionadas]
        
        # Botão de download
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Dados_Exportados')
        buffer.seek(0)
        
        st.download_button(
            label="Baixar Excel",
            data=buffer,
            file_name="dados_exportados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Selecione pelo menos uma coluna para exportar.")