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
        conteudo = corpo.get_text() if corpo else ""
        
        return titulo, conteudo
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

opcoes_tons = ["-3 (G#)", "-2 (A)", "-1 (A#)", "0 (Tom Original)",
                "+1 (C)", "+2 (C#)", "+3 (D)", "+4 (D#)", "+5 (E)", "+6 (F)"]

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Importar e Personalizar")
    
    c_id = st.session_state.limpador
    url = st.text_input("Link da cifra (ex: Cifra Club):", key=f"url_{c_id}")
    
    col_cap, col_div2, col_div1 = st.columns(3)
    with col_cap:
        if st.button("Capturar Dados"):
            t, c = buscar_cifra(url)
            if t:
                st.session_state.temp_titulo = t
                st.session_state.temp_conteudo = c
                st.session_state.original_conteudo = c
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
    
    tom_selecionado = st.sidebar.selectbox("🎸 Transpor Tonalidade", opcoes_tons, index=3)
    match_tom = re.search(r"([+-]?\d+)", tom_selecionado)
    tom_ajuste = int(match_tom.group(1)) if match_tom else 0
    
    conteudo_visivel = processar_transposicao(st.session_state.temp_conteudo, tom_ajuste)
    conteudo_f = st.text_area("Cifra (Editável):", value=conteudo_visivel, height=500)
    
    if st.button("✅ Salvar no meu Book"):
        if titulo_f.strip() and conteudo_f.strip():
            st.session_state.book.append({
                "titulo": titulo_f.strip(),
                "conteudo": conteudo_f
            })
            st.success(f"'{titulo_f}' salva com sucesso!")
            time.sleep(0.5)
            limpar_campos()
            st.rerun()
        else:
            st.warning("Preencha o título e a cifra antes de salvar.")

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("Seu book ainda está vazio.")
    else:
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']}"):
                st.code(m['conteudo'], language=None)
                if st.button(f"🗑️ Excluir música", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar Arquivos")
    
    if not st.session_state.book:
        st.warning("Adicione músicas antes de exportar.")
    else:
        nome_proj = st.text_input("Título do Projeto:", value="Meu Repertorio")
        nome_arq = nome_proj.replace(" ", "_").lower()
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # Exportação TXT
            txt = f"{nome_proj.upper()}\n" + ("="*40) + "\n\n"
            for m in st.session_state.book:
                txt += f"{m['titulo'].upper()}\n\n{m['conteudo']}\n\n"
                txt += f"{'-'*60}\n\n"
            st.download_button("📥 Baixar TXT", txt, f"{nome_arq}.txt", mime="text/plain")
        
        with c2:
            # Exportação DOCX (Word)
            doc = Document()
            for s in doc.sections:
                s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(0.5)
            
            doc.add_heading(nome_proj, 0)
            
            for i, m in enumerate(st.session_state.book):
                if i > 0:
                    doc.add_page_break() # Força nova música em nova página
                
                doc.add_heading(m['titulo'], 1)
                p = doc.add_paragraph()
                run = p.add_run(m['conteudo'])
                run.font.name = 'Courier New'
                run.font.size = Pt(10)
            
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Baixar DOCX", buf.getvalue(), f"{nome_arq}.docx")
        
        with c3:
            # Exportação PDF
            if st.button("Gerar PDF"):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                for m in st.session_state.book:
                    pdf.add_page() # Inicia cada música em uma nova página
                    
                    # Título
                    pdf.set_font("Courier", 'B', 14)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
                    pdf.ln(5)
                    
                    # Cifra
                    pdf.set_font("Courier", size=10)
                    texto = m['conteudo']
                    # O multi_cell cuida de quebrar a página se a música for maior que 1 folha
                    pdf.multi_cell(0, 5, texto.encode('latin-1', 'replace').decode('latin-1'))
                
                pdf_output = pdf.output(dest='S')
                if not isinstance(pdf_output, bytes):
                    pdf_output = pdf_output.encode('latin-1')
                
                st.download_button("📥 Baixar PDF", pdf_output, f"{nome_arq}.pdf", mime="application/pdf")
