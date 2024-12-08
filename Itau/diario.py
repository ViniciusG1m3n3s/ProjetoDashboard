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
    registros.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M'))

    inicio_dia = time(8, 0)
    fim_dia = time(18, 0)

    registros_por_dia = {}
    for inicio, fim in registros:
        inicio_dt = datetime.strptime(inicio, '%Y-%m-%d %H:%M')
        fim_dt = datetime.strptime(fim, '%Y-%m-%d %H:%M')
        dia = inicio_dt.date()
        if dia not in registros_por_dia:
            registros_por_dia[dia] = []
        registros_por_dia[dia].append((inicio_dt, fim_dt))

    fig = go.Figure()

    for dia, periodos in registros_por_dia.items():
        for inicio_dt, fim_dt in periodos:
            if inicio_dt.time() < inicio_dia:
                inicio_dt = inicio_dt.replace(hour=8, minute=0)
            if fim_dt.time() > fim_dia:
                fim_dt = fim_dt.replace(hour=18, minute=0)

            inicio_horas = (inicio_dt - inicio_dt.replace(hour=8, minute=0)).seconds / 3600
            fim_horas = (fim_dt - inicio_dt.replace(hour=8, minute=0)).seconds / 3600

            duracao_minutos = int((fim_dt - inicio_dt).total_seconds() // 60)

            periodo_texto = f"{inicio_dt.strftime('%H:%M')} - {fim_dt.strftime('%H:%M')}<br>({duracao_minutos} minutos)"
            fig.add_trace(go.Scatter(
                x=[inicio_horas, fim_horas],
                y=[str(dia), str(dia)],
                mode='lines',
                line=dict(color='red', width=22),
                hovertemplate=f"{inicio_dt.strftime('%H:%M')} - {fim_dt.strftime('%H:%M')}<extra></extra>",
                showlegend=False
            ))

            fig.add_trace(go.Scatter(
                x=[(inicio_horas + fim_horas) / 2],
                y=[str(dia)],
                mode='text',
                text=[f"{periodo_texto}<br><br>&nbsp;<br><br>"],
                textfont=dict(size=12, color="gray"),
                showlegend=False
            ))

    fig.update_layout(
        title="Painel de Indisponibilidade Diária",
        xaxis=dict(
            title="Hora do Dia",
            range=[0, 10],
            tickvals=list(range(11)),
            ticktext=[f"{h+8}:00" for h in range(11)],
            showgrid=True,
        ),
        yaxis=dict(
            title="Dias",
            showgrid=True,
            type="category",
            tickmode="linear",
            tickvals=[str(dia) for dia in registros_por_dia.keys()],
            ticktext=[str(dia) for dia in registros_por_dia.keys()],
        ),
        template="plotly_white",
        height=450 
    )

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
    
    # Converter valores para horas e minutos e criar rótulos detalhados
    formatted_values = []
    for label, value in zip(labels, values):
        hours, minutes = divmod(value, 60)
        formatted_values.append(f"{label}: {int(hours)}h {int(minutes)}m")

    # Criar o gráfico de pizza
    custom_colors = ['#ff571c', '#7f2b0e']
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hoverinfo="label+percent",  # Exibe o rótulo e porcentagem no hover
        text=formatted_values,  # Exibe os rótulos detalhados no gráfico
        textinfo='text',  # Exibe apenas o texto customizado
        marker=dict(colors=custom_colors[:len(labels)]),
    )])
    fig.update_layout(
        title_text=f"Indisponibilidade ({data_inicio} a {data_fim})",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )

    st.plotly_chart(fig)
    
def load_diario(usuario):
    file_path = f'diario_bordo_{usuario}.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            anotacoes = file.readlines()
    else:
        anotacoes = []
    return [anotacao.strip() for anotacao in anotacoes]

def save_anotacao(usuario, anotacao):
    file_path = f'diario_bordo_{usuario}.txt'
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M')} - {anotacao}\n")

def update_anotacoes(usuario, anotacoes):
    file_path = f'diario_bordo_{usuario}.txt'
    with open(file_path, 'w', encoding='utf-8') as file:
        for anotacao in anotacoes:
            file.write(f"{anotacao}\n")

# Main app
def diario():
    usuario_logado = st.session_state.usuario_logado  # Obtém o usuário logado
    # Carregar anotações anteriores
    anotacoes = load_diario(usuario_logado)

    # Área para adicionar uma nova anotação
    with st.container():
        st.subheader("Nova Anotação")
        nova_anotacao = st.text_area("Escreva sua anotação aqui...")

        if st.button(":material/check_circle: Salvar"):
            if nova_anotacao.strip():
                save_anotacao(usuario_logado, nova_anotacao)
                st.success("Anotação salva com sucesso!")
                st.rerun()  # Recarrega a p gina para exibir a nova anota o
            else:
                st.error("A anotação não pode estar vazia!")

    # Exibir e permitir edição das anotações anteriores
    with st.expander("📚 Anotações Anteriores", expanded=True):
        if anotacoes:
            edit_index = st.session_state.get('edit_index', -1)
            for idx, anotacao in enumerate(anotacoes):
                # Layout com `st.info` e botões lado a lado
                with st.container():
                        st.info(anotacao)
                col1, col2 = st.columns([0.1, 0.9])  # col1 tem 10% e col2 tem 90% do espaço
                with col1:
                    if st.button(":material/edit_document: Editar", key=f"edit_button_{idx}"):                         
                        st.session_state.edit_index = idx
                        st.rerun()
                with col2:
                    if st.button(":material/delete: Excluir", key=f"delete_button_{idx}"):  # Botão Excluir
                        anotacoes.pop(idx)
                        update_anotacoes(usuario_logado, anotacoes)
                        st.success("Anotação excluída com sucesso!")
                        st.rerun()
                # Modo de edição
                if idx == edit_index:
                    st.text_area("Editar Anotação", value=anotacao, key=f"edit_{idx}", on_change=None)
                    col1, col2 = st.columns([0.1, 0.9])  # col1 tem 10% e col2 tem 90% do espaço
                    with col1:
                        if st.button(":material/check_circle: Salvar", key=f"save_{idx}"):
                            anotacoes[idx] = st.session_state.get(f"edit_{idx}", anotacao)
                            update_anotacoes(usuario_logado, anotacoes)
                            st.success("Anotação editada com sucesso!")
                            st.session_state.edit_index = -1  # Sair do modo de edição
                            st.rerun()
                    with col2:
                        if st.button(":material/close: Cancelar", key=f"cancel_{idx}"):
                            st.session_state.edit_index = -1  # Sair do modo de edição
                            st.rerun()
        else:
            st.info("Nenhuma anotação encontrada.")
        
    if 'usuario_logado' not in st.session_state:
        st.session_state.usuario_logado = usuario_logado  # Usuário fictício para testes
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
    col1, col2 = st.columns(2)
    
    with col1:
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

    with col2:
        with st.container(border=True):
            st.subheader("Porcentagem de Indisponibilidade")

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

