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

# CSS para simular a folha de papel e fontes
st.markdown("""
    <style>
    textarea { font-family: 'Courier New', Courier, monospace !important; }
    .stButton > button { width: 100%; border-radius: 5px; }
    
    /* Estilo para simular a folha A4 no visualizador */
    .page-break-line {
        border-top: 2px dashed #ff4b4b;
        margin: 20px 0;
        position: relative;
    }
    .page-break-line::after {
        content: "CORTE DA PÁGINA (FIM DA FOLHA)";
        position: absolute;
        right: 0;
        top: -25px;
        font-size: 10px;
        color: #ff4b4b;
        font-weight: bold;
    }
    .page-container {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Session State
if 'book' not in st.session_state: st.session_state.book = []
if 'limpador' not in st.session_state: st.session_state.limpador = 0
if 'temp_titulo' not in st.session_state: st.session_state.temp_titulo = ""
if 'temp_conteudo' not in st.session_state: st.session_state.temp_conteudo = ""
if 'original_conteudo' not in st.session_state: st.session_state.original_conteudo = ""
if 'tom_ajuste' not in st.session_state: st.session_state.tom_ajuste = 0
if 'tamanho_fonte' not in st.session_state: st.session_state.tamanho_fonte = 11

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

def processar_transposicao(texto, semitons):
    if semitons == 0 or not texto: return texto
    linhas = texto.split('\n')
    novo_texto = []
    for linha in linhas:
        if not linha.strip():
            novo_texto.append(linha)
            continue
        nova_linha = ""
        pos = 0
        for m in re.finditer(r'\S+', linha):
            espacos = " " * (m.start() - pos)
            palavra = m.group()
            palavra_transp = "[" + transpor_acorde(palavra[1:-1], semitons) + "]" if palavra.startswith('[') else transpor_acorde(palavra, semitons)
            nova_linha += espacos + palavra_transp
            pos = m.start() + len(m.group())
        novo_texto.append(nova_linha)
    return '\n'.join(novo_texto)

# --- FUNÇÕES CORE ---
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

def dividir_em_colunas(texto):
    linhas = [l.rstrip() for l in texto.strip().split('\n')]
    meio = (len(linhas) // 2) + (len(linhas) % 2)
    col_esq, col_dir = linhas[:meio], linhas[meio:]
    larg_max = max([len(l) for l in col_esq]) if col_esq else 0
    return "\n".join([f"{(col_esq[i] if i < len(col_esq) else '').ljust(larg_max + 10)}{(col_dir[i] if i < len(col_dir) else '')}" for i in range(max(len(col_esq), len(col_dir)))])

# --- INTERFACE ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

st.sidebar.divider()
st.sidebar.markdown("### 🎸 Ajustes Gerais")
c_tom1, c_tom2, c_tom3 = st.sidebar.columns(3)
if c_tom1.button("♭"): st.session_state.tom_ajuste -= 1
if c_tom2.button("0"): st.session_state.tom_ajuste = 0
if c_tom3.button("♯"): st.session_state.tom_ajuste += 1

c_f1, c_f2, c_f3 = st.sidebar.columns(3)
if c_f1.button("A-"): st.session_state.tamanho_fonte -= 1
if c_f2.button("11"): st.session_state.tamanho_fonte = 11
if c_f3.button("A+"): st.session_state.tamanho_fonte += 1

# Estilo dinâmico de fonte
st.markdown(f"<style>.cifra-real {{ font-family: 'Courier New', monospace; font-size: {st.session_state.tamanho_fonte}pt; line-height: 1.2; white-space: pre; }}</style>", unsafe_allow_html=True)

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Importar")
    url = st.text_input("Link da cifra:", key=f"url_{st.session_state.limpador}")
    if st.button("Capturar"):
        t, c = buscar_cifra(url)
        st.session_state.temp_titulo, st.session_state.temp_conteudo, st.session_state.original_conteudo = t, c, c
        st.rerun()
    
    col_mod1, col_mod2 = st.columns(2)
    if col_mod1.button("📄 1 Coluna"): st.session_state.temp_conteudo = st.session_state.original_conteudo; st.rerun()
    if col_mod2.button("✂️ 2 Colunas"): st.session_state.temp_conteudo = dividir_em_colunas(st.session_state.original_conteudo); st.rerun()

    tit = st.text_input("Título:", value=st.session_state.temp_titulo)
    cif = st.text_area("Cifra:", value=processar_transposicao(st.session_state.temp_conteudo, st.session_state.tom_ajuste), height=300)
    
    if st.button("✅ Salvar"):
        st.session_state.book.append({"titulo": tit, "conteudo": cif})
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""; st.session_state.limpador += 1
        st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório (Simulador de Impressão)")
    
    if not st.session_state.book:
        st.info("Book vazio.")
    else:
        # Cálculo aproximado de linhas por página (A4 tem ~29.7cm)
        # Com margens e Courier 11pt, cabem cerca de 50-55 linhas.
        linhas_por_pagina = int(600 / (st.session_state.tamanho_fonte * 1.2))

        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']}", expanded=True):
                # Transpõe o conteúdo para o tom atual
                conteudo = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                linhas = conteudo.split('\n')
                total_linhas = len(linhas)
                paginas_necessarias = (total_linhas // linhas_por_pagina) + 1
                
                st.caption(f"📊 Estatísticas: {total_linhas} linhas | Estimativa: {paginas_necessarias} página(s) no arquivo final.")
                
                # Container que simula a folha
                with st.container():
                    st.markdown('<div class="page-container">', unsafe_allow_html=True)
                    
                    # Título simulado
                    st.markdown(f"### {m['titulo']}")
                    
                    # Exibe as linhas e insere o tracejado de corte
                    for idx, linha in enumerate(linhas):
                        st.markdown(f'<div class="cifra-real">{linha}</div>', unsafe_allow_html=True)
                        if (idx + 1) % linhas_por_pagina == 0 and (idx + 1) < total_linhas:
                            st.markdown('<div class="page-break-line"></div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.button(f"🗑️ Excluir", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar")
    if not st.session_state.book: st.warning("Adicione músicas.")
    else:
        nome_arq = st.text_input("Nome do arquivo:", "Meu_Repertorio").replace(" ", "_")
        c1, c2 = st.columns(2)
        
        with c1:
            doc = Document()
            for m in st.session_state.book:
                doc.add_heading(m['titulo'], 1)
                run = doc.add_paragraph().add_run(processar_transposicao(m['conteudo'], st.session_state.tom_ajuste))
                run.font.name = 'Courier New'; run.font.size = Pt(st.session_state.tamanho_fonte)
                doc.add_page_break()
            buf = io.BytesIO(); doc.save(buf)
            st.download_button("📥 Word", buf.getvalue(), f"{nome_arq}.docx")

        with c2:
            if st.button("Gerar PDF"):
                pdf = FPDF()
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14); pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                    pdf.set_font("Courier", size=st.session_state.tamanho_fonte)
                    pdf.multi_cell(0, 5, processar_transposicao(m['conteudo'], st.session_state.tom_ajuste).encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 PDF", pdf.output(dest='S'), f"{nome_arq}.pdf")
