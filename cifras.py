# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re
import io
import zipfile
from docx import Document
from docx.shared import Pt

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Music Book Pro",
    page_icon="🎸",
    layout="wide"
)

st.markdown("""
<style>
textarea, pre, .cifra-renderizada{
    font-family:'Courier New', monospace !important;
    white-space:pre !important;
    word-wrap:normal !important;
    line-height:1.2 !important;
}

.stButton > button{
    width:100%;
    border-radius:5px;
}

.page-container{
    background:#ffffff;
    padding:40px;
    border-radius:2px;
    border:1px solid #ccc;
    color:black;
    margin-bottom:20px;
    min-height: 500px;
    overflow-x: auto;
}
.warning-a4 {
    border: 2px solid red !important;
}
</style>""", unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "book" not in st.session_state:
    st.session_state.book = []
if "limpador" not in st.session_state:
    st.session_state.limpador = 0
if "musica_focada" not in st.session_state:
    st.session_state.musica_focada = None
if "temp_titulo" not in st.session_state:
    st.session_state.temp_titulo = ""
if "temp_conteudo" not in st.session_state:
    st.session_state.temp_conteudo = ""

# -------------------------------------------------
# TRANSPOSIÇÃO E LÓGICA
# -------------------------------------------------
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def transpor_acorde(acorde, semitons):
    if semitons == 0: return acorde
    def sub(match):
        nota = match.group(1)
        resto = match.group(2)
        if nota in NOTAS:
            idx = (NOTAS.index(nota) + semitons) % 12
            return NOTAS[idx] + resto
        return match.group(0)
    return re.sub(r'([A-G]#?)([^A-G\s]*)', sub, acorde)

def processar_texto(texto, semitons, colunas):
    if not texto: return ""
    linhas = texto.split("\n")
    linhas_t = []
    
    for linha in linhas:
        nova = ""
        pos = 0
        for m in re.finditer(r'\S+', linha):
            nova += " " * (m.start() - pos) + transpor_acorde(m.group(), semitons)
            pos = m.start() + len(m.group())
        linhas_t.append(nova + " " * (len(linha) - pos))
    
    if colunas == "2 Colunas":
        total = len(linhas_t)
        meio = (total // 2) + (total % 2)
        esq, dir = linhas_t[:meio], linhas_t[meio:]
        largura = max(len(x) for x in esq) if esq else 0
        final = []
        for i in range(max(len(esq), len(dir))):
            a = esq[i] if i < len(esq) else ""
            b = dir[i] if i < len(dir) else ""
            final.append(a.ljust(largura + 8) + b)
        return "\n".join(final)
    
    return "\n".join(linhas_t)

# -------------------------------------------------
# EXPORTAÇÃO
# -------------------------------------------------
def exportar_doc():
    doc = Document()
    for m in st.session_state.book:
        doc.add_heading(m["titulo"], level=1)
        texto = processar_texto(m["conteudo"], m["tom"], m["cols"])
        paragrafo = doc.add_paragraph()
        run = paragrafo.add_run(texto)
        run.font.name = "Courier New"
        run.font.size = Pt(11) # Fonte padrão para Word
        doc.add_page_break()
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

def exportar_pdf_buffer():
    pdf = FPDF()
    for m in st.session_state.book:
        pdf.add_page()
        pdf.set_font("Courier", "B", 14)
        pdf.cell(0, 10, m["titulo"].encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_font("Courier", size=11)
        txt = processar_texto(m["conteudo"], m["tom"], m["cols"])
        pdf.multi_cell(0, 5, txt.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# -------------------------------------------------
# SIDEBAR (AJUSTES ATIVOS)
# -------------------------------------------------
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

st.sidebar.divider()
st.sidebar.markdown("### 🛠️ Ajustes Ativos")

if st.session_state.musica_focada is not None and len(st.session_state.book) > st.session_state.musica_focada:
    idx = st.session_state.musica_focada
    
    st.sidebar.write(f"Editando: **{st.session_state.book[idx]['titulo']}**")
    
    st.sidebar.write("Tom")
    t1, t2, t3 = st.sidebar.columns(3)
    if t1.button("♭"): st.session_state.book[idx]["tom"] -= 1; st.rerun()
    if t2.button("0"): st.session_state.book[idx]["tom"] = 0; st.rerun()
    if t3.button("♯"): st.session_state.book[idx]["tom"] += 1; st.rerun()

    st.sidebar.write("Layout")
    l1, l2 = st.sidebar.columns(2)
    if l1.button("📄 1 Col"): st.session_state.book[idx]["cols"] = "1 Coluna"; st.rerun()
    if l2.button("✂️ 2 Col"): st.session_state.book[idx]["cols"] = "2 Colunas"; st.rerun()
else:
    st.sidebar.info("👈 Selecione uma música no Visualizar Book")

# -------------------------------------------------
# ADICIONAR MÚSICA
# -------------------------------------------------
if aba == "Adicionar Música":
    st.header("🔍 Capturar Cifra")
    url = st.text_input("Link da cifra (CifraClub)", key=f"url_{st.session_state.limpador}")
    
    if st.button("Capturar"):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            st.session_state.temp_titulo = (soup.find("h1", class_="t1") or soup.find("h1")).get_text().strip()
            st.session_state.temp_conteudo = soup.find("pre").get_text()
            st.success("Cifra capturada!")
            st.rerun()
        except: st.error("Erro ao capturar link.")
    
    st.divider()
    tit = st.text_input("Título", value=st.session_state.temp_titulo)
    cif = st.text_area("Cifra", value=st.session_state.temp_conteudo, height=300)
    
    if st.button("✅ Adicionar ao Repertório"):
        if tit and cif:
            st.session_state.book.append({
                "titulo": tit, "conteudo": cif, "tom": 0, "cols": "1 Coluna"
            })
            st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""
            st.rerun()

# -------------------------------------------------
# VISUALIZAR BOOK
# -------------------------------------------------
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("O book está vazio.")
    else:
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']} (Tom: {m['tom']})", expanded=(st.session_state.musica_focada == i)):
                if st.button("🎯 Selecionar para Ajustes", key=f"sel_{i}"):
                    st.session_state.musica_focada = i
                    st.rerun()
                
                texto_proc = processar_texto(m["conteudo"], m["tom"], m["cols"])
                
                # VERIFICAÇÃO DE MARGEM A4
                estourou = any(len(linha) > 80 for linha in texto_proc.split("\n"))
                if estourou:
                    st.warning("⚠️ Esta música ultrapassa a largura da folha A4!")
                
                # Preview Estilizado
                classe_aviso = "warning-a4" if estourou else ""
                bloco = ""
                for linha in texto_proc.split("\n"):
                    linha_formatada = linha.replace(" ", "&nbsp;") if linha.strip() != "" else "&nbsp;"
                    bloco += f"<div class='cifra-renderizada' style='font-size:11pt;'>{linha_formatada}</div>"
                
                st.markdown(f"<div class='page-container {classe_aviso}'>{bloco}</div>", unsafe_allow_html=True)
                
                if st.button("🗑️ Excluir", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# -------------------------------------------------
# EXPORTAR
# -------------------------------------------------
elif aba == "Exportar":
    st.header("📂 Exportar Livro")
    if not st.session_state.book:
        st.info("Adicione músicas primeiro.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📑 Baixar PDF", exportar_pdf_buffer(), "Repertorio.pdf", "application/pdf")
            st.download_button("🟦 Baixar Word (.docx)", exportar_doc(), "Repertorio.docx")

        with col2:
            txt_geral = "\n\n".join([f"== {m['titulo']} ==\n{processar_texto(m['conteudo'], m['tom'], '1 Coluna')}" for m in st.session_state.book])
            st.download_button("📝 Baixar TXT", txt_geral.encode("utf-8"), "Repertorio.txt")
            st.download_button("📱 Baixar Kindle (.txt)", txt_geral.encode("utf-8"), "Kindle.txt")
        
