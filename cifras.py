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
# CONFIG E ESTILOS
# -------------------------------------------------
st.set_page_config(page_title="Music Book Pro", page_icon="🎸", layout="wide")

st.markdown("""
<style>
    .a4-preview {
        background-color: white;
        color: black;
        width: 100%;
        max-width: 800px; /* Simulação de proporção A4 */
        min-height: 500px;
        padding: 40px;
        margin: auto;
        border: 2px solid #ddd;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        font-family: 'Courier New', Courier, monospace;
        overflow-x: auto;
        position: relative;
    }
    .overflow-warning {
        border: 2px solid #ff4b4b !important;
    }
    .warning-text {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 0.8em;
        margin-bottom: 5px;
    }
    .cifra-line {
        white-space: pre;
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LÓGICA DE NEGÓCIO (Transposição e Verificação)
# -------------------------------------------------
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def transpor_acorde(acorde, semitons):
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
        meio = (len(linhas_t) // 2) + (len(linhas_t) % 2)
        esq, dir = linhas_t[:meio], linhas_t[meio:]
        largura = max(len(x) for x in esq) if esq else 0
        return "\n".join([(esq[i] if i<len(esq) else "").ljust(largura + 6) + (dir[i] if i<len(dir) else "") for i in range(max(len(esq), len(dir)))])
    
    return "\n".join(linhas_t)

def verificar_estouro(texto, fonte):
    # Estimativa simples: Em Courier (monospaçada), cada caractere tem ~0.6 do tamanho da fonte em largura
    # Uma folha A4 tem 210mm. Com margens, sobram ~180mm.
    max_chars = int(180 / (fonte * 0.3527 * 0.6)) # conversão pt para mm aproximada
    linhas = texto.split('\n')
    if not linhas: return False
    maior_linha = max(len(l) for l in linhas)
    return maior_linha > max_chars

# -------------------------------------------------
# INICIALIZAÇÃO DE ESTADO
# -------------------------------------------------
for key in ["book", "musica_focada", "temp_titulo", "temp_conteudo"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "book" else None if key == "musica_focada" else ""

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("🎸 Music Book Pro")
aba = st.sidebar.radio("Menu", ["Adicionar Música", "Visualizar & Editar", "Exportar"])

if st.session_state.musica_focada is not None and aba == "Visualizar & Editar":
    st.sidebar.divider()
    st.sidebar.subheader("🛠️ Ajustar Selecionada")
    idx = st.session_state.musica_focada
    
    # Controles diretos no State
    st.session_state.book[idx]["fonte"] = st.sidebar.slider("Tamanho da Fonte", 8, 24, st.session_state.book[idx]["fonte"])
    st.session_state.book[idx]["tom"] = st.sidebar.number_input("Transpor (Semitons)", -12, 12, st.session_state.book[idx]["tom"])
    st.session_state.book[idx]["cols"] = st.sidebar.selectbox("Colunas", ["1 Coluna", "2 Colunas"], 
                                                             index=0 if st.session_state.book[idx]["cols"] == "1 Coluna" else 1)

# -------------------------------------------------
# ABA: ADICIONAR
# -------------------------------------------------
if aba == "Adicionar Música":
    st.header("➕ Nova Cifra")
    url = st.text_input("URL CifraClub (Opcional)")
    if st.button("Importar Link"):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            st.session_state.temp_titulo = (soup.find("h1", class_="t1") or soup.find("h1")).get_text()
            st.session_state.temp_conteudo = soup.find("pre").get_text()
            st.success("Capturado!")
        except: st.error("Erro ao importar.")

    tit = st.text_input("Título", value=st.session_state.temp_titulo)
    cif = st.text_area("Conteúdo", value=st.session_state.temp_conteudo, height=300)
    
    if st.button("Salvar no Repertório"):
        st.session_state.book.append({"titulo": tit, "conteudo": cif, "fonte": 12, "tom": 0, "cols": "1 Coluna"})
        st.session_state.temp_titulo = ""; st.session_state.temp_conteudo = ""
        st.rerun()

# -------------------------------------------------
# ABA: VISUALIZAR (O "CORAÇÃO" DO PROGRAMA)
# -------------------------------------------------
elif aba == "Visualizar & Editar":
    st.header("📖 Visual Book (Preview A4)")
    
    if not st.session_state.book:
        st.info("Repertório vazio.")
    else:
        # Lista de seleção rápida
        titulos = [f"{i+1}. {m['titulo']}" for i, m in enumerate(st.session_state.book)]
        escolha = st.selectbox("Selecione para editar/ver:", titulos, 
                               index=st.session_state.musica_focada if st.session_state.musica_focada is not None else 0)
        st.session_state.musica_focada = titulos.index(escolha)
        
        m = st.session_state.book[st.session_state.musica_focada]
        texto_renderizado = processar_texto(m["conteudo"], m["tom"], m["cols"])
        estourou = verificar_estouro(texto_renderizado, m["fonte"])
        
        if estourou:
            st.warning("⚠️ Atenção: A cifra está muito larga para a largura da página A4. Diminua a fonte ou use 1 coluna.")
        
        # Renderização do "Papel"
        warning_class = "overflow-warning" if estourou else ""
        
        html_content = f"<h3>{m['titulo']}</h3>"
        for linha in texto_renderizado.split('\n'):
            linha_html = linha.replace(" ", "&nbsp;")
            html_content += f"<div class='cifra-line' style='font-size:{m['fonte']}pt;'>{linha_html if linha_html.strip() else '&nbsp;'}</div>"
            
        st.markdown(f"""
            <div class='a4-preview {warning_class}'>
                {html_content}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Excluir Música"):
            st.session_state.book.pop(st.session_state.musica_focada)
            st.session_state.musica_focada = None
            st.rerun()

# -------------------------------------------------
# ABA: EXPORTAR
# -------------------------------------------------
elif aba == "Exportar":
    st.header("💾 Exportar Arquivos")
    if not st.session_state.book:
        st.info("Nada para exportar.")
    else:
        # Função interna para gerar PDF corrigida
        def generate_pdf():
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            for m in st.session_state.book:
                pdf.add_page()
                # Título
                pdf.set_font("Courier", "B", 16)
                pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                # Conteúdo
                pdf.set_font("Courier", size=m['fonte'])
                texto = processar_texto(m["conteudo"], m["tom"], m["cols"])
                pdf.multi_cell(0, 5, texto.encode('latin-1', 'replace').decode('latin-1'))
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("Baixar PDF Pro", data=generate_pdf(), file_name="repertorio.pdf", mime="application/pdf")
        
        if st.button("Preparar outros formatos (Docx/Zip)"):
            st.info("Processando arquivos pesados...")
            # Aqui você pode manter suas funções originais de DOCX e ZIP
