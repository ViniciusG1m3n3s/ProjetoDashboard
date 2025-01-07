import pandas as pd
import os
import plotly.express as px
import math
import streamlit as st
from io import BytesIO
from datetime import timedelta

def load_data(usuario):
    excel_file = f'dados_acumulados_{usuario}.xlsx'  # Caminho completo do arquivo
    # Verifica se o arquivo existe e se está intacto
    try:
        if os.path.exists(excel_file):
            df_total = pd.read_excel(excel_file)
            
            # Verifica se a coluna 'Justificativa' existe, caso contrário, adiciona ela
            if 'Justificativa' not in df_total.columns:
                df_total['Justificativa'] = ""  # Adiciona a coluna de justificativa com valores vazios
        else:
            raise FileNotFoundError
        
    except (FileNotFoundError, ValueError, OSError):
        # Cria um DataFrame vazio com a coluna 'Justificativa' e salva um novo arquivo
        df_total = pd.DataFrame(columns=[
            'NÚMERO DO PROTOCOLO', 
            'USUÁRIO QUE CONCLUIU A TAREFA', 
            'SITUAÇÃO DA TAREFA', 
            'TEMPO MÉDIO OPERACIONAL', 
            'DATA DE CONCLUSÃO DA TAREFA', 
            'FINALIZAÇÃO',
            'Justificativa'  # Inclui a coluna de justificativa ao criar um novo DataFrame
        ])
        df_total.to_excel(excel_file, index=False)
    
    return df_total

def save_data(df, usuario):
    excel_file = f'dados_acumulados_{usuario}.xlsx'  # Nome do arquivo específico do usuário

    # Certifique-se de que a coluna 'Justificativa' existe antes de salvar
    if 'Justificativa' not in df.columns:
        df['Justificativa'] = ""  # Se não existir, adiciona a coluna com valores vazios

    # Remove registros com 'USUÁRIO QUE CONCLUIU A TAREFA' igual a 'robohub_amil'
    if 'USUÁRIO QUE CONCLUIU A TAREFA' in df.columns:
        df = df[(df['USUÁRIO QUE CONCLUIU A TAREFA'] != 'robohub_amil') & (df['USUÁRIO QUE CONCLUIU A TAREFA'].notnull())]

    # Salva o DataFrame no arquivo Excel
    df['TEMPO MÉDIO OPERACIONAL'] = df['TEMPO MÉDIO OPERACIONAL'].astype(str)  # Ajuste de tipo de coluna, se necessário
    df.to_excel(excel_file, index=False)


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
        Finalizado=('FINALIZAÇÃO', 'count'),
    ).reset_index()

    # Calcula a produtividade total
    df_produtividade['Produtividade'] = + df_produtividade['Finalizado'] 
    return df_produtividade

def calcular_produtividade_diaria_cadastro(df):
    # Garante que a coluna 'Próximo' esteja em formato de data
    df['Dia'] = df['DATA DE CONCLUSÃO DA TAREFA'].dt.date

    # Agrupa e soma os status para calcular a produtividade
    df_produtividade_cadastro = df.groupby('Dia').agg(
        Finalizado=('FINALIZAÇÃO', lambda x: x[x == 'CADASTRADO'].count()),
        Atualizado=('FINALIZAÇÃO', lambda x: x[x == 'ATUALIZADO'].count())
    ).reset_index()

    # Calcula a produtividade total
    df_produtividade_cadastro['Produtividade'] = + df_produtividade_cadastro['Finalizado'] + df_produtividade_cadastro['Atualizado']
    return df_produtividade_cadastro

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

