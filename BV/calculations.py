import pandas as pd
import os
import plotly.express as px
import math
import streamlit as st
import locale

locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

def load_data(usuario):
    pasta_bv = 'BV'  # Defina o caminho da pasta 'BV'
    parquet_file = os.path.join(pasta_bv, f'dados_acumulados_{usuario}.parquet')  # Caminho completo do arquivo
    # Verifica se o arquivo existe e se está intacto
    try:
        if os.path.exists(parquet_file):
            df_total = pd.read_parquet(parquet_file)
        else:
            raise FileNotFoundError
        
    except (FileNotFoundError, ValueError, OSError):
        # Cria um DataFrame vazio e salva um novo arquivo se não existir ou se estiver corrompido
        df_total = pd.DataFrame(columns=[
            'NÚMERO DO PROTOCOLO', 
            'USUÁRIO QUE CONCLUIU A TAREFA', 
            'SITUAÇÃO DA TAREFA', 
            'TEMPO MÉDIO OPERACIONAL', 
            'DATA DE CONCLUSÃO DA TAREFA', 
            'FINALIZAÇÃO'
        ])
        df_total.to_parquet(parquet_file, index=False)
    
    return df_total

# Função para salvar os dados no Parquet do usuário logado
def save_data(df, usuario):
    pasta_bv = 'BV'  # Defina o caminho da pasta 'BV'
    parquet_file = os.path.join(pasta_bv, f'dados_acumulados_{usuario}.parquet')  # Nome do arquivo específico do usuário
    df['TEMPO MÉDIO OPERACIONAL'] = df['TEMPO MÉDIO OPERACIONAL'].astype(str)
    df.to_parquet(parquet_file, index=False)

def calcular_tmo_por_dia(df):
    df['Dia'] = pd.to_datetime(df['DATA DE CONCLUSÃO DA TAREFA']).dt.date
    df_finalizados = df[df['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])].copy()
    
    # Agrupando por dia
    df_tmo = df_finalizados.groupby('Dia').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),  # Soma total do tempo
        Total_Finalizados_Cancelados=('SITUAÇÃO DA TAREFA', 'count')  # Total de tarefas finalizadas ou canceladas
    ).reset_index()

    # Calcula o TMO (Tempo Médio Operacional)
    df_tmo['TMO'] = df_tmo['Tempo_Total'] / df_tmo['Total_Finalizados_Cancelados']
    
    # Formata o tempo médio no formato HH:MM:SS
    df_tmo['TMO'] = df_tmo['TMO'].apply(format_timedelta)
    return df_tmo[['Dia', 'TMO']]

def calcular_tmo_por_dia_geral(df):
    # Certifica-se de que a coluna de data está no formato correto
    df['Dia'] = pd.to_datetime(df['DATA DE CONCLUSÃO DA TAREFA']).dt.date

    # Filtra tarefas finalizadas ou canceladas, pois estas são relevantes para o cálculo do TMO
    df_finalizados = df[df['SITUAÇÃO DA TAREFA'].isin(['Finalizado', 'Cancelada'])].copy()
    
    # Agrupamento por dia para calcular o tempo médio diário
    df_tmo = df_finalizados.groupby('Dia').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),  # Soma total do tempo por dia
        Total_Finalizados_Cancelados=('SITUAÇÃO DA TAREFA', 'count')  # Total de tarefas finalizadas/canceladas por dia
    ).reset_index()

    # Calcula o TMO (Tempo Médio Operacional) diário
    df_tmo['TMO'] = df_tmo['Tempo_Total'] / df_tmo['Total_Finalizados_Cancelados']
    
    # Remove valores nulos e formata o tempo médio para o gráfico
    df_tmo['TMO'] = df_tmo['TMO'].fillna(pd.Timedelta(seconds=0))  # Preenche com zero se houver NaN
    df_tmo['TMO_Formatado'] = df_tmo['TMO'].apply(format_timedelta)  # Formata para exibição
    
    return df_tmo[['Dia', 'TMO', 'TMO_Formatado']]

