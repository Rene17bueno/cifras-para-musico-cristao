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

# CSS REFORÇADO PARA ALINHAMENTO
st.markdown("""
    <style>
    /* Força fonte monoespaçada em todos os campos de texto */
    textarea, pre, .cifra-renderizada {
        font-family: 'Courier New', Courier, monospace !important;
        white-space: pre !important; /* Mantém espaços e quebras de linha exatamente como são */
        word-wrap: normal !important;
        overflow-x: auto !important;
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
if 'original_conteudo' not in st.session_state: st.session_state.original_conteudo = ""
if 'tom_ajuste' not in st.session_state: st.session_state.tom_ajuste = 0
if 'fonte_atual_edicao' not in st.session_state: st.session_state.fonte_atual_edicao = 11

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
        # Regex melhorada para identificar acordes sem destruir o espaçamento
        for m in re.finditer(r'\S+', linha):
            espacos_vazios = " " * (m.start() - pos)
            palavra = m.group()
            palavra_transp = transpor_acorde(palavra, semitons)
            nova_linha += espacos_vazios + palavra_transp
            pos = m.start() + len(m.group())
        
        # Preserva os espaços no final da linha também
        restante = " " * (len(linha) - pos)
        novo_texto.append(nova_linha + restante)
        
    return '\n'.join(novo_texto)

def buscar_cifra(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        titulo = (soup.find('h1', class_='t1') or soup.find('h1', class_='t3') or soup.find('h1')).get_text().strip()
        corpo = soup.find('pre')
        conteudo = corpo.get_text() if corpo else ""
        return titulo, conteudo
    except: return "", ""

# --- INTERFACE ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

# Ajuste global de tom
st.sidebar.divider()
st.sidebar.markdown("### 🎸 Ajuste de Tom Global")
c_tom1, c_tom2, c_tom3 = st.sidebar.columns(3)
if c_tom1.button("♭"): st.session_state.tom_ajuste -= 1
if c_tom2.button("0"): st.session_state.tom_ajuste = 0
if c_tom3.button("♯"): st.session_state.tom_ajuste += 1
st.sidebar.caption(f"Semidons: {st.session_state.tom_ajuste}")

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Capturar Cifra")
    url = st.text_input("Link da música:", key=f"url_{st.session_state.limpador}")
    
    if st.button("Capturar Dados"):
        t, c = buscar_cifra(url)
        st.session_state.temp_titulo, st.session_state.temp_conteudo, st.session_state.original_conteudo = t, c, c
        st.rerun()

    st.divider()
    st.subheader("Configurações Locais")
    
    c_f1, c_f2, c_f3 = st.columns([1,1,4])
    if c_f1.button("A-"): st.session_state.fonte_atual_edicao -= 1
    if c_f3.button("A+"): st.session_state.fonte_atual_edicao += 1
    
    # CSS dinâmico para o campo de edição
    st.markdown(f"<style>textarea {{ font-size: {st.session_state.fonte_atual_edicao}pt !important; }}</style>", unsafe_allow_html=True)

    tit = st.text_input("Título:", value=st.session_state.temp_titulo)
    cifra_edit = st.text_area("Cifra (Ajuste o alinhamento aqui se necessário):", 
                              value=processar_transposicao(st.session_state.temp_conteudo, st.session_state.tom_ajuste), 
                              height=400)
    
    if st.button("✅ Salvar Música"):
        st.session_state.book.append({
            "titulo": tit, 
            "conteudo": cifra_edit, 
            "tamanho_fonte": st.session_state.fonte_atual_edicao
        })
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""; st.session_state.limpador += 1
        st.success("Salvo!")
        st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("Nenhuma música salva.")
    else:
        for i, m in enumerate(st.session_state.book):
            f_size = m.get("tamanho_fonte", 11)
            # Cálculo de quebra de página
            linhas_por_pagina = int(700 / (f_size * 1.3))
            
            with st.expander(f"🎸 {m['titulo']}", expanded=True):
                # Aplicando transposição e preservando espaços
                txt_final = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                linhas = txt_final.split('\n')
                
                # RENDERIZAÇÃO ESTREITA
                st.markdown(f'<div class="page-container" style="font-size: {f_size}pt;">', unsafe_allow_html=True)
                
                bloco_texto = ""
                for idx, linha in enumerate(linhas):
                    # Substitui espaços por espaços inquebráveis HTML (&nbsp;) para garantir o alinhamento
                    linha_html = linha.replace(" ", "&nbsp;")
                    bloco_texto += f'<div class="cifra-renderizada">{linha_html if linha_html != "" else "&nbsp;"}</div>'
                    
                    if (idx + 1) % linhas_por_pagina == 0 and (idx + 1) < len(linhas):
                        bloco_texto += '<div class="page-break-line"></div>'
                
                st.markdown(bloco_texto, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button(f"🗑️ Remover", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Gerar Arquivos")
    if not st.session_state.book:
        st.warning("Adicione músicas.")
    else:
        nome_arq = st.text_input("Nome do arquivo:", "Meu_Livro_de_Cifras")
        
        c1, c2 = st.columns(2)
        with c1:
            doc = Document()
            for i, m in enumerate(st.session_state.book):
                if i > 0: doc.add_page_break()
                doc.add_heading(m['titulo'], 1)
                p = doc.add_paragraph()
                run = p.add_run(processar_transposicao(m['conteudo'], st.session_state.tom_ajuste))
                run.font.name = 'Courier New'
                run.font.size = Pt(m.get("tamanho_fonte", 11))
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Baixar Word", buf.getvalue(), f"{nome_arq}.docx")

        with c2:
            if st.button("Gerar PDF"):
                pdf = FPDF()
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                    pdf.set_font("Courier", size=m.get("tamanho_fonte", 11))
                    cif_p = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                    pdf.multi_cell(0, 5, cif_p.encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Baixar PDF", pdf.output(dest='S'), f"{nome_arq}.pdf")