def calcular_tmo_por_dia_cadastro(df):
    df['Dia'] = pd.to_datetime(df['DATA DE CONCLUSÃO DA TAREFA']).dt.date
    df_finalizados_cadastro = df[df['FINALIZAÇÃO'] == 'CADASTRADO'].copy()
    
    # Agrupando por dia
    df_tmo_cadastro = df_finalizados_cadastro.groupby('Dia').agg(
        Tempo_Total=('TEMPO MÉDIO OPERACIONAL', 'sum'),  # Soma total do tempo
        Total_Finalizados_Cancelados=('FINALIZAÇÃO', 'count')  # Total de tarefas finalizadas ou canceladas
    ).reset_index()

    # Calcula o TMO (Tempo Médio Operacional)
    df_tmo_cadastro['TMO'] = df_tmo_cadastro['Tempo_Total'] / df_tmo_cadastro['Total_Finalizados_Cancelados']
    
    # Formata o tempo médio no formato HH:MM:SS
    df_tmo_cadastro['TMO'] = df_tmo_cadastro['TMO'].apply(format_timedelta)
    return df_tmo_cadastro[['Dia', 'TMO']]

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

        Finalizado=('FINALIZAÇÃO', lambda x: x[x == 'CADASTRADO'].count()),
        Distribuido=('FINALIZAÇÃO', lambda x: x[x == 'REALIZADO'].count()),
        Atualizado=('FINALIZAÇÃO', lambda x: x[x == 'ATUALIZADO'].count())
    ).reset_index()
    df_ranking['Total'] =df_ranking['Finalizado'] + df_ranking['Distribuido'] + df_ranking['Atualizado']
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
    colunas_necessarias = ['FILA', 'FINALIZAÇÃO', 'TEMPO MÉDIO OPERACIONAL']
    for coluna in colunas_necessarias:
        if coluna not in df_analista.columns:
            st.warning(f"A coluna '{coluna}' não está disponível nos dados. Verifique o arquivo carregado.")
            return None, None, None, None, None, None  # Atualizado para retornar seis valores

    # Excluir os registros com "FILA" como "Desconhecida"
    df_analista_filtrado = df_analista[df_analista['FILA'] != "Desconhecida"]

    # Filtrar os registros com status "CADASTRADO", "ATUALIZADO" e "REALIZADO"
    df_filtrados = df_analista_filtrado[df_analista_filtrado['FINALIZAÇÃO'].isin(['CADASTRADO', 'ATUALIZADO', 'REALIZADO'])]

    # Converter "TEMPO MÉDIO OPERACIONAL" para minutos
    df_filtrados['TEMPO_MÉDIO_MINUTOS'] = df_filtrados['TEMPO MÉDIO OPERACIONAL'].dt.total_seconds() / 60

    # Excluir registros da fila "DÚVIDA" com tempo médio superior a 1 hora
    df_filtrados = df_filtrados[~((df_filtrados['FILA'] == 'DÚVIDA') & (df_filtrados['TEMPO_MÉDIO_MINUTOS'] > 60))]

    # Calcula totais conforme os filtros de status
    total_finalizados = len(df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'CADASTRADO'])
    total_realizados = len(df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'REALIZADO'])
    total_atualizado = len(df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'ATUALIZADO'])

    # Calcula o tempo total para cada tipo de tarefa
    tempo_total_cadastrado = df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'CADASTRADO']['TEMPO MÉDIO OPERACIONAL'].sum()
    tempo_total_atualizado = df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'ATUALIZADO']['TEMPO MÉDIO OPERACIONAL'].sum()
    tempo_total_realizado = df_filtrados[df_filtrados['FINALIZAÇÃO'] == 'REALIZADO']['TEMPO MÉDIO OPERACIONAL'].sum()

    # Calcula o tempo médio para cada tipo de tarefa
    tmo_cadastrado = tempo_total_cadastrado / total_finalizados if total_finalizados > 0 else pd.Timedelta(0)
    tmo_atualizado = tempo_total_atualizado / total_atualizado if total_atualizado > 0 else pd.Timedelta(0)

    # Calcula o tempo médio geral considerando todas as tarefas
    tempo_total_analista = tempo_total_cadastrado + tempo_total_atualizado + tempo_total_realizado
    total_tarefas = total_finalizados + total_atualizado + total_realizados
    tempo_medio_analista = tempo_total_analista / total_tarefas if total_tarefas > 0 else pd.Timedelta(0)

    return total_finalizados, total_atualizado, tempo_medio_analista, tmo_cadastrado, tmo_atualizado, total_realizados

