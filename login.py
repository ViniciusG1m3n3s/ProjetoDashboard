import streamlit as st


# Dicionário com usuários e senhas
usuarios = {"usuario@itau": "senha1", "usuario2@bv": "senha2", "sidnei@itau": "f1nch", "carol@itau": "f1nch", "leonardo@itau": "123", "viviane@bv": "f1nch", "raissa@maestro": "f1nch", "sidnei@oficios": "f1nch", "viviane_bv@bv": "finch"}

# Função para autenticar usuário
def autenticar(usuario, senha):
    return usuarios.get(usuario) == senha

# Função para carregar o dashboard dependendo do domínio do usuário
def login():
    st.logo("finch.png")
    usuario = st.sidebar.text_input("Usuário", placeholder="👤 Usuário", label_visibility="collapsed")
    senha = st.sidebar.text_input("Senha", type="password", placeholder="🔑 *********", label_visibility="collapsed")

    if st.sidebar.button("Entrar", icon=":material/login:", use_container_width=True, type="primary"):
        if autenticar(usuario, senha):
            st.session_state.logado = True
            st.session_state.usuario_logado = usuario    # Armazena o usuário logado
            st.sidebar.success("Login bem-sucedido!")
            return True  # Retorna True se o login for bem-sucedido
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

    background_image_css = """
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://i.imgur.com/wdWNqgq.png");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: rgba(0, 0, 0, 0.3); /* Adiciona uma camada de transparência escura */
    }
    header {
    background-color: rgba(255, 255, 255, 0); /* Torna o fundo do cabeçalho transparente */
    color: transparent; /* Remove o texto do cabeçalho (opcional) */
    box-shadow: none; /* Remove a sombra (opcional) */
    }
    [data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0); /* Transparente no novo identificador */
    }
    #     /* Aplica transparência com blur à sidebar */
    # [data-testid="stSidebar"] {
    #     background-color: rgba(128, 128, 128, 0.5); /* Cinza translucido */
    #     backdrop-filter: blur(1px); /* Efeito de desfoque */
    #     -webkit-backdrop-filter: blur(10px); /* Compatibilidade com navegadores Webkit */
    # }
    # </style>
    """
    st.markdown(background_image_css, unsafe_allow_html=True)
    
    
    return False  # Retorna False se o login falhar