def calcular_produtividade_diaria(df):
    # Garante que a coluna 'Próximo' esteja em formato de data
    df['Dia'] = df['DATA DE CONCLUSÃO DA TAREFA'].dt.date

    # Agrupa e soma os status para calcular a produtividade
    df_produtividade = df.groupby('Dia').agg(
        Finalizado=('SITUAÇÃO DA TAREFA', lambda x: x[x == 'Finalizada'].count()),
        Cancelada=('SITUAÇÃO DA TAREFA', lambda x: x[x == 'Cancelada'].count())
    ).reset_index()

    # Calcula a produtividade total
    df_produtividade['Produtividade'] = + df_produtividade['Finalizado'] + df_produtividade['Cancelada']
    return df_produtividade

def convert_to_timedelta_for_calculations(df):
    df['TEMPO MÉDIO OPERACIONAL'] = pd.to_timedelta(df['TEMPO MÉDIO OPERACIONAL'], errors='coerce')
    return df

def convert_to_datetime_for_calculations(df):
    df['DATA DE CONCLUSÃO DA TAREFA'] = pd.to_datetime(df['DATA DE CONCLUSÃO DA TAREFA'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    return df
        
def format_timedelta(td):
    if pd.isnull(td):
        return "0 min"
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} min {seconds}s"

# Função para calcular o TMO por analista
def calcular_tmo_por_dia(df):
    df['Dia'] = pd.to_datetime(df['DATA DE CONCLUSÃO DA TAREFA']).dt.date
    df_finalizados = df[df['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])].copy()
    
    # Agrupando por dia
    df_tmo = df_finalizados.groupby('Dia').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),  # Soma total do tempo
        Total_Finalizados_Cancelados=('SITUAÇÃO DA TAREFA', 'count')  # Total de tarefas finalizadas ou canceladas
    ).reset_index()

    # Calcula o TMO (Tempo Médio Operacional)
    df_tmo['TMO'] = df_tmo['Tempo_Total'] / df_tmo['Total_Finalizados_Cancelados']
    
    # Formata o tempo médio no formato HH:MM:SS
    df_tmo['TMO'] = df_tmo['TMO'].apply(format_timedelta)
    return df_tmo[['Dia', 'TMO']]

# Função para calcular o TMO por analista
def calcular_tmo(df):
    # Verifica se a coluna 'SITUAÇÃO DA TAREFA' existe no DataFrame
    if 'SITUAÇÃO DA TAREFA' not in df.columns:
        raise KeyError("A coluna 'SITUAÇÃO DA TAREFA' não foi encontrada no DataFrame.")

    # Filtra as tarefas finalizadas ou canceladas
    df_finalizados = df[df['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])].copy()

    # Verifica se a coluna 'TEMPO MÉDIO OPERACIONAL' existe e converte para minutos
    if 'TEMPO MÉDIO OPERACIONAL' not in df_finalizados.columns:
        raise KeyError("A coluna 'TEMPO MÉDIO OPERACIONAL' não foi encontrada no DataFrame.")
    df_finalizados['TEMPO_MÉDIO_MINUTOS'] = df_finalizados['TEMPO MÉDIO OPERACIONAL'].dt.total_seconds() / 60

    # Verifica se a coluna 'FILA' existe antes de aplicar o filtro
    if 'FILA' in df_finalizados.columns:
        # Remove protocolos da fila "DÚVIDA" com mais de 1 hora de tempo médio
        df_finalizados = df_finalizados[~((df_finalizados['FILA'] == 'DÚVIDA') & (df_finalizados['TEMPO_MÉDIO_MINUTOS'] > 60))]

    # Agrupando por analista
    df_tmo_analista = df_finalizados.groupby('USUÁRIO QUE CONCLUIU A TAREFA').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),  # Soma total do tempo por analista
        Total_Tarefas=('SITUAÇÃO DA TAREFA', 'count')  # Total de tarefas finalizadas ou canceladas por analista
    ).reset_index()

    # Calcula o TMO (Tempo Médio Operacional) como média
    df_tmo_analista['TMO'] = df_tmo_analista['Tempo_Total'] / df_tmo_analista['Total_Tarefas']

    # Formata o tempo médio no formato de minutos e segundos
    df_tmo_analista['TMO_Formatado'] = df_tmo_analista['TMO'].apply(format_timedelta)

    return df_tmo_analista[['USUÁRIO QUE CONCLUIU A TAREFA', 'TMO_Formatado', 'TMO']]

# Função para calcular o ranking dinâmico
def calcular_ranking(df_total, selected_users):
    # Filtra o DataFrame com os usuários selecionados
    df_filtered = df_total[df_total['USUÁRIO QUE CONCLUIU A TAREFA'].isin(selected_users)]

    df_ranking = df_filtered.groupby('USUÁRIO QUE CONCLUIU A TAREFA').agg(

        Finalizado=('SITUAÇÃO DA TAREFA', lambda x: x[x == 'Finalizada'].count()),
        Cancelada=('SITUAÇÃO DA TAREFA', lambda x: x[x == 'Cancelaao'].count())
    ).reset_index()
    df_ranking['Total'] =df_ranking['Finalizado'] + df_ranking['Cancelada']
    df_ranking = df_ranking.sort_values(by  ='Total', ascending=False).reset_index(drop=True)
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

#MÉTRICAS INDIVIDUAIS
def calcular_metrica_analista(df_analista):
    # Verifica se as colunas necessárias estão presentes no DataFrame
    colunas_necessarias = ['FILA', 'SITUAÇÃO DA TAREFA', 'TEMPO MÉDIO OPERACIONAL']
    for coluna in colunas_necessarias:
        if coluna not in df_analista.columns:
            st.warning(f"A coluna '{coluna}' não está disponível nos dados. Verifique o arquivo carregado.")
            return None, None, None

    # Excluir os registros com "FILA" como "Desconhecida"
    df_analista_filtrado = df_analista[df_analista['FILA'] != "Desconhecida"]

    # Filtrar os registros com status "Finalizada" e "Cancelada"
    df_filtrados = df_analista_filtrado[df_analista_filtrado['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])]

    # Converter "TEMPO MÉDIO OPERACIONAL" para minutos
    df_filtrados['TEMPO_MÉDIO_MINUTOS'] = df_filtrados['TEMPO MÉDIO OPERACIONAL'].dt.total_seconds() / 60

    # Excluir registros da fila "DÚVIDA" com tempo médio superior a 1 hora
    df_filtrados = df_filtrados[~((df_filtrados['FILA'] == 'DÚVIDA') & (df_filtrados['TEMPO_MÉDIO_MINUTOS'] > 60))]

    # Calcula totais conforme os filtros de status
    total_finalizados = len(df_filtrados[df_filtrados['SITUAÇÃO DA TAREFA'] == 'Finalizada'])
    total_reclass = len(df_filtrados[df_filtrados['SITUAÇÃO DA TAREFA'] == 'Cancelada'])

    # Calcula o tempo total de análise considerando "Finalizada" e "Cancelada" apenas
    tempo_total_analista = df_filtrados['TEMPO MÉDIO OPERACIONAL'].sum()
    total_tarefas = total_finalizados + total_reclass
    tempo_medio_analista = tempo_total_analista / total_tarefas if total_tarefas > 0 else 0

    return total_finalizados, total_reclass, tempo_medio_analista

def calcular_tmo_equipe(df_total):
    return df_total[df_total['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])]['TEMPO MÉDIO OPERACIONAL'].mean()

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
    df_analista['Dia'] = df_analista['DATA DE CONCLUSÃO DA TAREFA'].dt.date
    tmo_por_dia = df_analista.groupby('Dia').agg(TMO=('TEMPO MÉDIO OPERACIONAL', 'mean')).reset_index()
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
    # Verifica se as colunas 'FILA' e 'TEMPO MÉDIO OPERACIONAL' estão no DataFrame
    if 'FILA' not in df.columns or 'TEMPO MÉDIO OPERACIONAL' not in df.columns:
        return "As colunas 'FILA' e/ou 'TEMPO MÉDIO OPERACIONAL' não foram encontradas no DataFrame."

    # Remove linhas com valores NaN na coluna 'TEMPO MÉDIO OPERACIONAL'
    df = df.dropna(subset=['TEMPO MÉDIO OPERACIONAL'])

    # Verifica se os valores da coluna 'TEMPO MÉDIO OPERACIONAL' são do tipo timedelta
    if not all(isinstance(x, pd.Timedelta) for x in df['TEMPO MÉDIO OPERACIONAL']):
        return "A coluna 'TEMPO MÉDIO OPERACIONAL' contém valores que não são do tipo timedelta."

    # Agrupa os dados por fila e calcula o tempo médio de análise para cada grupo
    tmo_por_carteira = df.groupby('FILA')['TEMPO MÉDIO OPERACIONAL'].mean().reset_index()

    # Converte o tempo médio de análise para minutos e segundos
    tmo_por_carteira['TMO'] = tmo_por_carteira['TEMPO MÉDIO OPERACIONAL'].apply(
        lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}"
    )

    # Seleciona apenas as colunas de interesse
    tmo_por_carteira = tmo_por_carteira[['FILA', 'TMO']]

    return tmo_por_carteira

def calcular_e_exibir_tmo_por_fila(df_analista, analista_selecionado, format_timedelta, st):
    """
    Calcula e exibe o TMO médio por fila, junto com a quantidade de tarefas realizadas, 
    para um analista específico, na dashboard Streamlit.

    Parâmetros:
        - df_analista: DataFrame contendo os dados de análise.
        - analista_selecionado: Nome do analista selecionado.
        - format_timedelta: Função para formatar a duração do TMO em minutos e segundos.
        - st: Referência para o módulo Streamlit (necessário para exibir os resultados).
    """
    if 'FILA' in df_analista.columns:
        # Filtrar apenas as tarefas finalizadas para cálculo do TMO
        filas_finalizadas_analista = df_analista[df_analista['SITUAÇÃO DA TAREFA'] == 'Finalizada']
        
        # Agrupa por 'FILA' e calcula a quantidade e o TMO médio para cada fila
        carteiras_analista = filas_finalizadas_analista.groupby('FILA').agg(
            Quantidade=('FILA', 'size'),
            TMO_médio=('TEMPO MÉDIO OPERACIONAL', 'mean')
        ).reset_index()

        # Converte o TMO médio para minutos e segundos
        carteiras_analista['TMO_médio'] = carteiras_analista['TMO_médio'].apply(format_timedelta)

        # Renomeia as colunas
        carteiras_analista = carteiras_analista.rename(columns={
            'FILA': 'Fila', 
            'Quantidade': 'Quantidade', 
            'TMO_médio': 'TMO Médio por Fila'
        })
        
        # Configura o estilo do DataFrame para alinhar o conteúdo à esquerda
        styled_df = carteiras_analista.style.format({'Quantidade': '{:.0f}', 'TMO Médio por Fila': '{:s}'}).set_properties(**{'text-align': 'left'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'left')])])

        # Exibe a tabela com as colunas Fila, Quantidade e TMO Médio
        st.subheader(f"Filas Realizadas por {analista_selecionado}")
        st.dataframe(styled_df, hide_index=True, width=1080)
    else:
        st.write("A coluna 'FILA' não foi encontrada no dataframe.")
        carteiras_analista = pd.DataFrame({'Fila': [], 'Quantidade': [], 'TMO Médio por Fila': []})
        styled_df = carteiras_analista.style.format({'Quantidade': '{:.0f}', 'TMO Médio por Fila': '{:s}'}).set_properties(**{'text-align': 'left'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'left')])])
        st.dataframe(styled_df, hide_index=True, width=1080)
        
