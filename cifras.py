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
# CONFIGURAÇÃO E BOOTSTRAP CSS
# -------------------------------------------------
st.set_page_config(page_title="Music Book Pro", page_icon="🎸", layout="wide")

# Injetando Bootstrap via CDN e Estilos Customizados
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .main { background-color: #f8f9fa; }
        
        /* Simulação da Folha A4 */
        .paper-a4 {
            background: white;
            padding: 50px;
            margin: 20px auto;
            width: 100%;
            max-width: 850px;
            min-height: 600px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid #dee2e6;
            font-family: 'Courier New', Courier, monospace;
            color: #212529;
            overflow-x: auto;
        }
        
        /* Alerta de erro de margem */
        .paper-warning {
            border: 3px solid #dc3545 !important;
        }

        .cifra-text {
            font-size: 11pt;
            line-height: 1.3;
            white-space: pre;
        }
        
        .sidebar-title { color: #0d6efd; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# ESTADO DA SESSÃO
# -------------------------------------------------
if "book" not in st.session_state:
    st.session_state.book = []
if "musica_focada" not in st.session_state:
    st.session_state.musica_focada = None
if "temp_titulo" not in st.session_state:
    st.session_state.temp_titulo = ""
if "temp_conteudo" not in st.session_state:
    st.session_state.temp_conteudo = ""

# -------------------------------------------------
# LÓGICA DE TRANSPOSIÇÃO
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
# SIDEBAR (CONTROLES BOOTSTRAP STYLE)
# -------------------------------------------------
with st.sidebar:
    st.markdown("<h2 class='sidebar-title'>🎸 Music Book Pro</h2>", unsafe_allow_html=True)
    aba = st.radio("Navegação", ["➕ Adicionar", "📖 Visual Book", "💾 Exportar"])
    
    st.divider()
    
    if st.session_state.musica_focada is not None and st.session_state.book:
        idx = st.session_state.musica_focada
        m = st.session_state.book[idx]
        st.markdown(f"**Ajustando:** <span class='badge bg-primary'>{m['titulo']}</span>", unsafe_allow_html=True)
        
        st.write("Transposição (Tom)")
        c1, c2, c3 = st.columns(3)
        if c1.button("♭", key="bt_b"): m["tom"] -= 1; st.rerun()
        if c2.button("0", key="bt_0"): m["tom"] = 0; st.rerun()
        if c3.button("♯", key="bt_s"): m["tom"] += 1; st.rerun()
        
        st.write("Layout da Folha")
        l1, l2 = st.columns(2)
        if l1.button("1 Coluna", use_container_width=True): m["cols"] = "1 Coluna"; st.rerun()
        if l2.button("2 Colunas", use_container_width=True): m["cols"] = "2 Colunas"; st.rerun()
    else:
        st.info("Selecione uma música no Visual Book para editar.")

# -------------------------------------------------
# ABA: ADICIONAR (LAYOUT EM CARDS)
# -------------------------------------------------
if aba == "➕ Adicionar":
    st.markdown("<div class='card p-4'>", unsafe_allow_html=True)
    st.header("Capturar Nova Cifra")
    url = st.text_input("Cole o link do CifraClub")
    if st.button("Importar do Site"):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            st.session_state.temp_titulo = soup.find("h1").get_text().strip()
            st.session_state.temp_conteudo = soup.find("pre").get_text()
            st.success("Cifra carregada com sucesso!")
            st.rerun()
        except: st.error("Não foi possível acessar o link.")
    
    st.divider()
    
    tit = st.text_input("Título da Música", value=st.session_state.temp_titulo)
    cif = st.text_area("Cifra (Texto)", value=st.session_state.temp_conteudo, height=250)
    
    if st.button("✅ Salvar no Repertório", type="primary"):
        if tit and cif:
            st.session_state.book.append({"titulo": tit, "conteudo": cif, "tom": 0, "cols": "1 Coluna"})
            st.session_state.temp_titulo, st.session_state.temp_conteudo = "", ""
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# ABA: VISUAL BOOK (SIMULAÇÃO A4)
# -------------------------------------------------
elif aba == "📖 Visual Book":
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        st.header("Visualização de Impressão")
        
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"{m['titulo']} (Tom: {m['tom']})", expanded=(st.session_state.musica_focada == i)):
                col_btn1, col_btn2 = st.columns([1, 5])
                if col_btn1.button("🎯 EDITAR", key=f"edit_{i}"):
                    st.session_state.musica_focada = i
                    st.rerun()
                
                texto_final = processar_texto(m["conteudo"], m["tom"], m["cols"])
                
                # Verificação de margem (80 caracteres é o limite do A4 Courier 11pt)
                estourou = any(len(l) > 80 for l in texto_final.split("\n"))
                if estourou:
                    st.markdown("<div class='alert alert-danger'>⚠️ <b>Atenção:</b> Esta música ultrapassa a margem lateral da folha A4!</div>", unsafe_allow_html=True)
                
                # Renderização da "Folha"
                warn_css = "paper-warning" if estourou else ""
                st.markdown(f"""
                    <div class="paper-a4 {warn_css}">
                        <h2 class="text-center mb-4">{m['titulo']}</h2>
                        <div class="cifra-text">{texto_final.replace(" ", "&nbsp;")}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🗑️ Excluir", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# -------------------------------------------------
# ABA: EXPORTAR (BOTÕES DE DOWNLOAD)
# -------------------------------------------------
elif aba == "💾 Exportar":
    st.header("Gerar Arquivos Finais")
    if not st.session_state.book:
        st.info("Repertório vazio.")
    else:
        st.markdown("<div class='row'>", unsafe_allow_html=True)
        
        # Função DOCX
        def get_docx():
            doc = Document()
            for m in st.session_state.book:
                doc.add_heading(m['titulo'], level=1)
                p = doc.add_paragraph(processar_texto(m["conteudo"], m["tom"], m["cols"]))
                p.style.font.name = 'Courier New'
                doc.add_page_break()
            buf = io.BytesIO()
            doc.save(buf)
            return buf.getvalue()

        # Botões
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("📑 Baixar Word (.docx)", get_docx(), "repertorio.docx", use_container_width=True)
        with c2:
            txt_book = "\n\n".join([f"== {m['titulo']} ==\n{processar_texto(m['conteudo'], m['tom'], '1 Coluna')}" for m in st.session_state.book])
            st.download_button("📝 Baixar Texto (.txt)", txt_book.encode("utf-8"), "repertorio.txt", use_container_width=True)
        with c3:
            st.download_button("📱 Formato Kindle (.txt)", txt_book.encode("utf-8"), "kindle.txt", use_container_width=True)
