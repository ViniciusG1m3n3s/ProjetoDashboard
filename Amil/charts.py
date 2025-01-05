import plotly.express as px
import os
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
import altair as alt

def plot_produtividade_diaria(df_produtividade, custom_colors):
    if df_produtividade.empty or 'Dia' not in df_produtividade.columns or 'Produtividade' not in df_produtividade.columns:
        st.warning("Não há dados para exibir no gráfico de produtividade diária.")
    else:
        fig_produtividade = px.line(
                        df_produtividade,
                        x='Dia',
                        y='Produtividade',
                        color_discrete_sequence=custom_colors,
                        labels={'Produtividade': 'Total de Cadastros'},
                        line_shape='linear',
                        markers=True
                    )
        fig_produtividade.update_traces(
                        hovertemplate='Dia = %{x|%d/%m/%Y}<br>Produtividade = %{y}'
                    )
        st.plotly_chart(fig_produtividade)
        
def plot_produtividade_diaria_cadastros(df_produtividade_cadastro, custom_colors):
    if df_produtividade_cadastro.empty or 'Dia' not in df_produtividade_cadastro.columns or 'Produtividade' not in df_produtividade_cadastro.columns:
        st.warning("Não há dados para exibir no gráfico de produtividade diária.")
    else:
        fig_produtividade = px.line(
                        df_produtividade_cadastro,
                        x='Dia',
                        y='Produtividade',
                        color_discrete_sequence=custom_colors,
                        labels={'Produtividade': 'Total de Cadastros'},
                        line_shape='linear',
                        markers=True
                    )
        fig_produtividade.update_traces(
                        hovertemplate='Dia = %{x|%d/%m/%Y}<br>Produtividade = %{y}'
                    )
        st.plotly_chart(fig_produtividade)

def plot_tmo_por_dia(df_tmo, custom_colors):
    if df_tmo.empty or 'Dia' not in df_tmo.columns or 'TMO' not in df_tmo.columns:
        st.warning("Não há dados para exibir no gráfico de TMO por dia.")
        return None

    # Garantir que não existam NaN ou valores inválidos na coluna 'TMO'
    df_tmo = df_tmo.dropna(subset=['TMO'])

    # Verificar e formatar a coluna TMO como minutos e segundos
    df_tmo['TMO_Formatado'] = df_tmo['TMO'].apply(
        lambda x: f"{int(x.total_seconds() // 60):02}:{int(x.total_seconds() % 60):02}" if pd.notnull(x) else "00:00"
    )

    # Criar o gráfico de linhas
    fig_tmo_linha = px.line(
        df_tmo,
        x='Dia',
        y=df_tmo['TMO'].dt.total_seconds() / 60,  # Converter TMO para minutos
        labels={'y': 'Tempo Médio Operacional (min)', 'Dia': 'Data'},
        color_discrete_sequence=custom_colors,
        line_shape='linear',
        markers=True
    )

    fig_tmo_linha.update_layout(
        xaxis=dict(
            tickvals=df_tmo['Dia'],
            ticktext=[f"{dia.day}/{dia.month}/{dia.year}" for dia in df_tmo['Dia']]
        )
    )

    # Personalizar o hover e exibir o gráfico
    fig_tmo_linha.update_traces(
        text=df_tmo['TMO_Formatado'],
        textposition='top center',
        hovertemplate='Data = %{x|%d/%m/%Y}<br>TMO = %{text}'
    )
    return fig_tmo_linha

def plot_tmo_por_dia_cadastro(df_tmo_cadastro, custom_colors):
    if df_tmo_cadastro.empty or 'Dia' not in df_tmo_cadastro.columns or 'TMO' not in df_tmo_cadastro.columns:
        st.warning("Não há dados para exibir no gráfico de TMO por dia.")
        return None

    if isinstance(df_tmo_cadastro['TMO'].iloc[0], str):
        df_tmo_cadastro['TMO'] = pd.to_timedelta(df_tmo_cadastro['TMO'].apply(lambda x: x.replace(' min', 'm').replace('s', 's')))
    
    df_tmo_cadastro['TMO_Formatado'] = df_tmo_cadastro['TMO'].apply(lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}")
    
    fig_tmo_linha = px.line(
        df_tmo_cadastro,
        x='Dia',
        y=df_tmo_cadastro['TMO'].dt.total_seconds() / 60,  # Converte TMO para minutos
        labels={'y': 'Tempo Médio Operacional (min)', 'Dia': 'Data'},
        color_discrete_sequence=custom_colors,
        line_shape='linear',
        markers=True
    )
    
    fig_tmo_linha.update_layout(
        xaxis=dict(
            tickvals=df_tmo_cadastro['Dia'],
            ticktext=[f"{dia.day}/{dia.month}/{dia.year}" for dia in df_tmo_cadastro['Dia']]
    )
)
    
    fig_tmo_linha.update_traces(
        text=df_tmo_cadastro['TMO_Formatado'],
        textposition='top center',
        hovertemplate='Data = %{x|%d/%m/%Y}<br>TMO = %{text}'
    )

    return fig_tmo_linha

