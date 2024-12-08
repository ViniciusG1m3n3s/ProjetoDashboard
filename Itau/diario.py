import streamlit as st
import os
from datetime import datetime, timedelta, time
import plotly.graph_objects as go

# Função para carregar registros de indisponibilidade
def load_indisponibilidade(usuario):
    file_path = os.path.join('Itau', f'indisponibilidade_{usuario}.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            registros = [line.strip().split(',') for line in file.readlines()]
    else:
        registros = []
    return registros

# Função para salvar um novo registro de indisponibilidade
def save_indisponibilidade(usuario, data, inicio, fim):
    file_path = os.path.join('Itau', f'indisponibilidade_{usuario}.txt')
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(f"{data} {inicio},{data} {fim}\n")
# Função para exibir o gráfico de linha do tempo em um único eixo (08:00 às 18:00)

def painel_indisponibilidade_diaria_adaptado(registros):
    """
    Função para exibir o painel de indisponibilidade diária.
    Parâmetros:
    - registros: Lista de tuplas [(inicio, fim)], onde inicio e fim estão no formato '%Y-%m-%d %H:%M'.
    """
    # Ordenar registros por data e horário
    registros.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M'))

    # Base do eixo X (08:00 às 18:00)
    inicio_dia = time(8, 0)
    fim_dia = time(18, 0)

    # Agrupar registros por dia
    registros_por_dia = {}
    for inicio, fim in registros:
        inicio_dt = datetime.strptime(inicio, '%Y-%m-%d %H:%M')
        fim_dt = datetime.strptime(fim, '%Y-%m-%d %H:%M')
        dia = inicio_dt.date()
        if dia not in registros_por_dia:
            registros_por_dia[dia] = []
        registros_por_dia[dia].append((inicio_dt, fim_dt))

    # Criar a base do gráfico
    fig = go.Figure()

    # Adicionar registros de indisponibilidade por dia
    for dia, periodos in registros_por_dia.items():
        for inicio_dt, fim_dt in periodos:
            # Ajustar horários ao intervalo permitido (08:00 às 18:00)
            if inicio_dt.time() < inicio_dia:
                inicio_dt = inicio_dt.replace(hour=8, minute=0)
            if fim_dt.time() > fim_dia:
                fim_dt = fim_dt.replace(hour=18, minute=0)

            # Calcular os horários como valores no eixo X
            inicio_horas = (inicio_dt - inicio_dt.replace(hour=8, minute=0)).seconds / 3600
            fim_horas = (fim_dt - inicio_dt.replace(hour=8, minute=0)).seconds / 3600

            # Calcular o período de indisponibilidade em minutos
            duracao_minutos = int((fim_dt - inicio_dt).total_seconds() // 60)

            # Formatar o texto a ser exibido fora da barra
            periodo_texto = f"{inicio_dt.strftime('%H:%M')} - {fim_dt.strftime('%H:%M')}<br>({duracao_minutos} minutos)"
            # Adicionar traço horizontal para o período de indisponibilidade
            fig.add_trace(go.Scatter(
                x=[inicio_horas, fim_horas],  # Início e fim no eixo X
                y=[str(dia), str(dia)],  # Mesmo dia no eixo Y
                mode='lines',
                line=dict(color='red', width=22),  # Barra horizontal maior
                hovertemplate=f"{inicio_dt.strftime('%H:%M')} - {fim_dt.strftime('%H:%M')}<extra></extra>",
                showlegend=False
            ))

            # Adicionar o texto fora da barra
            fig.add_trace(go.Scatter(
                x=[(inicio_horas + fim_horas) / 2],  # Ponto central da barra no eixo X
                y=[str(dia)],  # Mesmo dia no eixo Y
                mode='text',
                text=[f"{periodo_texto}<br><br>&nbsp;<br><br>"],  # Texto com o período e duração
                textfont=dict(size=12, color="gray"),  # Texto em cinza para contraste
                showlegend=False
            ))

    # Configurações do layout
    fig.update_layout(
        title="Painel de Indisponibilidade Diária",
        xaxis=dict(
            title="Hora do Dia",
            range=[0, 10],  # De 08:00 (0 horas) a 18:00 (10 horas)
            tickvals=list(range(11)),  # Marcar ticks em cada hora
            ticktext=[f"{h+8}:00" for h in range(11)],  # De 08:00 a 18:00
            showgrid=True,
        ),
        yaxis=dict(
            title="Dias",
            showgrid=True,
            type="category",  # Para exibir os dias como categorias
            tickmode="linear",
            tickvals=[str(dia) for dia in registros_por_dia.keys()],
            ticktext=[str(dia) for dia in registros_por_dia.keys()],
        ),
        template="plotly_white",
        height=400  # Altura ajustada para comportar os textos
    )

    # Exibir o gráfico
    st.plotly_chart(fig)
    
# Função para calcular e exibir o gráfico de pizza com filtro de período
def exibir_grafico_pizza_com_periodo(registros, data_inicio, data_fim):
    # Tempo total do expediente diário (08:00 às 18:00)
    expediente_total_min = (18 - 8) * 60

    # Filtrar registros dentro do período selecionado
    registros_filtrados = [
        (inicio, fim) for inicio, fim in registros
        if data_inicio <= datetime.strptime(inicio.split(' ')[0], '%Y-%m-%d').date() <= data_fim
    ]

    # Cálculo de indisponibilidade por data
    tempo_indisponibilidade_por_dia = {}
    for inicio, fim in registros_filtrados:
        inicio_dt = datetime.strptime(inicio, '%Y-%m-%d %H:%M')
        fim_dt = datetime.strptime(fim, '%Y-%m-%d %H:%M')

        # Ajustar os horários para o intervalo permitido
        inicio_dt = max(inicio_dt, inicio_dt.replace(hour=8, minute=0))
        fim_dt = min(fim_dt, fim_dt.replace(hour=18, minute=0))

        # Calcula o tempo de indisponibilidade
        tempo_indisponibilidade = (fim_dt - inicio_dt).total_seconds() / 60
        data = inicio_dt.date()

        # Soma o tempo indisponível para cada dia
        tempo_indisponibilidade_por_dia[data] = tempo_indisponibilidade_por_dia.get(data, 0) + tempo_indisponibilidade

    # Dados para o gráfico
    total_indisponibilidade = sum(tempo_indisponibilidade_por_dia.values())
    dias_filtrados = (data_fim - data_inicio).days + 1
    total_trabalhado = (expediente_total_min * dias_filtrados) - total_indisponibilidade

    # Evitar valores negativos
    if total_trabalhado < 0:
        total_trabalhado = 0

    # Dados para o gráfico de pizza
    labels = ['Indisponibilidade', 'Trabalhado']
    values = [total_indisponibilidade, total_trabalhado]
    hovertemplate = []
    for label, value in zip(labels, values):
        hours, remainder = divmod(value, 60)
        minutes, _ = divmod(remainder, 1)
        if value > 260:
            hovertemplate.append(f'{label}: {int(hours):02d}:{int(minutes):02d} (%{{percent:.1f}}%)<br>')
        else:
            hovertemplate.append(f'{label}: {value:.0f} minutos (%{{percent:.1f}}%)<br>')
    total_trabalhado_str = f'{int(hours):02d}:{int(minutes):02d}'
    # Criar o gráfico de pizza
    custom_colors = ['#ff571c', '#7f2b0e', '#4c1908', '#ff884d', '#a34b28', '#331309']
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hovertemplate=hovertemplate,  # Exibe valor e porcentagem no hover
        textinfo='label+percent',  # Exibe apenas porcentagem no gráfico
        marker=dict(colors=custom_colors[:len(labels)]),
    )])
    fig.update_layout(title_text=f"Indisponibilidade ({data_inicio} a {data_fim})")

    st.plotly_chart(fig)
    
