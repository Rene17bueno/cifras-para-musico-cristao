# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from docx import Document
import io

# -------------------------------------------------
# CONFIGURAÇÃO
# -------------------------------------------------
st.set_page_config(page_title="Music Book Pro", layout="wide")

if "book" not in st.session_state:
    st.session_state.book = []
if "musica_focada" not in st.session_state:
    st.session_state.musica_focada = 0

# -------------------------------------------------
# FUNÇÕES DE APOIO
# -------------------------------------------------
def processar_texto(texto, semitons, colunas):
    # (Mantendo a lógica de transposição original)
    return texto 

# -------------------------------------------------
# FUNÇÕES DE EXPORTAÇÃO
# -------------------------------------------------
def gerar_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for m in st.session_state.book:
        pdf.add_page()
        pdf.set_font("Courier", "B", 16)
        pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_font("Courier", size=12) # Fonte fixa
        txt = processar_texto(m["conteudo"], m["tom"], m["cols"])
        pdf.multi_cell(0, 5, txt.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

def gerar_docx():
    doc = Document()
    for m in st.session_state.book:
        doc.add_heading(m['titulo'], level=1)
        txt = processar_texto(m["conteudo"], m["tom"], m["cols"])
        p = doc.add_paragraph(txt)
        p.style.font.name = 'Courier New'
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

def gerar_txt_simples():
    conteudo = ""
    for m in st.session_state.book:
        conteudo += f"--- {m['titulo']} ---\n\n"
        conteudo += processar_texto(m["conteudo"], m["tom"], "1 Coluna")
        conteudo += "\n\n"
    return conteudo.encode('utf-8')

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("Configurações")
if st.session_state.book:
    idx = st.sidebar.selectbox("Editar Música:", range(len(st.session_state.book)), 
                               format_func=lambda x: st.session_state.book[x]['titulo'])
    st.session_state.musica_focada = idx
    m = st.session_state.book[idx]
    
    st.sidebar.subheader("Ajustes")
    m["tom"] = st.sidebar.number_input("Transpor Tom", -12, 12, m["tom"])
    m["cols"] = st.sidebar.radio("Layout", ["1 Coluna", "2 Colunas"], 
                                 index=0 if m["cols"] == "1 Coluna" else 1)
else:
    st.sidebar.info("Adicione uma música.")

# -------------------------------------------------
# ABAS
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Adicionar", "Visualizar", "Exportar"])

with tab1:
    st.header("➕ Adicionar Música")
    tit = st.text_input("Título")
    cif = st.text_area("Cifra", height=300)
    if st.button("Salvar"):
        st.session_state.book.append({"titulo": tit, "conteudo": cif, "tom": 0, "cols": "1 Coluna"})
        st.success("Salvo!")

with tab2:
    st.header("📖 Preview (Padrão A4)")
    if st.session_state.book:
        musica = st.session_state.book[st.session_state.musica_focada]
        st.markdown(f"<div style='font-family:Courier; white-space:pre; padding:20px; border:1px solid #ccc;'>{processar_texto(musica['conteudo'], musica['tom'], musica['cols'])}</div>", unsafe_allow_html=True)

with tab3:
    st.header("💾 Exportar")
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        # PDF
        st.download_button("📥 Baixar PDF", gerar_pdf(), "repertorio.pdf", "application/pdf")
        
        # Word (.docx)
        st.download_button("📥 Baixar Word (.docx)", gerar_docx(), "repertorio.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        # TXT Simples
        st.download_button("📥 Baixar TXT", gerar_txt_simples(), "repertorio.txt", "text/plain")
        
        # Kindle (Txt formatado)
        st.download_button("📥 Baixar para Kindle (.txt)", gerar_txt_simples(), "kindle_repertorio.txt", "text/plain")
