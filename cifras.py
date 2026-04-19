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
    textarea { font-family: 'Courier New', Courier, monospace !important; }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Session State
if 'book' not in st.session_state:
    st.session_state.book = []
if 'limpador' not in st.session_state:
    st.session_state.limpador = 0
if 'temp_titulo' not in st.session_state:
    st.session_state.temp_titulo = ""
if 'temp_conteudo' not in st.session_state:
    st.session_state.temp_conteudo = ""
if 'original_conteudo' not in st.session_state:
    st.session_state.original_conteudo = ""
if 'select_tom_principal' not in st.session_state:
    st.session_state.select_tom_principal = "0 (Tom Original - B)"

# --- LÓGICA DE TRANSPOSIÇÃO ---
NOTAS = ['B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#']

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
    if semitons == 0 or not texto:
        return texto
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
            if palavra.startswith('[') and palavra.endswith(']'):
                conteudo_tag = palavra[1:-1]
                palavra_transp = "[" + transpor_acorde(conteudo_tag, semitons) + "]"
            else:
                palavra_transp = transpor_acorde(palavra, semitons)
            nova_linha += espacos + palavra_transp
            pos = m.start() + len(m.group())
        novo_texto.append(nova_linha)
    return '\n'.join(novo_texto)

# --- FUNÇÕES CORE ---
def limpar_campos():
    st.session_state.limpador += 1
    st.session_state.temp_titulo = ""
    st.session_state.temp_conteudo = ""
    st.session_state.original_conteudo = ""

