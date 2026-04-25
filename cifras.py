# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re
import io

# -------------------------------------------------
# CONFIGURAÇÃO
# -------------------------------------------------
st.set_page_config(page_title="Music Book Pro", layout="wide")

# Inicialização do Estado (Crucial para Reatividade)
if "book" not in st.session_state:
    st.session_state.book = []
if "musica_focada" not in st.session_state:
    st.session_state.musica_focada = 0

# -------------------------------------------------
# FUNÇÕES DE APOIO
# -------------------------------------------------
def processar_texto(texto, semitons, colunas):
    # (Mantenha sua lógica de transposição aqui)
    # Exemplo simplificado para o teste de fonte:
    return texto 

def verificar_limite_a4(texto, tamanho_fonte):
    # Aproximação: em fonte Courier, cada caractere tem ~0.6 do tamanho da fonte
    # Largura A4 útil é ~180mm. 1pt = 0.3527mm.
    largura_caractere_mm = (tamanho_fonte * 0.3527) * 0.6
    limite_caracteres = int(180 / largura_caractere_mm)
    
    linhas = texto.split('\n')
    maior_linha = max([len(l) for l in linhas]) if linhas else 0
    return maior_linha > limite_caracteres, limite_caracteres

# -------------------------------------------------
# SIDEBAR (CONTROLES)
# -------------------------------------------------
st.sidebar.title("Configurações")

if st.session_state.book:
    idx = st.sidebar.selectbox("Editar Música:", 
                               range(len(st.session_state.book)), 
                               format_func=lambda x: st.session_state.book[x]['titulo'])
    st.session_state.musica_focada = idx
    
    # Referência direta para facilitar
    m = st.session_state.book[idx]
    
    st.sidebar.subheader("Ajustes de Exibição")
    # Usamos o on_change para garantir que o Streamlit saiba que houve mudança
    m["fonte"] = st.sidebar.slider("Tamanho da Letra (pt)", 6, 30, m["fonte"])
    m["tom"] = st.sidebar.number_input("Transpor Tom", -12, 12, m["tom"])
    m["cols"] = st.sidebar.radio("Layout", ["1 Coluna", "2 Colunas"], 
                                 index=0 if m["cols"] == "1 Coluna" else 1)
else:
    st.sidebar.info("Adicione uma música para editar.")

# -------------------------------------------------
# VISUAL BOOK (O PREVIEW)
# -------------------------------------------------
st.header("📖 Visual Book")

if st.session_state.book:
    musica = st.session_state.book[st.session_state.musica_focada]
    
    # Processamento
    texto_final = processar_texto(musica["conteudo"], musica["tom"], musica["cols"])
    estourou, limite = verificar_limite_a4(texto_final, musica["fonte"])
    
    # Alerta visual se passar da margem
    if estourou:
        st.error(f"⚠️ A LINHA ESTÁ FORA DA MARGEM A4! (Máximo para {musica['fonte']}pt: {limite} caracteres)")
    else:
        st.success(f"✅ Dentro da margem A4 ({limite} caracteres por linha).")

    # CSS Dinâmico injetado na hora para garantir a mudança de fonte
    # Usamos f-string para passar o valor exato de musica["fonte"]
    estilo_dinamico = f"""
    <style>
        .folha-a4 {{
            background: white;
            color: black;
            padding: 40px;
            border: 2px solid {'#ff4b4b' if estourou else '#333'};
            font-family: 'Courier New', Courier, monospace;
            line-height: 1.2;
            white-space: pre;
            overflow-x: auto;
            font-size: {musica['fonte']}pt !important;
        }}
    </style>
    """
    st.markdown(estilo_dinamico, unsafe_allow_html=True)
    
    # Renderização da folha
    st.markdown(f'<div class="folha-a4">{texto_final}</div>', unsafe_allow_html=True)

# -------------------------------------------------
# ÁREA DE ADIÇÃO (SIMPLIFICADA PARA TESTE)
# -------------------------------------------------
with st.expander("➕ Adicionar Nova Música"):
    novo_tit = st.text_input("Título")
    novo_txt = st.text_area("Cifra")
    if st.button("Salvar"):
        st.session_state.book.append({
            "titulo": novo_tit, 
            "conteudo": novo_txt, 
            "fonte": 12, 
            "tom": 0, 
            "cols": "1 Coluna"
        })
        st.rerun()