def calcular_e_exibir_protocolos_por_fila(df_analista, analista_selecionado, format_timedelta, st):
    """
    Calcula e exibe informações detalhadas sobre protocolos por fila, incluindo a quantidade de pastas,
    requisições, ID Projuris e tempo médio operacional (TMO), na dashboard Streamlit.

    Parâmetros:
        - df_analista: DataFrame contendo os dados de análise.
        - analista_selecionado: Nome do analista selecionado.
        - format_timedelta: Função para formatar a duração do TMO em minutos e segundos.
        - st: Referência para o módulo Streamlit (necessário para exibir os resultados).
    """
    # Verificar se o DataFrame possui as colunas necessárias
    if not df_analista.empty and 'NÚMERO DO PROTOCOLO' in df_analista.columns and 'FILA' in df_analista.columns:
        # Filtrar apenas as tarefas finalizadas para cálculo do TMO
        filas_finalizadas_analista = df_analista[df_analista['SITUAÇÃO DA TAREFA'] == 'Finalizada']

        # Contar a quantidade de pastas preenchidas para cada protocolo
        pasta_columns = [col for col in filas_finalizadas_analista.columns if col.startswith('PASTA')]
        filas_finalizadas_analista['Quantidade de Pastas'] = filas_finalizadas_analista[pasta_columns].notna().sum(axis=1)

        # Verificar a quantidade de requisições
        filas_finalizadas_analista['Número de Requisições'] = filas_finalizadas_analista['NÚMERO REQUISIÇÃO'].notna().astype(int)
        filas_finalizadas_analista['ID Projuris'] = filas_finalizadas_analista['ID PROJURIS'].notna().astype(int)

        # Agrupar os dados por 'NÚMERO DO PROTOCOLO' e 'FILA'
        protocolos_analista = filas_finalizadas_analista.groupby(['NÚMERO DO PROTOCOLO', 'FILA']).agg(
            Quantidade_de_Pastas=('Quantidade de Pastas', 'first'),
            Número_de_Requisições=('Número de Requisições', 'first'),
            ID_Projuris=('ID Projuris', 'first'),
            TMO_médio=('TEMPO MÉDIO OPERACIONAL', 'mean')
        ).reset_index()

        # Ajustar a quantidade de pastas para exibir 0 caso não haja pastas
        protocolos_analista['Quantidade_de_Pastas'] = protocolos_analista['Quantidade_de_Pastas'].fillna(0)

        # Converter o TMO médio para minutos e segundos
        protocolos_analista['TMO_médio'] = protocolos_analista['TMO_médio'].apply(format_timedelta)

        # Renomear as colunas para exibição
        protocolos_analista = protocolos_analista.rename(columns={
            'NÚMERO DO PROTOCOLO': 'Número do Protocolo',
            'FILA': 'Fila',
            'Quantidade_de_Pastas': 'Quantidade de Pastas',
            'Número_de_Requisições': 'Número de Requisições',
            'ID_Projuris': 'ID Projuris',
            'TMO_médio': 'Tempo de Análise por Protocolo'
        })

        # Configurar o estilo do DataFrame para alinhamento à esquerda
        styled_df = protocolos_analista.style.format({
            'Quantidade de Pastas': '{:.0f}',
            'Número de Requisições': '{:.0f}',
            'Tempo de Análise por Protocolo': '{:s}'
        }).set_properties(**{'text-align': 'left'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'left')])])

        # Exibir a tabela com as colunas solicitadas
        st.subheader(f"Quantidade de Pastas e Requisições por Protocolo - {analista_selecionado}")
        st.dataframe(styled_df, hide_index=True, width=1080)
    else:
        st.write("Não há dados suficientes para exibir a tabela de protocolos por fila.")

def calcular_tmo_por_mes(df):
    # Converter coluna de tempo de análise para timedelta, se necessário
    if df['TEMPO MÉDIO OPERACIONAL'].dtype != 'timedelta64[ns]':
        df['TEMPO MÉDIO OPERACIONAL'] = pd.to_timedelta(df['TEMPO MÉDIO OPERACIONAL'], errors='coerce')
    
    # Adicionar coluna com ano e mês extraído da coluna 'Próximo'
    df['AnoMes'] = df['DATA DE CONCLUSÃO DA TAREFA'].dt.to_period('M')
    
    # Filtrar apenas os protocolos com status 'FINALIZADO'
    df_finalizados = df[df['SITUAÇÃO DA TAREFA'].isin(['Finalizada', 'Cancelada'])]
    
    # Agrupar por AnoMes e calcular o TMO
    df_tmo_mes = df_finalizados.groupby('AnoMes').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),
        Total_Protocolos=('TEMPO MÉDIO OPERACIONAL', 'count')
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