import streamlit as st
import requests
import os
import datetime
from PIL import Image
from scripts.interface_voz import falar, ouvir
from scripts.integracao_rag_voz import limpar_texto_para_voz

# 1. CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Contador IA - Assistente Digital", page_icon="📊", layout="wide")

# Caminho do Avatar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AVATAR_PATH = os.path.join(BASE_DIR, "assets", "avatar_assistente.png")

# Função para saudação dinâmica
def obter_saudacao():
    hora = datetime.datetime.now().hour
    if hora < 12: return "Bom dia"
    elif hora < 18: return "Boa tarde"
    else: return "Boa noite"

# Estilo CSS Personalizado (Laranja Itaú/UEMG Style)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 25px; height: 3.5em; background-color: #FF6200; color: white; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #e55a00; border: none; color: white; }
    .stTextInput>div>div>input { border-radius: 15px; }
    .sidebar-text { font-size: 14px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# 2. SIDEBAR - STATUS E KNOWLEDGE
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2641/2641409.png", width=80)
    st.title("Painel de Controle")
    st.success("🤖 API RAG: Online")
    st.info("📚 Base: PDFs Carregados")
    
    st.divider()
    st.markdown("**Bolsa ICT Itaú / UEMG**")
    st.caption("Projeto: Auditoria de Voz em Fluxos Contábeis")
    
    # Listagem de Pastas de Conhecimento (Rastreabilidade)
    st.markdown("### 📂 Repositório Local")
    path_k = os.path.join(BASE_DIR, "data", "knowledge")
    if os.path.exists(path_k):
        for pasta in os.listdir(path_k):
            st.caption(f"📁 {pasta}")

# 3. IDENTIFICAÇÃO DO USUÁRIO
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "saudacao_feita" not in st.session_state:
    st.session_state.saudacao_feita = False

# Tela de Login Inicial
if not st.session_state.nome_usuario:
    st.title("📊 Contador IA")
    nome = st.text_input("Olá! Para começarmos, qual o seu nome?", placeholder="Ex: Danilo")
    if st.button("Acessar Sistema"):
        if nome:
            st.session_state.nome_usuario = nome
            st.rerun()
        else:
            st.warning("Por favor, digite seu nome.")
    st.stop()

# 4. INTERFACE PRINCIPAL COM AVATAR
col_av, col_txt = st.columns([1, 3])

with col_av:
    if os.path.exists(AVATAR_PATH):
        st.image(Image.open(AVATAR_PATH), use_container_width=True)
    else:
        st.warning("Avatar não encontrado em /assets")

with col_txt:
    saudacao = f"{obter_saudacao()}, {st.session_state.nome_usuario}!"
    st.title(saudacao)
    intro = "Eu sou sua assistente contábil brasileira. Estou pronta para analisar seus PDFs de DRE, Balanço e Fiscal. Como posso ajudar hoje?"
    st.markdown(f"*{intro}*")
    
    # Boas vindas por VOZ (Apenas uma vez ao entrar)
    if not st.session_state.saudacao_feita:
        falar(f"{saudacao}. {intro}")
        st.session_state.saudacao_feita = True

# 5. CHAT E PROCESSAMENTO
st.divider()

# Exibe histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Botão de Voz e Input de Texto
col_v, col_i = st.columns([1, 4])

with col_v:
    if st.button("🎤 FALAR"):
        pergunta_voz = ouvir()
        if pergunta_voz:
            st.session_state.messages.append({"role": "user", "content": pergunta_voz})
            with st.chat_message("user"):
                st.markdown(pergunta_voz)
            
            # Consulta RAG
            with st.spinner("Analisando PDFs..."):
                try:
                    r = requests.post("http://localhost:8000/v1/rag/query", json={"question": pergunta_voz, "top_k": 1})
                    if r.status_code == 200:
                        dados = r.json()
                        resp = dados.get("answer", "Sem resposta.")
                        fonte = dados["chunks"][0].get("source", "Geral") if dados.get("chunks") else "Desconhecida"
                        
                        full_txt = f"**Fonte:** `{fonte}`\n\n{resp}"
                        st.session_state.messages.append({"role": "assistant", "content": full_txt})
                        
                        with st.chat_message("assistant"):
                            st.markdown(full_txt)
                        
                        falar(limpar_texto_para_voz(resp))
                    else:
                        st.error("Erro na API.")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")

with col_i:
    prompt = st.chat_input("Digite sua dúvida aqui...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Lógica de consulta (Opcional: replicar a lógica acima ou unificar em função)