def buscar_cifra(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        titulo_tag = soup.find('h1', class_='t1') or soup.find('h1', class_='t3') or soup.find('h1')
        titulo = titulo_tag.get_text().strip() if titulo_tag else "Nova Música"
        corpo = soup.find('pre')
        return titulo, (corpo.get_text() if corpo else "")
    except:
        return "", ""

def dividir_em_colunas(texto):
    linhas = [l.rstrip() for l in texto.strip().split('\n')]
    meio = (len(linhas) // 2) + (len(linhas) % 2)
    col_esq, col_dir = linhas[:meio], linhas[meio:]
    larg_max = max([len(l) for l in col_esq]) if col_esq else 0
    res = ""
    for i in range(max(len(col_esq), len(col_dir))):
        e = col_esq[i] if i < len(col_esq) else ""
        d = col_dir[i] if i < len(col_dir) else ""
        res += f"{e.ljust(larg_max + 10)}{d}\n"
    return res

# --- INTERFACE ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

opcoes_tons = ["-3 (G#)", "-2 (A)", "-1 (A#)", "0 (Tom Original - B)",
               "+1 (C)", "+2 (C#)", "+3 (D)", "+4 (D#)", "+5 (E)", "+6 (F)"]

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Importar e Personalizar")
    
    c_id = st.session_state.limpador
    
    url = st.text_input("Link da cifra:", key=f"url_{c_id}")
    
    col_cap, col_div2, col_div1 = st.columns(3)
    with col_cap:
        if st.button("Capturar Dados"):
            t, c = buscar_cifra(url)
            if t:
                st.session_state.temp_titulo = t
                st.session_state.temp_conteudo = c
                st.session_state.original_conteudo = c
                st.session_state.select_tom_principal = "0 (Tom Original - B)"
                st.rerun()
    
    with col_div2:
        if st.button("✂️ Modo 2 Colunas"):
            if st.session_state.original_conteudo:
                st.session_state.temp_conteudo = dividir_em_colunas(st.session_state.original_conteudo)
                st.rerun()
    
    with col_div1:
        if st.button("📄 Modo 1 Coluna"):
            if st.session_state.original_conteudo:
                st.session_state.temp_conteudo = st.session_state.original_conteudo
                st.rerun()
    
    titulo_f = st.text_input("Título:", value=st.session_state.temp_titulo, key=f"tit_{c_id}")
    
    tom_selecionado = st.sidebar.selectbox(
        "🎸 Transpor Tonalidade", opcoes_tons, key="select_tom_principal"
    )
    match_tom = re.search(r"([+-]?\d+)", tom_selecionado)
    tom_ajuste = int(match_tom.group(1)) if match_tom else 0
    
    conteudo_visivel = processar_transposicao(st.session_state.temp_conteudo, tom_ajuste)
    
    conteudo_f = st.text_area(
        "Cifra (Editável):",
        value=conteudo_visivel,
        height=500
    )
    
    if st.button("✅ Salvar no meu Book"):
        if titulo_f.strip() and conteudo_f.strip():
            st.session_state.book.append({
                "titulo": titulo_f.strip(),
                "conteudo": conteudo_f
            })
            st.success(f"'{titulo_f}' salva com sucesso!")
            time.sleep(0.8)
            limpar_campos()
            st.rerun()
        else:
            st.warning("Preencha o título e a cifra antes de salvar.")

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    
    tom_selecionado = st.sidebar.selectbox(
        "🎸 Transpor Tonalidade", opcoes_tons, key="select_tom_principal"
    )
    match_tom = re.search(r"([+-]?\d+)", tom_selecionado)
    tom_ajuste = int(match_tom.group(1)) if match_tom else 0
    
    if not st.session_state.book:
        st.info("Seu book ainda está vazio. Adicione músicas na aba 'Adicionar Música'.")
    else:
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']}", expanded=False):
                st.code(
                    processar_transposicao(m['conteudo'], tom_ajuste),
                    language=None
                )
                if st.button(f"🗑️ Excluir música", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.success(f"'{m['titulo']}' excluída.")
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar Arquivos")
    
    tom_selecionado = st.sidebar.selectbox(
        "🎸 Transpor Tonalidade", opcoes_tons, key="select_tom_principal"
    )
    match_tom = re.search(r"([+-]?\d+)", tom_selecionado)
    tom_ajuste = int(match_tom.group(1)) if match_tom else 0
    
    if not st.session_state.book:
        st.warning("Adicione pelo menos uma música antes de exportar.")
    else:
        nome_proj = st.text_input("Título do Projeto:", value="Meu Repertorio")
        nome_arq = nome_proj.replace(" ", "_").lower()
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        with c1:
            txt = f"{nome_proj.upper()}\n\n"
            for m in st.session_state.book:
                txt += f"{m['titulo'].upper()}\n\n"
                txt += f"{processar_transposicao(m['conteudo'], tom_ajuste)}\n\n"
                txt += f"{'-'*40}\n\n"
            st.download_button("📥 Baixar TXT", txt, f"{nome_arq}.txt", mime="text/plain")
        
        with c2:
            doc = Document()
            for s in doc.sections:
                s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(0.5)
            doc.add_heading(nome_proj, 0)
            for m in st.session_state.book:
                doc.add_heading(m['titulo'], 1)
                run = doc.add_paragraph().add_run(processar_transposicao(m['conteudo'], tom_ajuste))
                run.font.name = 'Courier New'
                run.font.size = Pt(11)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Baixar DOCX", buf.getvalue(), f"{nome_arq}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        with c3:
            if st.button("Gerar PDF"):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=10)
                pdf.add_page()
                pdf.set_font("Courier", 'B', 16)
                pdf.cell(0, 10, nome_proj.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
                
                for m in st.session_state.book:
                    pdf.set_font("Courier", 'B', 12)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                    pdf.set_font("Courier", size=11)
                    texto = processar_transposicao(m['conteudo'], tom_ajuste)
                    pdf.multi_cell(0, 5, texto.encode('latin-1', 'replace').decode('latin-1'))
                    pdf.ln(5)
                
                # === CORREÇÃO FINAL PARA O PDF ===
                output = pdf.output(dest='S')
                
                # Garante que seja sempre bytes
                if isinstance(output, str):
                    pdf_output = output.encode('latin-1', 'replace')
                elif isinstance(output, (bytes, bytearray)):
                    pdf_output = bytes(output)
                else:
                    # Fallback: salva em BytesIO
                    buf = io.BytesIO()
                    pdf.output(buf)
                    pdf_output = buf.getvalue()
                
                st.download_button(
                    "📥 Baixar PDF",
                    pdf_output,
                    f"{nome_arq}.pdf",
                    mime="application/pdf"
                )