def calcular_tempo_ocioso_por_analista(df):
    try:
        # Converte as colunas de data para datetime, tratando erros
        df['DATA DE INÍCIO DA TAREFA'] = pd.to_datetime(
            df['DATA DE INÍCIO DA TAREFA'], format='%d/%m/%Y %H:%M:%S', errors='coerce'
        )
        df['DATA DE CONCLUSÃO DA TAREFA'] = pd.to_datetime(
            df['DATA DE CONCLUSÃO DA TAREFA'], format='%d/%m/%Y %H:%M:%S', errors='coerce'
        )

        # Filtrar ou preencher valores nulos nas colunas de data
        df = df.dropna(subset=['DATA DE INÍCIO DA TAREFA', 'DATA DE CONCLUSÃO DA TAREFA']).reset_index(drop=True)

        # Ordena os dados por usuário e data de início da tarefa
        df = df.sort_values(by=['USUÁRIO QUE CONCLUIU A TAREFA', 'DATA DE INÍCIO DA TAREFA']).reset_index(drop=True)

        # Calcula o próximo horário de início da tarefa por usuário
        df['PRÓXIMO'] = df.groupby('USUÁRIO QUE CONCLUIU A TAREFA')['DATA DE INÍCIO DA TAREFA'].shift(-1)

        # Extração dos dias para comparar conclusões e inícios
        df['DIA_CONCLUSAO'] = df['DATA DE CONCLUSÃO DA TAREFA'].dt.date
        df['DIA_PROXIMO'] = df['PRÓXIMO'].dt.date

        # Calcula o tempo ocioso entre tarefas no mesmo dia
        df['TEMPO OCIOSO'] = df.apply(
            lambda row: (row['PRÓXIMO'] - row['DATA DE CONCLUSÃO DA TAREFA'])
            if row['DIA_CONCLUSAO'] == row['DIA_PROXIMO'] else pd.Timedelta(0),
            axis=1
        )

        # Filtra para tempo ocioso <= 1 hora e antes das 18h
        df['TEMPO OCIOSO'] = df.apply(
            lambda row: row['TEMPO OCIOSO']
            if (row['TEMPO OCIOSO'] <= pd.Timedelta(hours=1)) and (row['DATA DE CONCLUSÃO DA TAREFA'].hour < 18)
            else pd.Timedelta(0),
            axis=1
        )

        # Formata o tempo ocioso como string
        df['TEMPO_OCIOSO_FORMATADO'] = df['TEMPO OCIOSO'].apply(
            lambda x: str(pd.to_timedelta(x)).split("days")[-1].strip() if pd.notnull(x) else '0:00:00'
        )

        # Agrupa os tempos ociosos por usuário e dia de conclusão
        df_soma_ocioso = df.groupby(['USUÁRIO QUE CONCLUIU A TAREFA', 'DIA_CONCLUSAO'])['TEMPO OCIOSO'].sum().reset_index()

        # Formata o tempo ocioso somado
        df_soma_ocioso['TEMPO_OCIOSO_FORMATADO'] = df_soma_ocioso['TEMPO OCIOSO'].apply(
            lambda x: str(pd.to_timedelta(x)).split("days")[-1].strip() if pd.notnull(x) else '0:00:00'
        )

        # Renomeia as colunas para exibição
        df_soma_ocioso = df_soma_ocioso.rename(columns={
            'DIA_CONCLUSAO': 'Data',
            'TEMPO_OCIOSO_FORMATADO': 'Tempo Ocioso'
        })

        # Retorna o DataFrame sem índice e ajustado para Streamlit
        return df_soma_ocioso[['Data', 'Tempo Ocioso']]

    except Exception as e:
        # Em caso de erro, retorna um DataFrame com a mensagem de erro
        error_df = pd.DataFrame({
            'Usuário': ['Erro'],
            'Data': [''],
            'Tempo Ocioso': [f'Erro: {str(e)}']
        })
        return error_df

def calcular_tmo_equipe_cadastro(df_total):
    return df_total[df_total['FINALIZAÇÃO'].isin(['CADASTRADO'])]['TEMPO MÉDIO OPERACIONAL'].mean()

def calcular_tmo_equipe_atualizado(df_total):
    return df_total[df_total['FINALIZAÇÃO'].isin(['ATUALIZADO'])]['TEMPO MÉDIO OPERACIONAL'].mean()

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
    tmo_por_carteira = df.groupby('FILA').agg(
        Quantidade=('FILA', 'size'),
        TMO_médio=('TEMPO MÉDIO OPERACIONAL', 'mean')
    ).reset_index()

    # Converte o tempo médio de análise para minutos e segundos
    tmo_por_carteira['TMO'] = tmo_por_carteira['TMO_médio'].apply(
        lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}"
    )

    # Seleciona apenas as colunas de interesse
    tmo_por_carteira = tmo_por_carteira[['FILA', 'Quantidade', 'TMO']]

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
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
    else:
        st.write("A coluna 'FILA' não foi encontrada no dataframe.")
        carteiras_analista = pd.DataFrame({'Fila': [], 'Quantidade': [], 'TMO Médio por Fila': []})
        styled_df = carteiras_analista.style.format({'Quantidade': '{:.0f}', 'TMO Médio por Fila': '{:s}'}).set_properties(**{'text-align': 'left'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'left')])])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