def plot_status_pie(total_parcial, total_nao_tratada, total_completa, custom_colors):
    fig_status = px.pie(
        names=['Subsídio Parcial', 'Fora do Escopo', 'Subsídio Completo'],
        values=[total_parcial, total_nao_tratada, total_completa],
        color_discrete_sequence=custom_colors
    )
    fig_status.update_traces(
        hovertemplate='Tarefas %{label} = %{value}<extra></extra>',
    )
    fig_status.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    return fig_status

# Função para gerar o gráfico de TMO por analista
def grafico_tmo(df_tmo_analista, custom_colors):
    # Gráfico de barras de TMO por analista em minutos
    fig_tmo_analista = px.bar(
        df_tmo_analista,
        x='USUÁRIO QUE CONCLUIU A TAREFA',
        y=df_tmo_analista['TMO'].dt.total_seconds() / 60,  # TMO em minutos
        labels={'y': 'Tempo Médio Operacional (min)', 'x': 'Analista', 'USUÁRIO QUE CONCLUIU A TAREFA': 'Analista'},
        text=df_tmo_analista['TMO_Formatado'],
        color_discrete_sequence=custom_colors
    )
    fig_tmo_analista.update_traces(
        textposition='outside',  # Exibe o tempo formatado fora das barras
        hovertemplate='Analista = %{x}<br>TMO = %{text}<extra></extra>',
        text=df_tmo_analista['TMO_Formatado']
    )
    return fig_tmo_analista

def grafico_status_analista(total_parcial_analista, total_fora_analista, total_completo_analista, custom_colors):
    fig_status = px.pie(
        names=['Subsídio Parcial', 'Fora do Escopo', 'Subsídio Completo'],
        values=[total_parcial_analista, total_fora_analista, total_completo_analista],
        color_discrete_sequence=custom_colors
    )
    fig_status.update_traces(
        hovertemplate='Tarefas %{label} = %{value}<extra></extra>',
    )
    fig_status.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    return fig_status

import plotly.express as px

def exibir_grafico_filas_realizadas(df_analista, analista_selecionado, custom_colors, st):
    """
    Gera e exibe um gráfico de pizza com as filas realizadas por um analista específico.

    Parâmetros:
        - df_analista: DataFrame contendo os dados de análise.
        - analista_selecionado: Nome do analista selecionado.
        - custom_colors: Lista de cores personalizadas para o gráfico.
        - st: Referência para o módulo Streamlit (necessário para exibir os resultados).
    ""
    """

    if 'FILA' in df_analista.columns:
        # Contar a quantidade de tarefas por fila
        filas_feitas_analista = df_analista['FILA'].dropna().value_counts().reset_index()
        filas_feitas_analista.columns = ['Tarefa', 'Quantidade']

        # Criar o gráfico de pizza
        fig_filas_feitas_analista = px.pie(
            names=filas_feitas_analista['Tarefa'],
            values=filas_feitas_analista['Quantidade'],
            color_discrete_sequence=custom_colors
        )

        # Personalizar o hover e layout do gráfico
        fig_filas_feitas_analista.update_traces(
            hovertemplate='Tarefas %{label} = %{value}<extra></extra>',
        )

        fig_filas_feitas_analista.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )

        # Exibir o gráfico na dashboard
        st.plotly_chart(fig_filas_feitas_analista)
    else:
        st.write("A coluna 'FILA' não foi encontrada no dataframe.")
        
def format_timedelta_Chart(td):
    """
    Formata um objeto Timedelta em uma string no formato 'X min Y s'.

    Parâmetros:
        - td: Timedelta a ser formatado.
    """
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes} min {seconds}s"


