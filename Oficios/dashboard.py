import streamlit as st
import pandas as pd
from .calculations import calcular_produtividade_diaria, calcular_tmo_por_dia, convert_to_timedelta_for_calculations, convert_to_datetime_for_calculations, save_data, load_data, format_timedelta, calcular_ranking, calcular_filas_analista, calcular_metrica_analista, calcular_tmo_equipe, calcular_carteiras_analista, get_points_of_attention, calcular_tmo_por_carteira, calcular_tmo, calcular_e_exibir_tmo_por_fila, calcular_e_exibir_protocolos_por_fila, calcular_tmo_por_mes, exibir_tmo_por_mes, exibir_dataframe_tmo_formatado
from .charts import plot_produtividade_diaria, plot_tmo_por_dia, plot_status_pie, grafico_tmo, grafico_status_analista, exibir_grafico_filas_realizadas, exibir_grafico_tmo_por_dia
from datetime import datetime
import streamlit as st

def dashboard():
    st.title("Dashboard de Produtividade")
    
    # Carregar dados
    usuario_logado = st.session_state.usuario_logado
    df_total = load_data(usuario_logado)

    st.logo("finch.png")

    # Sidebar
    st.sidebar.header("Navegação")
    opcao_selecionada = st.sidebar.selectbox("Escolha uma visão", ["Visão Geral", "Métricas Individuais", "Diário de Bordo"])

    # Carregar nova planilha
    uploaded_file = st.sidebar.file_uploader("Carregar nova planilha", type=["xlsx"])

    if uploaded_file is not None:
        df_new = pd.read_excel(uploaded_file)
        df_total = pd.concat([df_total, df_new], ignore_index=True)
        save_data(df_total, usuario_logado)
        st.sidebar.success(f'Arquivo "{uploaded_file.name}" carregado com sucesso!')

    # Converte para cálculos temporários
    df_total = convert_to_timedelta_for_calculations(df_total)
    df_total = convert_to_datetime_for_calculations(df_total)

    custom_colors = ['#ff571c', '#7f2b0e', '#4c1908', '#ff884d', '#a34b28', '#331309']

    if opcao_selecionada == "Visão Geral":
        st.header("Visão Geral")

        # Filtros de data
        min_date = df_total['DATA DE CONCLUSÃO DA TAREFA'].min().date() if not df_total.empty else datetime.today().date()
        max_date = df_total['DATA DE CONCLUSÃO DA TAREFA'].max().date() if not df_total.empty else datetime.today().date()

        col1, col2 = st.columns(2)
        with col1:
            data_inicial = st.date_input("Data Inicial", min_date)
        with col2:
            data_final = st.date_input("Data Final", max_date)

        if data_inicial > data_final:
            st.sidebar.error("A data inicial não pode ser posterior à data final!")

        df_total = df_total[(df_total['DATA DE CONCLUSÃO DA TAREFA'].dt.date >= data_inicial) & (df_total['DATA DE CONCLUSÃO DA TAREFA'].dt.date <= data_final)]

        # Métricas de produtividade
        total_finalizados = len(df_total[df_total['SITUAÇÃO DA TAREFA'] == 'Finalizada'])
        total_reclass = len(df_total[df_total['SITUAÇÃO DA TAREFA'] == 'Cancelada'])
        
        # Verifique se o denominador não é zero
        if (total_finalizados + total_reclass) > 0:
            # Se houver cadastros finalizados ou reclassificados, calcula o tempo médio
            tempo_medio = (df_total[df_total['SITUAÇÃO DA TAREFA'] == 'Finalizada']['TEMPO MÉDIO OPERACIONAL'].sum() + 
                        df_total[df_total['SITUAÇÃO DA TAREFA'] == 'Cancelada']['TEMPO MÉDIO OPERACIONAL'].sum()) / (total_finalizados + total_reclass)
        else:
            # Se não houver cadastros finalizados ou reclassificados, define o tempo médio como zero ou outro valor padrão
            tempo_medio = pd.Timedelta(0)  # ou "0 min"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.metric("Total Geral", total_finalizados + total_reclass)
        with col2:
            with st.container(border=True):
                st.metric("Tarefas Finalizadas", total_finalizados)
        with col3:
            with st.container(border=True):
                st.metric("Tarefas Canceladas", total_reclass)
        with col4:
            with st.container(border=True):
                st.metric("Tempo Médio por Cadastro", format_timedelta(tempo_medio))     
        
        # Expander com Total Geral --- Sendo a soma de todos os cadastros, reclassificados e andamentos
        with st.expander("Tempo Médio por Fila"):
            df_tmo_por_carteira = calcular_tmo_por_carteira(df_total)
            if isinstance(df_tmo_por_carteira, str):
                st.write(df_tmo_por_carteira)  # Exibe mensagem de erro se as colunas não existirem
            else:
                st.dataframe(df_tmo_por_carteira, use_container_width=True, hide_index=True)

        # Calculando e exibindo gráficos
        df_produtividade = calcular_produtividade_diaria(df_total)
        
        df_tmo = calcular_tmo_por_dia(df_total)  # Certifique-se de que essa função retorne os dados necessários para o gráfico

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.subheader("Produtividade Diária")
                fig_produtividade = plot_produtividade_diaria(df_produtividade, custom_colors)
                if fig_produtividade:
                    st.plotly_chart(fig_produtividade)

        with col2:
            with st.container(border=True):
                st.subheader("TMO por Dia")
                fig_tmo = plot_tmo_por_dia(df_tmo, custom_colors)
                if fig_tmo:
                    st.plotly_chart(fig_tmo)
                    
        total_completa = len(df_total[df_total['FINALIZAÇÃO'] == 'Subsídio Completo'])
        total_parcial = len(df_total[df_total['FINALIZAÇÃO'] == 'Subsídio Parcial'])
        total_nao_tratada = len(df_total[df_total['FINALIZAÇÃO'] == 'Fora do Escopo'])
        
        with st.container(border=True):
            exibir_tmo_por_mes(df_total)
            # Exibir o DataFrame formatado na seção correspondente
            df_tmo_formatado = exibir_dataframe_tmo_formatado(df_total)

        with st.container(border=True):
            # Gráfico de Status
            st.subheader("Status de Produtividade")
            st.plotly_chart(plot_status_pie(df_total, 'FINALIZAÇÃO', custom_colors))            
            #Grafico de TMO por Analista
            df_tmo_analista = calcular_tmo(df_total)

        with st.container(border=True):
            # Filtro de analistas
            st.subheader("Tempo Médio Operacional por Analista")
            analistas = df_tmo_analista['USUÁRIO QUE CONCLUIU A TAREFA'].unique()
            selected_analistas = st.multiselect("Selecione os analistas", analistas, default=analistas)

            # Mostrar o gráfico de TMO
            df_tmo_analista_filtered = df_tmo_analista[df_tmo_analista['USUÁRIO QUE CONCLUIU A TAREFA'].isin(selected_analistas)]
            fig_tmo_analista = grafico_tmo(df_tmo_analista_filtered, custom_colors)
            if fig_tmo_analista:
                st.plotly_chart(fig_tmo_analista)  
            else:   
                st.write("Nenhum analista selecionado")
        
        with st.container(border=True):
            # Seleção de usuários para o ranking
            st.subheader("Ranking de Produtividade")
            
            # Selecione os usuários
            users = df_total['USUÁRIO QUE CONCLUIU A TAREFA'].unique()
            selected_users = st.multiselect("Selecione os usuários", users, default=users)
            
            # Calcular o ranking
            styled_df_ranking = calcular_ranking(df_total, selected_users)
            
            # Exibir a tabela de ranking
            st.dataframe(styled_df_ranking, width=2000)
            
    elif opcao_selecionada == "Métricas Individuais":
        st.header("Métricas Individuais")
        
        # Filtro de data
        st.subheader("Filtro por Data")
        min_date = df_total['DATA DE CONCLUSÃO DA TAREFA'].min().date() if not df_total.empty else datetime.today().date()
        max_date = df_total['DATA DE CONCLUSÃO DA TAREFA'].max().date() if not df_total.empty else datetime.today().date()

        col1, col2 = st.columns(2)
        with col1:
            data_inicial = st.date_input("Data Inicial", min_date)
        with col2:
            data_final = st.date_input("Data Final", max_date)

        if data_inicial > data_final:
            st.error("A data inicial não pode ser posterior à data final!")

        df_total = df_total[(df_total['DATA DE CONCLUSÃO DA TAREFA'].dt.date >= data_inicial) & (df_total['DATA DE CONCLUSÃO DA TAREFA'].dt.date <= data_final)]
        analista_selecionado = st.selectbox('Selecione o analista', df_total['USUÁRIO QUE CONCLUIU A TAREFA'].unique())
        df_analista = df_total[df_total['USUÁRIO QUE CONCLUIU A TAREFA'] == analista_selecionado].copy()

        # Chama as funções de cálculo
        total_finalizados_analista, total_reclass_analista, tempo_medio_analista = calcular_metrica_analista(df_analista)
        tmo_equipe = calcular_tmo_equipe(df_total)
        
        total_finalizados_analista, total_reclass_analista, tempo_medio_analista = calcular_metrica_analista(df_analista)

        # Define valores padrão caso as variáveis retornem como None
        if total_finalizados_analista is None:
            total_finalizados_analista = 0
        if total_reclass_analista is None:
            total_reclass_analista = 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.metric("Total Geral", total_finalizados_analista+total_reclass_analista)
        with col2:
            with st.container(border=True):
                st.metric("Tarefas Finalizadas", total_finalizados_analista)
        with col3:
            with st.container(border=True):
                st.metric("Tarefas Canceladas", total_reclass_analista)
        with col4:
            with st.container(border=True):
                if tempo_medio_analista is not None and tmo_equipe is not None:
                    st.metric(f"Tempo Médio por Cadastro", f"{format_timedelta(tempo_medio_analista)}")
                else:
                    st.metric(f"Tempo Médio por Cadastro", 'Nenhum dado encontrado')
        
        if tempo_medio_analista is not None and tmo_equipe is not None:
            if tempo_medio_analista > tmo_equipe:
                st.toast(f"O tempo médio de operação do analista {analista_selecionado} ({format_timedelta(tempo_medio_analista)}) excede o tempo médio da equipe ({format_timedelta(tmo_equipe)}).", icon="🚨")
            else:
                pass            
        # Agrupa por fila e calcula a quantidade e o TMO médio

        # Exibe o DataFrame estilizado com as filas realizadas pelo analista
        with st.container(border=True):
            calcular_e_exibir_tmo_por_fila(
                df_analista=df_analista, 
                analista_selecionado=analista_selecionado, 
                format_timedelta=format_timedelta, 
                st=st
            )

        # with st.container(border=True):
        #     calcular_e_exibir_protocolos_por_fila(
        #         df_analista=df_analista, 
        #         analista_selecionado=analista_selecionado, 
        #         format_timedelta=format_timedelta, 
        #         st=st
        #     )
                    
        # Gráficos de pizza usando as funções do `graph.py`
        col1, col2 = st.columns(2)
        
        total_completo_analista = len(df_analista[df_analista['FINALIZAÇÃO'] == 'Subsídio Completo'])
        total_parcial_analista = len(df_analista[df_analista['FINALIZAÇÃO'] == 'Subsídio Parcial'])
        total_fora_analista = len(df_analista[df_analista['FINALIZAÇÃO'] == 'Fora do Escopo'])
        
        with col1:
            with st.container(border=True):
                st.subheader(f"Status de Finalizações - {analista_selecionado}")
                fig_status = grafico_status_analista(df_analista, 'FINALIZAÇÃO', 'USUÁRIO QUE CONCLUIU A TAREFA', custom_colors)
                st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            with st.container(border=True):
                st.subheader(f"Filas Realizadas por - {analista_selecionado}")                    
                exibir_grafico_filas_realizadas(
                    df_analista=df_analista,
                    analista_selecionado=analista_selecionado,
                    custom_colors=custom_colors,
                    st=st
                )

        # Gráfico de TMO por dia usando a função do `graph.py`
        with st.container(border=True):
            st.subheader(f"Tempo Médio Operacional por Dia do Analista - {analista_selecionado}")
            exibir_grafico_tmo_por_dia(
            df_analista=df_analista,
            analista_selecionado=analista_selecionado,
            calcular_tmo_por_dia=calcular_tmo_por_dia,
            custom_colors=custom_colors,
            st=st
        )

    if st.sidebar.button("Logout", icon=":material/logout:"):
        st.session_state.logado = False
        st.session_state.usuario_logado = None
        st.sidebar.success("Desconectado com sucesso!")
        st.rerun()  # Volta para a tela de login

if __name__ == "__main__":
    dashboard()