def calcular_tmo_por_mes(df):
    # Converter coluna de tempo de análise para timedelta, se necessário
    if df['TEMPO MÉDIO OPERACIONAL'].dtype != 'timedelta64[ns]':
        df['TEMPO MÉDIO OPERACIONAL'] = pd.to_timedelta(df['TEMPO MÉDIO OPERACIONAL'], errors='coerce')
    
    # Adicionar coluna com ano e mês extraído da coluna 'Próximo'
    df['AnoMes'] = df['DATA DE CONCLUSÃO DA TAREFA'].dt.to_period('M')
    
    # Filtrar apenas os protocolos com status 'FINALIZADO'
    df_finalizados = df[df['FINALIZAÇÃO'].isin(['CADASTRADO', 'ATUALIZADO', 'REALIZADO'])]
    
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
    """Formata um valor em minutos (float) como 'Xh Ym Zs' se acima de 60 minutos, caso contrário, 'X min Ys'."""
    if minutes >= 60:
        hours = int(minutes // 60)
        minutes_remainder = int(minutes % 60)
        seconds = (minutes - hours * 60 - minutes_remainder) * 60
        seconds_int = round(seconds)
        return f"{hours}h {minutes_remainder}m {seconds_int}s"
    else:
        minutes_int = int(minutes)
        seconds = (minutes - minutes_int) * 60
        seconds_int = round(seconds)
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
        
        st.subheader("Tempo Médio Operacional Mensal")
        
        # Crie um multiselect para os meses
        meses_disponiveis = df_tmo_mes['AnoMes'].unique()
        meses_selecionados = st.multiselect(
            "Selecione os meses para exibição",
            options=meses_disponiveis,
            default=meses_disponiveis
        )
        
        # Filtrar os dados com base nos meses selecionados
        df_tmo_mes_filtrado = df_tmo_mes[df_tmo_mes['AnoMes'].isin(meses_selecionados)]
        
        # Verificar se há dados após o filtro
        if df_tmo_mes_filtrado.empty:
            st.warning("Nenhum dado disponível para os meses selecionados.")
            return None
        
        # Crie e exiba o gráfico de barras
        fig = px.bar(
            df_tmo_mes_filtrado, 
            x='AnoMes', 
            y='TMO', 
            labels={'AnoMes': 'Mês', 'TMO': 'TMO (minutos)'},
            text=df_tmo_mes_filtrado['TMO_Formatado'], # Usar o TMO formatado como rótulo
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
        
def calcular_melhor_tmo_por_dia(df_analista):
    # Calcula o TMO por dia
    df_tmo_por_dia = calcular_tmo_por_dia(df_analista)
    
    # Identifica o dia com o menor TMO
    if not df_tmo_por_dia.empty:
        melhor_dia = df_tmo_por_dia.loc[df_tmo_por_dia['TMO'].idxmin()]
        return melhor_dia['Dia'], melhor_dia['TMO']
    return None, None

def calcular_melhor_dia_por_cadastro(df_analista):
    # Agrupa os dados por dia e conta os cadastros
    if 'FINALIZAÇÃO' in df_analista.columns and 'DATA DE CONCLUSÃO DA TAREFA' in df_analista.columns:
        df_cadastros_por_dia = df_analista[df_analista['FINALIZAÇÃO'] == 'CADASTRADO'].groupby(
            df_analista['DATA DE CONCLUSÃO DA TAREFA'].dt.date
        ).size().reset_index(name='Quantidade')
        
        # Identifica o dia com maior quantidade de cadastros
        if not df_cadastros_por_dia.empty:
            melhor_dia = df_cadastros_por_dia.loc[df_cadastros_por_dia['Quantidade'].idxmax()]
            return melhor_dia['DATA DE CONCLUSÃO DA TAREFA'], melhor_dia['Quantidade']
    
    return None, 0

def exibir_tmo_por_mes_analista(df_analista, analista_selecionado):
    """
    Exibe o gráfico e a tabela do TMO mensal para um analista específico com filtro por mês.

    Parâmetros:
        - df_analista: DataFrame filtrado para o analista.
        - analista_selecionado: Nome do analista selecionado.
    """
    # Calcular o TMO por mês
    df_tmo_mes = calcular_tmo_por_mes(df_analista)

    # Verificar se há dados para exibir
    if df_tmo_mes.empty:
        st.warning(f"Não há dados para calcular o TMO mensal do analista {analista_selecionado}.")
        return None

    # Formatar o TMO para exibição
    df_tmo_mes['TMO_Formatado'] = df_tmo_mes['TMO'].apply(format_timedelta_mes)

    # Criar multiselect para os meses disponíveis
    meses_disponiveis = df_tmo_mes['AnoMes'].unique()
    meses_selecionados = st.multiselect(
        "Selecione os meses para exibição",
        options=meses_disponiveis,
        default=meses_disponiveis
    )

    # Filtrar os dados com base nos meses selecionados
    df_tmo_mes_filtrado = df_tmo_mes[df_tmo_mes['AnoMes'].isin(meses_selecionados)]

    # Verificar se há dados após o filtro
    if df_tmo_mes_filtrado.empty:
        st.warning("Nenhum dado disponível para os meses selecionados.")
        return None

    # Criar e exibir o gráfico de barras
    fig = px.bar(
        df_tmo_mes_filtrado,
        x='AnoMes',
        y='TMO',
        labels={'AnoMes': 'Mês', 'TMO': 'TMO (minutos)'},
        text=df_tmo_mes_filtrado['TMO_Formatado'],  # Usar o TMO formatado como rótulo
        color_discrete_sequence=['#ff571c', '#7f2b0e', '#4c1908', '#ff884d', '#a34b28', '#331309']
    )
    fig.update_xaxes(type='category')  # Tratar o eixo X como categórico
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    # Criar e exibir a tabela com os dados formatados
    df_tmo_mes_filtrado['Mês'] = df_tmo_mes_filtrado['AnoMes']  # Renomear para exibição
    df_tmo_formatado = df_tmo_mes_filtrado[['Mês', 'TMO_Formatado']].rename(columns={'TMO_Formatado': 'Tempo Médio Operacional'})
    st.dataframe(df_tmo_formatado, use_container_width=True, hide_index=True)

    return df_tmo_formatado

def calcular_tmo_personalizado(df):
    """
    Calcula o TMO considerando as regras específicas para cada tipo de tarefa.

    Parâmetros:
        - df: DataFrame com os dados filtrados.

    Retorno:
        - DataFrame com TMO calculado por analista.
    """
    # Filtrar tarefas por tipo de finalização
    total_finalizados = len(df[df['FINALIZAÇÃO'] == 'CADASTRADO'])
    total_realizados = len(df[df['FINALIZAÇÃO'] == 'REALIZADO'])
    total_atualizado = len(df[df['FINALIZAÇÃO'] == 'ATUALIZADO'])

    # Calcular o tempo total por tipo de finalização
    tempo_total_cadastrado = df[df['FINALIZAÇÃO'] == 'CADASTRADO']['TEMPO MÉDIO OPERACIONAL'].sum()
    tempo_total_atualizado = df[df['FINALIZAÇÃO'] == 'ATUALIZADO']['TEMPO MÉDIO OPERACIONAL'].sum()
    tempo_total_realizado = df[df['FINALIZAÇÃO'] == 'REALIZADO']['TEMPO MÉDIO OPERACIONAL'].sum()

    # Calcular o tempo médio por tipo de finalização
    tmo_cadastrado = tempo_total_cadastrado / total_finalizados if total_finalizados > 0 else pd.Timedelta(0)
    tmo_atualizado = tempo_total_atualizado / total_atualizado if total_atualizado > 0 else pd.Timedelta(0)

    # Calcular o TMO geral
    tempo_total_analista = tempo_total_cadastrado + tempo_total_atualizado + tempo_total_realizado
    total_tarefas = total_finalizados + total_atualizado + total_realizados
    tempo_medio_analista = tempo_total_analista / total_tarefas if total_tarefas > 0 else pd.Timedelta(0)

    return tempo_medio_analista


def exportar_planilha_com_tmo(df, periodo_selecionado, analistas_selecionados):
    """
    Exporta uma planilha com informações do período selecionado, analistas, TMO e quantidade de tarefas,
    adicionando formatação condicional baseada na média do TMO.

    Parâmetros:
        - df: DataFrame com os dados.
        - periodo_selecionado: Tuple contendo a data inicial e final.
        - analistas_selecionados: Lista de analistas selecionados.
    """
    # Filtrar o DataFrame com base no período e analistas selecionados
    data_inicial, data_final = periodo_selecionado
    df_filtrado = df[
        (df['DATA DE CONCLUSÃO DA TAREFA'].dt.date >= data_inicial) &
        (df['DATA DE CONCLUSÃO DA TAREFA'].dt.date <= data_final) &
        (df['USUÁRIO QUE CONCLUIU A TAREFA'].isin(analistas_selecionados))
    ]

    # Calcular o TMO e a quantidade por analista
    analistas = []
    tmos = []
    quantidades = []

    for analista in analistas_selecionados:
        df_analista = df_filtrado[df_filtrado['USUÁRIO QUE CONCLUIU A TAREFA'] == analista]
        tmo_analista = calcular_tmo_personalizado(df_analista)
        quantidade_analista = len(df_analista)
        
        analistas.append(analista)
        tmos.append(tmo_analista)
        quantidades.append(quantidade_analista)

    # Criar o DataFrame de resumo
    df_resumo = pd.DataFrame({
        'Analista': analistas,
        'TMO': tmos,
        'Quantidade': quantidades
    })

    # Adicionar o período ao DataFrame exportado
    df_resumo['Período Inicial'] = data_inicial
    df_resumo['Período Final'] = data_final

    # Formatar o TMO como HH:MM:SS
    df_resumo['TMO'] = df_resumo['TMO'].apply(
        lambda x: f"{int(x.total_seconds() // 3600):02}:{int((x.total_seconds() % 3600) // 60):02}:{int(x.total_seconds() % 60):02}"
    )

    # Calcular a média do TMO em segundos
    tmo_segundos = [timedelta(hours=int(t.split(":")[0]), minutes=int(t.split(":")[1]), seconds=int(t.split(":")[2])).total_seconds() for t in df_resumo['TMO']]
    media_tmo_segundos = sum(tmo_segundos) / len(tmo_segundos)

    # Criar um arquivo Excel em memória
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Exportar os dados
        df_resumo.to_excel(writer, index=False, sheet_name='Resumo')

        # Acessar o workbook e worksheet para aplicar formatação condicional
        workbook = writer.book
        worksheet = writer.sheets['Resumo']

        # Ajustar largura das colunas
        worksheet.set_column('A:A', 20)  # Coluna 'Analista'
        worksheet.set_column('B:B', 12)  # Coluna 'TMO'
        worksheet.set_column('C:C', 15)  # Coluna 'Quantidade'
        worksheet.set_column('D:E', 15)  # Colunas 'Período Inicial' e 'Período Final'

        # Formatação baseada na média do TMO
        format_tmo_green = workbook.add_format({'bg_color': '#CCFFCC', 'font_color': '#006600'})  # Verde
        format_tmo_yellow = workbook.add_format({'bg_color': '#FFFFCC', 'font_color': '#666600'})  # Amarelo
        format_tmo_red = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#FF0000'})  # Vermelho

        # Aplicar formatação condicional
        for row, tmo in enumerate(tmo_segundos, start=2):
            if tmo < media_tmo_segundos * 0.9:  # Abaixo da média
                worksheet.write(f'B{row}', df_resumo.loc[row-2, 'TMO'], format_tmo_green)
            elif media_tmo_segundos * 0.9 <= tmo <= media_tmo_segundos * 1.1:  # Na média ou próximo
                worksheet.write(f'B{row}', df_resumo.loc[row-2, 'TMO'], format_tmo_yellow)
            else:  # Acima da média
                worksheet.write(f'B{row}', df_resumo.loc[row-2, 'TMO'], format_tmo_red)

    buffer.seek(0)

    # Oferecer download
    st.download_button(
        label="Baixar Planilha",
        data=buffer,
        file_name="resumo_analistas_formatado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

