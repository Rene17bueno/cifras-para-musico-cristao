# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from docx import Document
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Music Book Pro", page_icon="🎸", layout="wide")

if 'book' not in st.session_state:
    st.session_state.book = []

# --- FUNÇÕES CORE ---

def buscar_cifra(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        
        titulo_tag = soup.find('h1', class_='t1') or soup.find('h1', class_='t3') or soup.find('h1')
        titulo = titulo_tag.get_text().strip() if titulo_tag else ""
        
        if not titulo or "Cifra Club" in titulo:
            titulo = soup.title.string.split('-')[0].strip() if soup.title else "Nova Música"

        corpo = soup.find('pre')
        texto = corpo.get_text() if corpo else ""
        
        return titulo, texto
    except:
        return "", ""

# --- INTERFACE ---
st.sidebar.title("🎵 Music Book")
aba = st.sidebar.radio("Navegação", ["Adicionar Música", "Visualizar Book", "Exportar"])

# --- ABA 1: ADICIONAR ---
if aba == "Adicionar Música":
    st.header("🔍 Importar e Personalizar")
    url = st.text_input("Link da cifra (ex: Cifra Club):")
    
    col_cap, col_edit = st.columns(2)
    
    with col_cap:
        if st.button("Capturar Dados do Link"):
            t, c = buscar_cifra(url)
            st.session_state['temp_titulo'] = t
            st.session_state['temp_conteudo'] = c

    titulo_personalizado = st.text_input("Confirmar/Editar Título:", value=st.session_state.get('temp_titulo', ""))
    conteudo_personalizado = st.text_area("Conteúdo da Cifra:", value=st.session_state.get('temp_conteudo', ""), height=300)

    if st.button("✅ Salvar no meu Book"):
        if titulo_personalizado and conteudo_personalizado:
            st.session_state.book.append({
                "titulo": titulo_personalizado, 
                "conteudo": conteudo_personalizado
            })
            st.success("Música salva!")
            st.session_state['temp_titulo'] = ""
            st.session_state['temp_conteudo'] = ""
        else:
            st.error("Preencha o título e o conteúdo.")

# --- ABA 2: VISUALIZAR ---
elif aba == "Visualizar Book":
    st.header("📖 Meu Repertório")
    if not st.session_state.book:
        st.info("O book está vazio.")
    else:
        for i, musica in enumerate(st.session_state.book):
            with st.expander(f"🎸 {musica['titulo']}"):
                st.subheader(musica['titulo'])
                st.code(musica['conteudo'], language=None)
                if st.button(f"Excluir Música", key=f"del_{i}"):
                    st.session_state.book.pop(i)
                    st.rerun()

# --- ABA 3: EXPORTAR ---
elif aba == "Exportar":
    st.header("📂 Opções de Exportação")
    if not st.session_state.book:
        st.warning("Adicione músicas primeiro.")
    else:
        # --- NOVO CAMPO DE NOME DO ARQUIVO/PROJETO ---
        nome_projeto = st.text_input("Nome do Arquivo / Título do Repertório:", value="Meu Repertorio")
        nome_arquivo_limpo = nome_projeto.replace(" ", "_").lower()
        
        st.divider()
        col1, col2, col3 = st.columns(3)

        # TXT Simples
        with col1:
            st.write("### TXT")
            txt_output = f"{nome_projeto.upper()}\n{'='*len(nome_projeto)}\n\n"
            for m in st.session_state.book:
                txt_output += f"{m['titulo'].upper()}\n\n{m['conteudo']}\n\n{'-'*40}\n\n"
            st.download_button("📥 Baixar .TXT", txt_output, f"{nome_arquivo_limpo}.txt")

        # WORD (.DOCX)
        with col2:
            st.write("### Word")
            doc = Document()
            doc.add_heading(nome_projeto, 0) # Título principal do arquivo
            for m in st.session_state.book:
                doc.add_heading(m['titulo'], 1)
                p = doc.add_paragraph()
                run = p.add_run(m['conteudo'])
                run.font.name = 'Courier New'
                doc.add_page_break()
            buf_word = io.BytesIO()
            doc.save(buf_word)
            st.download_button("📥 Baixar .DOCX", buf_word.getvalue(), f"{nome_arquivo_limpo}.docx")

        # PDF EM 2 COLUNAS
        with col3:
            st.write("### PDF (2 Colunas)")
            if st.button("Gerar PDF Especial"):
                pdf = FPDF()
                # Capa ou Título Inicial
                pdf.add_page()
                pdf.set_font("Courier", 'B', 20)
                pdf.cell(0, 50, nome_projeto.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
                
                for m in st.session_state.book:
                    pdf.add_page()
                    pdf.set_font("Courier", 'B', 14)
                    pdf.cell(0, 10, m['titulo'].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
                    pdf.ln(2)
                    
                    pdf.set_font("Courier", size=8)
                    linhas = m['conteudo'].split('\n')
                    meio = (len(linhas) // 2) + 1
                    col_esquerda = "\n".join(linhas[:meio])
                    col_direita = "\n".join(linhas[meio:])
                    
                    y_inicial = pdf.get_y()
                    pdf.set_xy(10, y_inicial)
                    pdf.multi_cell(95, 4, col_esquerda.encode('latin-1', 'replace').decode('latin-1'))
                    
                    pdf.set_xy(105, y_inicial)
                    pdf.multi_cell(95, 4, col_direita.encode('latin-1', 'replace').decode('latin-1'))
                
                st.download_button("📥 Baixar PDF", bytes(pdf.output(dest='S')), f"{nome_arquivo_limpo}.pdf")
