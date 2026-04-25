# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re

# -----------------------------------
# CONFIGURAÇÃO
# -----------------------------------
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
}

.stButton > button{
    width:100%;
    border-radius:5px;
}

.page-container{
    background:#0e1117;
    padding:30px;
    border-radius:10px;
    border:1px solid #333;
    color:white;
    line-height:1.2;
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# INICIALIZAÇÃO (CORRIGIDO)
# -----------------------------------
if 'book' not in st.session_state:
    st.session_state.book = []

if 'limpador' not in st.session_state:
    st.session_state.limpador = 0

if 'musica_focada' not in st.session_state:
    st.session_state.musica_focada = None

# CORREÇÃO PRINCIPAL
if 'temp_titulo' not in st.session_state:
    st.session_state.temp_titulo = ""

if 'temp_conteudo' not in st.session_state:
    st.session_state.temp_conteudo = ""

# -----------------------------------
# TRANSPOSIÇÃO
# -----------------------------------
NOTAS = [
'C','C#','D','D#','E',
'F','F#','G','G#','A','A#','B'
]

def transpor_acorde(acorde,semitons):

    def substituir(match):
        nota_original=match.group(1)
        acessorio=match.group(2)

        if nota_original in NOTAS:
            idx=(NOTAS.index(nota_original)+semitons)%12
            return NOTAS[idx]+acessorio

        return match.group(0)

    return re.sub(
        r'([A-G]#?)([^A-G\s]*)',
        substituir,
        acorde
    )


def processar_texto(texto,semitons,colunas):

    if not texto:
        return ""

    linhas=texto.split("\n")

    linhas_t=[]

    for linha in linhas:
        nova=""
        pos=0

        for m in re.finditer(r'\S+',linha):

            nova+=(
                " "*(m.start()-pos)
                +transpor_acorde(
                    m.group(),
                    semitons
                )
            )

            pos=m.start()+len(m.group())

        linhas_t.append(
            nova+(" "*(len(linha)-pos))
        )


    if colunas=="2 Colunas":

        total=len(linhas_t)

        meio=(total//2)+(total%2)

        if (
            meio<total and
            len(
                re.findall(
                    r'[A-G][b#]?[a-z0-9]*',
                    linhas_t[meio]
                )
            )>0
        ):
            meio+=1

        col_esq=linhas_t[:meio]
        col_dir=linhas_t[meio:]

        larg_max=max(
            [len(l) for l in col_esq]
        ) if col_esq else 0

        final=[]

        for i in range(
            max(
                len(col_esq),
                len(col_dir)
            )
        ):

            e=col_esq[i] if i<len(col_esq) else ""
            d=col_dir[i] if i<len(col_dir) else ""

            final.append(
                f"{e.ljust(larg_max+8)}{d}"
            )

        return "\n".join(final)

    return "\n".join(linhas_t)


# -----------------------------------
# SIDEBAR
# -----------------------------------
st.sidebar.title("🎵 Music Book")

aba=st.sidebar.radio(
"Navegação",
[
"Adicionar Música",
"Visualizar Book",
"Exportar"
]
)

st.sidebar.divider()
st.sidebar.markdown(
"### 🛠️ Ajustes da Música Selecionada"
)

def ajustar_fonte(delta):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]['fonte']+=delta


def set_fonte(valor):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]['fonte']=valor


def ajustar_tom(delta):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]['tom']+=delta


def set_tom(valor):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]['tom']=valor


def set_layout(modo):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]['cols']=modo


st.sidebar.write("Tamanho da Letra:")
c1,c2,c3=st.sidebar.columns(3)

c1.button(
"A-",
on_click=ajustar_fonte,
args=(-1,)
)

c2.button(
"11",
on_click=set_fonte,
args=(11,)
)

c3.button(
"A+",
on_click=ajustar_fonte,
args=(1,)
)


st.sidebar.write("Tom:")
t1,t2,t3=st.sidebar.columns(3)

t1.button(
"♭",
on_click=ajustar_tom,
args=(-1,)
)

t2.button(
"0",
on_click=set_tom,
args=(0,)
)

t3.button(
"♯",
on_click=ajustar_tom,
args=(1,)
)


st.sidebar.write("Layout:")
l1,l2=st.sidebar.columns(2)

l1.button(
"📄 1 Col",
on_click=set_layout,
args=("1 Coluna",)
)

