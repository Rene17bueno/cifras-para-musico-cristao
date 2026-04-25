# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re
import io
from docx import Document
from docx.shared import Pt

# -------------------------------------------------
# 1. CONFIGURAÇÃO E INTERFACE (BOOTSTRAP)
# -------------------------------------------------
st.set_page_config(page_title="Music Book Pro", page_icon="🎸", layout="wide")

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .paper-a4 {
            background: white;
            padding: 60px;
            margin: 20px auto;
            width: 100%;
            max-width: 800px;
            min-height: 1000px;
            box-shadow: 0 0 20px rgba(0,0,0,0.2);
            border: 1px solid #ddd;
            font-family: 'Courier New', Courier, monospace;
            color: black;
            overflow-x: auto;
        }
        .warning-margin {
            border: 3px solid #ff4b4b !important;
        }
        .cifra-content {
            font-size: 11pt;
            white-space: pre;
            line-height: 1.2;
        }
        .sidebar-header { color: #0d6efd; font-weight: bold; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 2. ESTADO DO SISTEMA
# -------------------------------------------------
if "book" not in st.session_state:
    st.session_state.book = []
if "musica_focada" not in st.session_state:
    st.session_state.musica_focada = 0
if "temp_titulo" not in st.session_state:
    st.session_state.temp_titulo = ""
if "temp_conteudo" not in st.session_state:
    st.session_state.temp_conteudo = ""

# -------------------------------------------------
# 3. FUNÇÕES DE TRANSPOSIÇÃO E PROCESSAMENTO
# -------------------------------------------------
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def transpor_acorde(acorde, semitons):
    if semitons == 0: return acorde
    def sub(match):
        nota, resto = match.group(1), match.group(2)
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
        meio = (len(linhas_t) // 2) + (len(linhas_t) % 2)
        esq, dir = linhas_t[:meio], linhas_t[meio:]
        largura = max(len(x) for x in esq) if esq else 0
        return "\n".join([(esq[i] if i<len(esq) else "").ljust(largura + 6) + (dir[i] if i<len(dir) else "") for i in range(max(len(esq), len(dir)))])
    
    return "\n".join(linhas_t)

# -------------------------------------------------
# 4. FUNÇÕES DE EXPORTAÇÃO
# -------------------------------------------------
def gerar_pdf():
    pdf = FPDF()
    for m in st.session_state.book:
        pdf.add_page()
        pdf.set_font("Courier", "B", 16)
        pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_font("Courier", size=11)
        txt = processar_texto(m["conteudo"], m["tom"], m["cols"])
        pdf.multi_cell(0, 5, txt.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

def gerar_docx():
    doc = Document()
    for m in st.session_state.book:
        doc.add_heading(m['titulo'], 0)
        txt = processar_texto(m["conteudo"], m["tom"], m["cols"])
        p = doc.add_paragraph()
        run = p.add_run(txt)
        run.font.name = 'Courier New'
        run.font.size = Pt(11)
        doc.add_page_break()
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

# -------------------------------------------------
# 5. SIDEBAR (MENU E AJUSTES)
# -------------------------------------------------
with st.sidebar:
    st.markdown("<h2 class='sidebar-header'>🎵 Music Book Pro</h2>", unsafe_allow_html=True)
    aba = st.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])
    
    if st.session_state.book and aba == "Visualizar Book":
        st.divider()
        st.subheader("🛠️ Ajustes Ativos")
        idx = st.session_state.musica_focada
        m = st.session_state.book[idx]
        
        st.write(f"Música: **{m['titulo']}**")
        col1, col2, col3 = st.columns(3)
        if col1.button("♭"): m["tom"] -= 1; st.rerun()
        if col2.button("0"): m["tom"] = 0; st.rerun()
        if col3.button("♯"): m["tom"] += 1; st.rerun()
        
        layout = st.radio("Layout", ["1 Coluna", "2 Colunas"], index=0 if m["cols"]=="1 Coluna" else 1)
        m["cols"] = layout

# -------------------------------------------------
# 6. CONTEÚDO PRINCIPAL
# -------------------------------------------------
if aba == "Adicionar Música":
    st.header("➕ Nova Cifra")
    url = st.text_input("Link CifraClub")
    if st.button("Capturar"):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            st.session_state.temp_titulo = soup.find("h1").get_text().strip()
            st.session_state.temp_conteudo = soup.find("pre").get_text()
            st.rerun()
        except: st.error("Erro ao capturar.")

    tit = st.text_input("Título", value=st.session_state.temp_titulo)
    cif = st.text_area("Cifra", value=st.session_state.temp_conteudo, height=300)
    
    if st.button("✅ Salvar no Book"):
        st.session_state.book.append({"titulo": tit, "conteudo": cif, "tom": 0, "cols": "1 Coluna"})
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""
        st.rerun()

elif aba == "Visualizar Book":
    if not st.session_state.book:
        st.info("O book está vazio.")
    else:
        titulos = [m['titulo'] for m in st.session_state.book]
        st.session_state.musica_focada = st.selectbox("Escolha a música para ver/ajustar:", range(len(titulos)), format_func=lambda x: titulos[x])
        
        m = st.session_state.book[st.session_state.musica_focada]
        texto_render = processar_texto(m["conteudo"], m["tom"], m["cols"])
        
        # Validação de Margem A4 (Courier 11pt suporta ~80 chars)
        estourou = any(len(l) > 80 for l in texto_render.split("\n"))
        
        if estourou:
            st.error("⚠️ LINHA FORA DA MARGEM A4! Diminua o texto ou use 1 coluna.")
            
        st.markdown(f"""
            <div class="paper-a4 {'warning-margin' if estourou else ''}">
                <h2 style="text-align:center;">{m['titulo']}</h2>
                <hr>
                <div class="cifra-content">{texto_render.replace(" ", "&nbsp;")}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Excluir Música"):
            st.session_state.book.pop(st.session_state.musica_focada)
            st.rerun()

elif aba == "Exportar":
    st.header("📂 Exportar Livro")
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        st.markdown("### Escolha o formato para baixar todo o repertório:")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.download_button("📑 PDF", gerar_pdf(), "repertorio.pdf", use_container_width=True)
        with c2:
            st.download_button("🟦 Word (.docx)", gerar_docx(), "repertorio.docx", use_container_width=True)
        
        # Lógica TXT comum para os dois últimos
        txt_full = ""
        for m in st.session_state.book:
            txt_full += f"\n\n{'='*30}\n{m['titulo'].upper()}\n{'='*30}\n"
            txt_full += processar_texto(m["conteudo"], m["tom"], "1 Coluna")
            
        with c3:
            st.download_button("📝 Texto (.txt)", txt_full.encode("utf-8"), "repertorio.txt", use_container_width=True)
        with c4:
            st.download_button("📱 Kindle", txt_full.encode("utf-8"), "kindle.txt", use_container_width=True)
