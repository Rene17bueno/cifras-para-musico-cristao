# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from docx import Document
from docx.shared import Pt
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
# Controladores globais da sidebar que servirão para a música "focada"
if 'fonte_global' not in st.session_state: st.session_state.fonte_global = 11
if 'tom_ajuste' not in st.session_state: st.session_state.tom_ajuste = 0
if 'modo_colunas' not in st.session_state: st.session_state.modo_colunas = "1 Coluna"

# --- LÓGICA DE TRANSPOSIÇÃO ---
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
    
    # 1. Transposição
    linhas_transpostas = []
    for linha in linhas:
        nova_linha = ""
        pos = 0
        for m in re.finditer(r'\S+', linha):
            nova_linha += " " * (m.start() - pos) + transpor_acorde(m.group(), semitons)
            pos = m.start() + len(m.group())
        linhas_transpostas.append(nova_linha + (" " * (len(linha) - pos)))

    # 2. Divisão em Colunas (Ajustado para subir acorde + letra juntos)
    if colunas == "2 Colunas":
        total_linhas = len(linhas_transpostas)
        meio = (total_linhas // 2) + (total_linhas % 2)
        
        # Garante que não quebre entre um acorde e uma letra
        # Se a linha do meio for de acorde (poucos caracteres e muitos espaços), joga pro lado
        if meio < total_linhas and len(linhas_transpostas[meio].strip()) < 10:
            meio += 1

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

# --- SIDEBAR ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

st.sidebar.divider()
st.sidebar.markdown("### 🛠️ Controles (Música Ativa)")

# Os botões agora atualizam a música que estiver sendo visualizada/editada
c_f1, c_f2, c_f3 = st.sidebar.columns(3)
if c_f1.button("A-"): st.session_state.fonte_global -= 1
if c_f2.button("11"): st.session_state.fonte_global = 11
if c_f3.button("A+"): st.session_state.fonte_global += 1

c_t1, c_t2, c_t3 = st.sidebar.columns(3)
if c_t1.button("♭"): st.session_state.tom_ajuste -= 1
if c_t2.button("0"): st.session_state.tom_ajuste = 0
if c_t3.button("♯"): st.session_state.tom_ajuste += 1

c_c1, c_c2 = st.sidebar.columns(2)
if c_c1.button("📄 1"): st.session_state.modo_colunas = "1 Coluna"
if c_c2.button("✂️ 2"): st.session_state.modo_colunas = "2 Colunas"

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Capturar Cifra")
    url = st.text_input("Link:", key=f"url_{st.session_state.limpador}")
    if st.button("Capturar"):
        t, c = buscar_cifra(url)
        st.session_state.temp_titulo, st.session_state.temp_conteudo = t, c
        st.rerun()

    st.divider()
    tit = st.text_input("Título:", value=st.session_state.temp_titulo)
    txt_proc = processar_texto(st.session_state.temp_conteudo, st.session_state.tom_ajuste, st.session_state.modo_colunas)
    cif = st.text_area("Edição:", value=txt_proc, height=400)
    
    if st.button("✅ Salvar"):
        st.session_state.book.append({
            "titulo": tit, "conteudo": cif, 
            "fonte": st.session_state.fonte_global,
            "tom": st.session_state.tom_ajuste,
            "cols": st.session_state.modo_colunas
        })
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""; st.session_state.limpador += 1
        st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    for i, m in enumerate(st.session_state.book):
        # Cada música usa suas próprias configurações salvas
        with st.expander(f"🎸 {m['titulo']}", expanded=True):
            # Se o usuário mexer na sidebar COM O EXPANDER ABERTO, atualizamos SÓ ESTA música
            m['fonte'] = st.session_state.fonte_global
            m['tom'] = st.session_state.tom_ajuste
            m['cols'] = st.session_state.modo_colunas
            
            f_size = m['fonte']
            linhas_por_pág = int(720 / (f_size * 1.3))
            texto_exibir = processar_texto(m['conteudo'], m['tom'], m['cols'])
            
            st.markdown(f'<div class="page-container" style="font-size: {f_size}pt;">', unsafe_allow_html=True)
            bloco = ""
            for idx, linha in enumerate(texto_exibir.split('\n')):
                l_html = linha.replace(" ", "&nbsp;")
                bloco += f'<div class="cifra-renderizada">{l_html if l_html != "" else "&nbsp;"}</div>'
                if (idx + 1) % linhas_por_pág == 0:
                    bloco += '<div class="page-break-line"></div>'
            st.markdown(bloco, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button(f"🗑️ Excluir", key=f"del_{i}"):
                st.session_state.book.pop(i)
                st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar")
    if st.session_state.book:
        if st.button("Gerar PDF"):
            pdf = FPDF()
            for m in st.session_state.book:
                pdf.add_page()
                pdf.set_font("Courier", 'B', 14); pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                pdf.set_font("Courier", size=m['fonte'])
                txt = processar_texto(m['conteudo'], m['tom'], m['cols'])
                pdf.multi_cell(0, 5, txt.encode('latin-1', 'replace').decode('latin-1'))
            st.download_button("📥 Baixar PDF", pdf.output(dest='S'), "Livro.pdf")