l2.button(
"✂️ 2 Col",
on_click=set_layout,
args=("2 Colunas",)
)


# -----------------------------------
# ADICIONAR
# -----------------------------------
if aba=="Adicionar Música":

    st.header("🔍 Capturar Cifra")

    url=st.text_input(
        "Link da cifra:",
        key=f"url_{st.session_state.limpador}"
    )

    if st.button("Capturar"):

        try:
            res=requests.get(
                url,
                headers={
                    'User-Agent':'Mozilla/5.0'
                },
                timeout=10
            )

            res.encoding=res.apparent_encoding

            soup=BeautifulSoup(
                res.text,
                'html.parser'
            )

            t=(
                soup.find(
                    'h1',
                    class_='t1'
                )
                or
                soup.find('h1')
            ).get_text().strip()

            c=soup.find(
                'pre'
            ).get_text()

            st.session_state.temp_titulo=t
            st.session_state.temp_conteudo=c

            st.rerun()

        except:
            st.error(
                "Erro ao capturar."
            )

    st.divider()

    tit=st.text_input(
        "Título:",
        value=st.session_state.temp_titulo
    )

    cif=st.text_area(
        "Cifra (Original):",
        value=st.session_state.temp_conteudo,
        height=300
    )

    if st.button(
        "✅ Adicionar ao Repertório"
    ):

        st.session_state.book.append({
            "titulo":tit,
            "conteudo":cif,
            "fonte":12,
            "tom":0,
            "cols":"1 Coluna"
        })

        st.session_state.temp_titulo=""
        st.session_state.temp_conteudo=""
        st.session_state.limpador+=1

        st.success("Adicionado!")
        st.rerun()


# -----------------------------------
# VISUALIZAR
# -----------------------------------
elif aba=="Visualizar Book":

    st.header("📖 Meu Repertório")

    if not st.session_state.book:
        st.info("O book está vazio.")

    else:

        for i,m in enumerate(
            st.session_state.book
        ):

            with st.expander(
                f"🎸 {m['titulo']} ({m['fonte']}pt | Tom:{m['tom']})",
                expanded=(
                    st.session_state.musica_focada==i
                )
            ):

                if st.session_state.musica_focada!=i:
                    st.session_state.musica_focada=i
                    st.rerun()

                texto_proc=processar_texto(
                    m['conteudo'],
                    m['tom'],
                    m['cols']
                )

                st.markdown(
f'<div class="page-container" style="font-size:{m["fonte"]}pt;">',
unsafe_allow_html=True
                )

                st.markdown(
                    f"### {m['titulo']}"
                )

                bloco=""

                for linha in texto_proc.split("\n"):

                    l_html=linha.replace(
                        " ",
                        "&nbsp;"
                    )

                    bloco+=f'''
<div class="cifra-renderizada">
{l_html if l_html else "&nbsp;"}
</div>
'''

                st.markdown(
                    bloco,
                    unsafe_allow_html=True
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

                if st.button(
                    "🗑️ Excluir Música",
                    key=f"del_{i}"
                ):
                    st.session_state.book.pop(i)
                    st.session_state.musica_focada=None
                    st.rerun()


# -----------------------------------
# EXPORTAR
# -----------------------------------
elif aba=="Exportar":

    st.header("📂 Exportar Livro")

    if st.session_state.book:

        if st.button("Gerar PDF"):

            pdf=FPDF()

            for m in st.session_state.book:

                pdf.add_page()

                pdf.set_font(
                    "Courier",
                    "B",
                    14
                )

                pdf.cell(
                    0,
                    10,
                    m['titulo'].encode(
                        'latin-1',
                        'replace'
                    ).decode(
                        'latin-1'
                    ),
                    ln=True
                )

                pdf.set_font(
                    "Courier",
                    size=m['fonte']
                )

                txt=processar_texto(
                    m['conteudo'],
                    m['tom'],
                    m['cols']
                )

                pdf.multi_cell(
                    0,
                    5,
                    txt.encode(
                        'latin-1',
                        'replace'
                    ).decode(
                        'latin-1'
                    )
                )

            # CORREÇÃO PDF
            pdf_bytes=bytes(
                pdf.output(dest='S')
            )

            st.download_button(
                "📥 Baixar PDF",
                data=pdf_bytes,
                file_name="MeuRepertorio.pdf",
                mime="application/pdf"
            )