# Main app
def diario():
    if 'usuario_logado' not in st.session_state:
        st.session_state.usuario_logado = "usuario_teste"  # Usuário fictício para testes
    usuario_logado = st.session_state.usuario_logado

    st.header("Controle de Indisponibilidade Sistêmica")

    # Inputs de data e horário usando os widgets de Streamlit
    data = st.date_input("Data", value=datetime.now().date())
    col1, col2 = st.columns(2)
    with col1:
        inicio = st.time_input("Hora de Início", value=time(8, 0))
    with col2:
        fim = st.time_input("Hora de Fim", value=time(9, 0))

    if st.button("Salvar Registro"):
        try:
            if inicio < time(8, 0) or fim > time(18, 0) or inicio >= fim:
                st.error("Os horários devem estar entre 08:00 e 18:00 e o início deve ser antes do fim!")
            else:
                save_indisponibilidade(usuario_logado, data.strftime('%Y-%m-%d'), inicio.strftime('%H:%M'), fim.strftime('%H:%M'))
                st.success("Registro salvo com sucesso!")
                st.rerun()
        except ValueError:
            st.error("Erro ao salvar registro! Verifique os dados e tente novamente.")

    with st.container(border=True):
            registros = load_indisponibilidade(usuario_logado)
            if registros:
                st.subheader("Registros de Indisponibilidade")

                # Extrair todas as datas únicas
                datas_unicas = sorted(set(registro[0].split(' ')[0] for registro in registros))

                # Multiselect para escolher as datas para o gráfico de linha do tempo
                datas_selecionadas = st.multiselect(
                    "Selecione as datas para visualizar os registros:",
                    options=datas_unicas,
                    default=datas_unicas
                )

                # Filtrar registros pelas datas selecionadas
                registros_filtrados = [
                    registro for registro in registros
                    if registro[0].split(' ')[0] in datas_selecionadas
                ]

                if registros_filtrados:
                    # Exibir o gráfico de linha do tempo
                    painel_indisponibilidade_diaria_adaptado(registros_filtrados)
                else:
                    st.info("Nenhum registro encontrado para as datas selecionadas.")

    with st.container(border=True):
            st.subheader("Gráfico de Pizza por Período")

            col1, col2 = st.columns(2)
            with col1:
                periodo_inicio = st.date_input("Início do Período", value=datetime.now().date())
            with col2:
                periodo_fim = st.date_input("Fim do Período", value=datetime.now().date())

            if periodo_inicio > periodo_fim:
                st.error("A data de início não pode ser posterior à data de fim!")
            else:
                # Exibir o gráfico de pizza
                exibir_grafico_pizza_com_periodo(registros, periodo_inicio, periodo_fim)

