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
    .stButton > button { width: 100%; border-radius: 5px; }
    /* Estilo para os botões de fonte ficarem menores e lado a lado */
    .font-btn > div { padding: 0px 5px; }
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
if 'tom_ajuste' not in st.session_state:
    st.session_state.tom_ajuste = 0
if 'tamanho_fonte' not in st.session_state:
    st.session_state.tamanho_fonte = 11  # Tamanho padrão inicial

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
    st.session_state.temp_titulo = ""
    st.session_state.temp_conteudo = ""
    st.session_state.original_conteudo = ""
    st.session_state.limpador += 1

def buscar_cifra(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        titulo_tag = soup.find('h1', class_='t1') or soup.find('h1', class_='t3') or soup.find('h1')
        titulo = titulo_tag.get_text().strip() if titulo_tag else ""
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

# --- CONTROLES GERAIS (Sidebar) ---
st.sidebar.divider()
st.sidebar.markdown("### 🎸 Ajustes de Visualização")

# Ajuste de Tom
st.sidebar.write("Transposição:")
c_tom1, c_tom2, c_tom3 = st.sidebar.columns(3)
if c_tom1.button("♭"): st.session_state.tom_ajuste -= 1
if c_tom2.button("0"): st.session_state.tom_ajuste = 0
if c_tom3.button("♯"): st.session_state.tom_ajuste += 1
st.sidebar.caption(f"Tom atual: {st.session_state.tom_ajuste} semitons")

# Ajuste de Tamanho da Fonte (Estilo Word)
st.sidebar.write("Tamanho da Letra:")
c_f1, c_f2, c_f3 = st.sidebar.columns(3)
if c_f1.button("A-"): 
    if st.session_state.tamanho_fonte > 6: st.session_state.tamanho_fonte -= 1
if c_f2.button("11"): # Reset para o padrão
    st.session_state.tamanho_fonte = 11
if c_f3.button("A+"): 
    if st.session_state.tamanho_fonte < 30: st.session_state.tamanho_fonte += 1
st.sidebar.caption(f"Fonte atual: {st.session_state.tamanho_fonte}pt")

# Injeta CSS dinâmico para o tamanho da letra na área de edição/visualização
st.markdown(f"""
    <style>
    .stTextArea textarea {{ font-size: {st.session_state.tamanho_fonte}pt !important; }}
    code {{ font-size: {st.session_state.tamanho_fonte}pt !important; }}
    </style>
    """, unsafe_allow_html=True)

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Importar e Personalizar")
    url = st.text_input("Link da cifra:", key=f"url_in_{st.session_state.limpador}")
    
    col_cap, col_div2, col_div1 = st.columns(3)
    with col_cap:
        if st.button("Capturar Dados"):
            if url:
                t, c = buscar_cifra(url)
                st.session_state.temp_titulo, st.session_state.temp_conteudo = t, c
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

    titulo_editado = st.text_input("Título da Música:", value=st.session_state.temp_titulo)
    conteudo_visivel = processar_transposicao(st.session_state.temp_conteudo, st.session_state.tom_ajuste)
    conteudo_editado = st.text_area("Cifra (Editável):", value=conteudo_visivel, height=450)
    
    if st.button("✅ Salvar no meu Book"):
        if titulo_editado.strip() and conteudo_editado.strip():
            st.session_state.book.append({"titulo": titulo_editado.strip(), "conteudo": conteudo_editado})
            st.success(f"'{titulo_editado}' salva!")
            time.sleep(0.5)
            limpar_campos()
            st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("Seu book está vazio.")
    else:
        for i, m in enumerate(st.session_state.book):
            with st.expander(f"🎸 {m['titulo']}"):
                display = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                st.code(display, language=None)
                if st.button(f"Excluir {m['titulo']}", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar Arquivos")
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        nome_proj = st.text_input("Nome do Livro:", value="Meu Repertorio")
        nome_arq = nome_proj.replace(" ", "_").lower()
        
        st.info(f"O arquivo será gerado com Fonte tamanho **{st.session_state.tamanho_fonte}**.")
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # TXT
            txt = f"{nome_proj.upper()}\n" + ("="*30) + "\n\n"
            for m in st.session_state.book:
                txt += f"{m['titulo'].upper()}\n\n{processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)}\n\n"
                txt += f"{'-'*50}\n\n"
            st.download_button("📥 Baixar TXT", txt, f"{nome_arq}.txt")
            
        with c2:
            # WORD (DOCX)
            doc = Document()
            for s in doc.sections:
                s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(0.5)
            doc.add_heading(nome_proj, 0)
            for i, m in enumerate(st.session_state.book):
                if i > 0: doc.add_page_break()
                doc.add_heading(m['titulo'], 1)
                p = doc.add_paragraph()
                run = p.add_run(processar_transposicao(m['conteudo'], st.session_state.tom_ajuste))
                run.font.name = 'Courier New'
                run.font.size = Pt(st.session_state.tamanho_fonte) # AQUI APLICA O TAMANHO
            
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Baixar DOCX", buf.getvalue(), f"{nome_arq}.docx")
            
        with c3:
            # PDF
            if st.button("Gerar PDF"):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
                    pdf.ln(4)
                    # AQUI APLICA O TAMANHO NO PDF
                    pdf.set_font("Courier", size=st.session_state.tamanho_fonte)
                    txt_p = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                    pdf.multi_cell(0, 5, txt_p.encode('latin-1', 'replace').decode('latin-1'))
                
                pdf_out = pdf.output(dest='S')
                if not isinstance(pdf_out, bytes): pdf_out = pdf_out.encode('latin-1')
                st.download_button("📥 Baixar PDF", pdf_out, f"{nome_arq}.pdf")
