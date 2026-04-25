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
        for m in re.finditer(r'\S+', linha):
            espacos = " " * (m.start() - pos)
            palavra = m.group()
            palavra_transp = "[" + transpor_acorde(palavra[1:-1], semitons) + "]" if palavra.startswith('[') else transpor_acorde(palavra, semitons)
            nova_linha += espacos + palavra_transp
            pos = m.start() + len(m.group())
        novo_texto.append(nova_linha)
    return '\n'.join(novo_texto)

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

# Transposição global na sidebar (opcional, pode ser zerada)
st.sidebar.divider()
st.sidebar.markdown("### 🎸 Ajuste de Tom")
c_tom1, c_tom2, c_tom3 = st.sidebar.columns(3)
if c_tom1.button("♭"): st.session_state.tom_ajuste -= 1
if c_tom2.button("0"): st.session_state.tom_ajuste = 0
if c_tom3.button("♯"): st.session_state.tom_ajuste += 1

# ====================== ADICIONAR MÚSICA ======================
if aba == "Adicionar Música":
    st.header("🔍 Importar e Personalizar")
    url = st.text_input("Link da cifra:", key=f"url_{st.session_state.limpador}")
    
    col_cap, col_mod1, col_mod2 = st.columns(3)
    with col_cap:
        if st.button("Capturar"):
            t, c = buscar_cifra(url)
            st.session_state.temp_titulo, st.session_state.temp_conteudo, st.session_state.original_conteudo = t, c, c
            st.rerun()
    with col_mod1:
        if st.button("📄 1 Coluna"): st.session_state.temp_conteudo = st.session_state.original_conteudo; st.rerun()
    with col_mod2:
        if st.button("✂️ 2 Colunas"): st.session_state.temp_conteudo = dividir_em_colunas(st.session_state.original_conteudo); st.rerun()

    st.divider()
    st.subheader("Configurações desta Música")
    
    # Botões de tamanho de letra exclusivos para a música que está sendo adicionada
    c_f1, c_f2, c_f3 = st.columns([1,1,4])
    if c_f1.button("A-"): st.session_state.fonte_atual_edicao -= 1
    if c_f3.button("A+"): st.session_state.fonte_atual_edicao += 1
    st.write(f"Tamanho da letra para esta música: **{st.session_state.fonte_atual_edicao}pt**")

    # Injeta CSS apenas para a área de texto de edição
    st.markdown(f"<style>textarea {{ font-size: {st.session_state.fonte_atual_edicao}pt !important; }}</style>", unsafe_allow_html=True)

    tit = st.text_input("Título:", value=st.session_state.temp_titulo)
    cif = st.text_area("Cifra (Editável):", value=processar_transposicao(st.session_state.temp_conteudo, st.session_state.tom_ajuste), height=400)
    
    if st.button("✅ Salvar no Book"):
        # Salva o tamanho da fonte junto com a música
        st.session_state.book.append({
            "titulo": tit, 
            "conteudo": cif, 
            "tamanho_fonte": st.session_state.fonte_atual_edicao
        })
        st.session_state.temp_titulo = ""
        st.session_state.temp_conteudo = ""
        st.session_state.fonte_atual_edicao = 11 # Reseta para a próxima
        st.session_state.limpador += 1
        st.success("Música salva com o tamanho escolhido!")
        time.sleep(0.5)
        st.rerun()

# ====================== VISUALIZAR BOOK ======================
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("Book vazio.")
    else:
        for i, m in enumerate(st.session_state.book):
            # Recupera o tamanho da fonte específico desta música
            f_size = m.get("tamanho_fonte", 11)
            linhas_por_pagina = int(600 / (f_size * 1.2))
            
            with st.expander(f"🎸 {m['titulo']} ({f_size}pt)", expanded=False):
                st.caption(f"Tamanho da fonte: {f_size}pt | Tom ajustado na visualização")
                
                conteudo = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                linhas = conteudo.split('\n')
                
                # Container Visual com a fonte específica da música
                st.markdown(f"""
                    <div class="page-container" style="font-family: 'Courier New', monospace; font-size: {f_size}pt; line-height: 1.2; white-space: pre;">
                    <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 10px;">{m['titulo']}</div>
                """, unsafe_allow_html=True)
                
                for idx, linha in enumerate(linhas):
                    st.write(linha) # Usar st.write dentro do container ou concatenar HTML
                    if (idx + 1) % linhas_por_pagina == 0 and (idx + 1) < len(linhas):
                        st.markdown('<div class="page-break-line"></div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button(f"🗑️ Excluir", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# ====================== EXPORTAR ======================
elif aba == "Exportar":
    st.header("📂 Exportar")
    if not st.session_state.book:
        st.warning("Adicione músicas.")
    else:
        nome_arq = st.text_input("Nome do arquivo:", "Meu_Repertorio").replace(" ", "_")
        st.write("Cada música será exportada com seu próprio tamanho de letra configurado.")
        
        c1, c2 = st.columns(2)
        with c1:
            doc = Document()
            for i, m in enumerate(st.session_state.book):
                if i > 0: doc.add_page_break()
                doc.add_heading(m['titulo'], 1)
                run = doc.add_paragraph().add_run(processar_transposicao(m['conteudo'], st.session_state.tom_ajuste))
                run.font.name = 'Courier New'
                run.font.size = Pt(m.get("tamanho_fonte", 11)) # USA O TAMANHO DA MÚSICA
            
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Word (.docx)", buf.getvalue(), f"{nome_arq}.docx")

        with c2:
            if st.button("Gerar PDF"):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
                    
                    # APLICA O TAMANHO ESPECÍFICO DA MÚSICA NO PDF
                    pdf.set_font("Courier", size=m.get("tamanho_fonte", 11))
                    
                    cif_transp = processar_transposicao(m['conteudo'], st.session_state.tom_ajuste)
                    pdf.multi_cell(0, 5, cif_transp.encode('latin-1', 'replace').decode('latin-1'))
                
                st.download_button("📥 PDF (.pdf)", pdf.output(dest='S'), f"{nome_arq}.pdf")
