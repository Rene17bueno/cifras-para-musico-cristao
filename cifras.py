# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from docx import Document
from docx.shared import Pt, Inches
import io
import re
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Music Book Pro", page_icon="🎸", layout="wide")

st.markdown("""
    <style>
    textarea, pre, .cifra-renderizada {
        font-family: 'Courier New', Courier, monospace !important;
        white-space: pre !important;
        word-wrap: normal !important;
    }
    .stButton > button { width: 100%; border-radius: 5px; }
    .page-container {
        background-color: #0e1117;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #333;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .page-break-line {
        border-top: 2px dashed #ff4b4b;
        margin: 25px 0;
        position: relative;
    }
    .page-break-line::after {
        content: "CORTE DA PÁGINA (A4)";
        position: absolute;
        right: 0;
        top: -20px;
        font-size: 10px;
        color: #ff4b4b;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if 'book' not in st.session_state: st.session_state.book = []
if 'limpador' not in st.session_state: st.session_state.limpador = 0
if 'temp_titulo' not in st.session_state: st.session_state.temp_titulo = ""
if 'temp_conteudo' not in st.session_state: st.session_state.temp_conteudo = ""
if 'tom_ajuste' not in st.session_state: st.session_state.tom_ajuste = 0
if 'fonte_global' not in st.session_state: st.session_state.fonte_global = 11
if 'modo_colunas' not in st.session_state: st.session_state.modo_colunas = "1 Coluna"

# --- LÓGICA DE TRANSPOSIÇÃO E PROCESSAMENTO ---
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def transpor_acorde(acorde, semitons):
    def substituir(match):
        nota_original = match.group(1)
        acessorio = match.group(2)
        if nota_original in NOTAS:
            idx = (NOTAS.index(nota_original) + semitons) % 12
            return NOTAS[idx] + acessorio
        return match.group(0)
    return re.sub(r'([A-G]#?)([^A-G\s]*)', substituir, acorde)

def processar_texto(texto, semitons, colunas):
    if not texto: return ""
    linhas = texto.split('\n')
    linhas_transpostas = []
    for linha in linhas:
        nova_linha = ""
        pos = 0
        for m in re.finditer(r'\S+', linha):
            nova_linha += " " * (m.start() - pos) + transpor_acorde(m.group(), semitons)
            pos = m.start() + len(m.group())
        linhas_transpostas.append(nova_linha + (" " * (len(linha) - pos)))

    if colunas == "2 Colunas":
        meio = (len(linhas_transpostas) // 2) + (len(linhas_transpostas) % 2)
        col_esq = linhas_transpostas[:meio]
        col_dir = linhas_transpostas[meio:]
        larg_max = max([len(l) for l in col_esq]) if col_esq else 0
        final = []
        for i in range(max(len(col_esq), len(col_dir))):
            e = col_esq[i] if i < len(col_esq) else ""
            d = col_dir[i] if i < len(col_dir) else ""
            final.append(f"{e.ljust(larg_max + 8)}{d}")
        return "\n".join(final)
    return "\n".join(linhas_transpostas)

def buscar_cifra(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        titulo = (soup.find('h1', class_='t1') or soup.find('h1', class_='t3') or soup.find('h1')).get_text().strip()
        conteudo = soup.find('pre').get_text()
        return titulo, conteudo
    except: return "", ""

# --- SIDEBAR (MENU LATERAL) ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

st.sidebar.divider()
st.sidebar.markdown("### 🛠️ Controles de Cifra")

# 1. Tamanho da Letra
st.sidebar.write("Tamanho da Letra:")
c_f1, c_f2, c_f3 = st.sidebar.columns([1, 1, 1])
if c_f1.button("A-"): st.session_state.fonte_global -= 1
if c_f2.button("11"): st.session_state.fonte_global = 11
if c_f3.button("A+"): st.session_state.fonte_global += 1
st.sidebar.caption(f"Atual: **{st.session_state.fonte_global}pt**")

# 2. Transposição (Tom)
st.sidebar.write("Ajuste de Tom:")
c_t1, c_t2, c_t3 = st.sidebar.columns(3)
if c_t1.button("♭"): st.session_state.tom_ajuste -= 1
if c_t2.button("0 "): st.session_state.tom_ajuste = 0
if c_t3.button("♯"): st.session_state.tom_ajuste += 1
st.sidebar.caption(f"Semitons: {st.session_state.tom_ajuste}")

# 3. Colunas
st.sidebar.write("Colunas:")
c_c1, c_c2 = st.sidebar.columns(2)
if c_c1.button("📄 1"): st.session_state.modo_colunas = "1 Coluna"
if c_c2.button("✂️ 2"): st.session_state.modo_colunas = "2 Colunas"
st.sidebar.caption(f"Layout: {st.session_state.modo_colunas}")

# Injeta CSS Global para respeitar a fonte da Sidebar
st.markdown(f"<style>textarea, .cifra-renderizada, .page-container {{ font-size: {st.session_state.fonte_global}pt !important; }}</style>", unsafe_allow_html=True)

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Capturar Nova Cifra")
    url = st.text_input("Link da cifra:", key=f"url_{st.session_state.limpador}")
    if st.button("Capturar Dados"):
        t, c = buscar_cifra(url)
        st.session_state.temp_titulo, st.session_state.temp_conteudo = t, c
        st.rerun()

    st.divider()
    tit = st.text_input("Título:", value=st.session_state.temp_titulo)
    conteudo_view = processar_texto(st.session_state.temp_conteudo, st.session_state.tom_ajuste, st.session_state.modo_colunas)
    cif = st.text_area("Cifra (Editável):", value=conteudo_view, height=450)
    
    if st.button("✅ Salvar Música no Book"):
        # Salva o conteúdo final e o tamanho que estava na sidebar naquele momento
        st.session_state.book.append({
            "titulo": tit, 
            "conteudo": cif, 
            "tamanho_fonte": st.session_state.fonte_global
        })
        st.success("Salvo com sucesso!")
        time.sleep(0.5)
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""; st.session_state.limpador += 1
        st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Visualização do Repertório")
    if not st.session_state.book:
        st.info("Nenhuma música no book.")
    else:
        # Linhas por página baseada na fonte global da sidebar
        linhas_por_pagina = int(720 / (st.session_state.fonte_global * 1.3))
        
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']}", expanded=True):
                # O texto exibido reage aos botões de Tom e Coluna na Sidebar
                texto_final = processar_texto(m['conteudo'], st.session_state.tom_ajuste, st.session_state.modo_colunas)
                linhas = texto_final.split('\n')
                
                st.markdown('<div class="page-container">', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size: 1.4em; font-weight: bold; margin-bottom: 15px;">{m["titulo"]}</div>', unsafe_allow_html=True)
                
                bloco = ""
                for idx, linha in enumerate(linhas):
                    l_html = linha.replace(" ", "&nbsp;")
                    bloco += f'<div class="cifra-renderizada">{l_html if l_html != "" else "&nbsp;"}</div>'
                    if (idx + 1) % linhas_por_pagina == 0 and (idx + 1) < len(linhas):
                        bloco += '<div class="page-break-line"></div>'
                
                st.markdown(bloco, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button(f"🗑️ Excluir", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar Livro")
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        nome_arq = st.text_input("Nome do arquivo:", "Livro_de_Cifras")
        st.info(f"O arquivo será gerado com o tamanho **{st.session_state.fonte_global}pt** e layout de **{st.session_state.modo_colunas}**.")
        
        c1, c2 = st.columns(2)
        with c1:
            doc = Document()
            for i, m in enumerate(st.session_state.book):
                if i > 0: doc.add_page_break()
                doc.add_heading(m['titulo'], 1)
                txt = processar_texto(m['conteudo'], st.session_state.tom_ajuste, st.session_state.modo_colunas)
                run = doc.add_paragraph().add_run(txt)
                run.font.name = 'Courier New'
                run.font.size = Pt(st.session_state.fonte_global)
            buf = io.BytesIO(); doc.save(buf)
            st.download_button("📥 Baixar Word", buf.getvalue(), f"{nome_arq}.docx")
        with c2:
            if st.button("Gerar PDF"):
                pdf = FPDF()
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14); pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                    pdf.set_font("Courier", size=st.session_state.fonte_global)
                    txt = processar_texto(m['conteudo'], st.session_state.tom_ajuste, st.session_state.modo_colunas)
                    pdf.multi_cell(0, 5, txt.encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Baixar PDF", pdf.output(dest='S'), f"{nome_arq}.pdf")