def exibir_grafico_tmo_por_dia(df_analista, analista_selecionado, calcular_tmo_por_dia, custom_colors, st):
    """
    Gera e exibe um gráfico de barras com o Tempo Médio Operacional (TMO) por dia para um analista específico.

    Parâmetros:
        - df_analista: DataFrame contendo os dados de análise.
        - analista_selecionado: Nome do analista selecionado.
        - calcular_tmo_por_dia: Função que calcula o TMO por dia.
        - custom_colors: Lista de cores personalizadas para o gráfico.
        - st: Referência para o módulo Streamlit (necessário para exibir os resultados).
    """

    # Calcular o TMO por dia
    df_tmo_analista = calcular_tmo_por_dia(df_analista)

    # Converter a coluna "TMO" (Timedelta) para minutos e segundos
    df_tmo_analista['TMO_segundos'] = df_tmo_analista['TMO'].dt.total_seconds()
    df_tmo_analista['TMO_minutos'] = df_tmo_analista['TMO_segundos'] / 60

    # Formatar TMO para exibição como "X min Y s"
    df_tmo_analista['TMO_formatado'] = df_tmo_analista['TMO'].apply(format_timedelta_Chart)

    # Criar o gráfico de barras
    fig_tmo_analista = px.bar(
        df_tmo_analista, 
        x='Dia', 
        y='TMO_minutos', 
        labels={'TMO_minutos': 'TMO (min)', 'Dia': 'Dia'},
        text=df_tmo_analista['TMO_formatado'],  # Exibe o tempo formatado nas barras
        color_discrete_sequence=custom_colors
    )
    
    fig_tmo_analista.update_layout(
        xaxis=dict(
            tickvals=df_tmo_analista['Dia'],
            ticktext=[f"{dia.day}/{dia.month}/{dia.year}" for dia in df_tmo_analista['Dia']]
        )
    )

    # Personalizar o gráfico
    fig_tmo_analista.update_traces(
        hovertemplate='Data = %{x}<br>TMO = %{text}',  # Formato do hover
        textfont_color='white'  # Define a cor do texto como branco
    )

    # Exibir o gráfico na dashboard
    st.plotly_chart(fig_tmo_analista)

def exibir_grafico_quantidade_por_dia(df_analista, analista_selecionado, custom_colors, st):
    """
    Gera e exibe um gráfico de barras com a quantidade de tarefas realizadas por dia para um analista específico.

    Parâmetros:
        - df_analista: DataFrame contendo os dados de análise.
        - analista_selecionado: Nome do analista selecionado.
        - custom_colors: Lista de cores personalizadas para o gráfico.
        - st: Referência para o módulo Streamlit (necessário para exibir os resultados).
    """

    # Agrupar os dados por dia e contar a quantidade de tarefas realizadas
    df_quantidade_analista = df_analista.groupby(df_analista['DATA DE CONCLUSÃO DA TAREFA'].dt.date).size().reset_index(name='Quantidade')
    df_quantidade_analista = df_quantidade_analista.rename(columns={'DATA DE CONCLUSÃO DA TAREFA': 'Dia'})

    # Criar o gráfico de barras
    fig_quantidade_analista = px.bar(
        df_quantidade_analista, 
        x='Dia', 
        y='Quantidade', 
        labels={'Quantidade': 'Quantidade de Tarefas', 'Dia': 'Data'},
        text='Quantidade',  # Exibe a quantidade nas barras
        color_discrete_sequence=custom_colors
    )
    
    fig_quantidade_analista.update_layout(
        xaxis=dict(
            tickvals=df_quantidade_analista['Dia'],
            ticktext=[f"{dia.day}/{dia.month}/{dia.year}" for dia in df_quantidade_analista['Dia']],
            title='Data'
        ),
        yaxis=dict(
            title='Quantidade de Tarefas'
        ),
        bargap=0.2  # Espaçamento entre as barras
    )

    # Personalizar o gráfico
    fig_quantidade_analista.update_traces(
        hovertemplate='Data = %{x}<br>Quantidade = %{y}',  # Formato do hover
        textfont_color='white'  # Define a cor do texto como branco
    )

    # Exibir o gráfico na dashboard
    st.plotly_chart(fig_quantidade_analista)
