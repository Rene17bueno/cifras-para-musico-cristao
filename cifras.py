# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re

# ----------------------------------
# CONFIG
# ----------------------------------
st.set_page_config(
page_title="Music Book Pro",
page_icon="🎸",
layout="wide"
)

st.markdown("""
<style>

textarea, pre{
font-family:'Courier New', monospace !important;
white-space:pre !important;
line-height:1 !important;
}

.stButton > button{
width:100%;
border-radius:6px;
}

.page-container{
background:#0e1117;
padding:20px;
border-radius:10px;
border:1px solid #333;
margin-bottom:15px;
color:white;
}

.cifra-renderizada{
font-family:'Courier New', monospace !important;
font-size:inherit !important;
white-space:pre !important;
line-height:1 !important;
margin:0 !important;
padding:0 !important;
display:block;
}

div[data-testid="stMarkdownContainer"] p{
margin-top:0 !important;
margin-bottom:0 !important;
}

</style>
""",unsafe_allow_html=True)


# ----------------------------------
# SESSION
# ----------------------------------
if "book" not in st.session_state:
    st.session_state.book=[]

if "limpador" not in st.session_state:
    st.session_state.limpador=0

if "musica_focada" not in st.session_state:
    st.session_state.musica_focada=None

if "temp_titulo" not in st.session_state:
    st.session_state.temp_titulo=""

if "temp_conteudo" not in st.session_state:
    st.session_state.temp_conteudo=""


# ----------------------------------
# TRANSPOSIÇÃO
# ----------------------------------
NOTAS=[
"C","C#","D","D#","E",
"F","F#","G","G#",
"A","A#","B"
]

def transpor_acorde(acorde,semitons):

    def substituir(match):

        nota=match.group(1)
        resto=match.group(2)

        if nota in NOTAS:
            i=(NOTAS.index(nota)+semitons)%12
            return NOTAS[i]+resto

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

            nova += (
                " "*(m.start()-pos)
                +transpor_acorde(
                    m.group(),
                    semitons
                )
            )

            pos=m.start()+len(m.group())

        linhas_t.append(
            nova + (
                " "*(len(linha)-pos)
            )
        )


    if colunas=="2 Colunas":

        total=len(linhas_t)

        meio=(total//2)+(total%2)

        col1=linhas_t[:meio]
        col2=linhas_t[meio:]

        largura=max(
            len(x)
            for x in col1
        ) if col1 else 0

        final=[]

        for i in range(
            max(
                len(col1),
                len(col2)
            )
        ):

            a=col1[i] if i<len(col1) else ""
            b=col2[i] if i<len(col2) else ""

            final.append(
                a.ljust(largura+8)+b
            )

        return "\n".join(final)


    return "\n".join(linhas_t)



# ----------------------------------
# SIDEBAR
# ----------------------------------
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
"### 🎸 Ajustes da Música"
)


# ----------------------------------
# CONTROLES
# ----------------------------------
def ajustar_fonte(delta):

    if st.session_state.musica_focada is not None:

        idx=st.session_state.musica_focada

        atual=st.session_state.book[idx]["fonte"]

        novo=max(
            8,
            min(
                32,
                atual+delta
            )
        )

        st.session_state.book[idx]["fonte"]=novo


def set_fonte(valor):
    if st.session_state.musica_focada is not None:
        idx=st.session_state.musica_focada
        st.session_state.book[idx]["fonte"]=valor


def ajustar_tom(delta):
    if st.session_state.musica_focada is not None:
        idx=st.session_state.musica_focada
        st.session_state.book[idx]["tom"]+=delta


def set_tom(v):
    if st.session_state.musica_focada is not None:
        idx=st.session_state.musica_focada
        st.session_state.book[idx]["tom"]=v


def set_layout(modo):
    if st.session_state.musica_focada is not None:
        idx=st.session_state.musica_focada
        st.session_state.book[idx]["cols"]=modo


# FONTE
st.sidebar.write("Tamanho:")

a,b,c=st.sidebar.columns(3)

a.button(
"A-",
on_click=ajustar_fonte,
args=(-1,)
)

b.button(
"11",
on_click=set_fonte,
args=(11,)
)

c.button(
"A+",
on_click=ajustar_fonte,
args=(1,)
)


# TOM
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


# LAYOUT
st.sidebar.write("Layout:")

l1,l2=st.sidebar.columns(2)

l1.button(
"📄1 Col",
on_click=set_layout,
args=("1 Coluna",)
)

l2.button(
"✂️2 Col",
on_click=set_layout,
args=("2 Colunas",)
)



# ----------------------------------
# ADICIONAR
# ----------------------------------
if aba=="Adicionar Música":

    st.header("🔍 Capturar Cifra")

    url=st.text_input(
        "Link da cifra:",
        key=f"url_{st.session_state.limpador}"
    )

    if st.button("Capturar"):

        try:

            r=requests.get(
                url,
                headers={
                "User-Agent":"Mozilla/5.0"
                },
                timeout=10
            )

            soup=BeautifulSoup(
                r.text,
                "html.parser"
            )

            titulo=(
                soup.find(
                    "h1",
                    class_="t1"
                )
                or
                soup.find("h1")
            ).get_text().strip()

            cifra=soup.find(
                "pre"
            ).get_text()

            st.session_state.temp_titulo=titulo
            st.session_state.temp_conteudo=cifra

            st.rerun()

        except:
            st.error(
                "Erro ao capturar"
            )


    st.divider()

    tit=st.text_input(
        "Título",
        value=st.session_state.temp_titulo
    )

    cif=st.text_area(
        "Cifra",
        value=st.session_state.temp_conteudo,
        height=300
    )


    if st.button(
        "Adicionar ao repertório"
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

        st.success("Adicionado")
        st.rerun()



# ----------------------------------
# VISUALIZAR
# ----------------------------------
elif aba=="Visualizar Book":

    st.header("📖 Meu Repertório")

    if not st.session_state.book:
        st.info("Book vazio")

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


                texto=processar_texto(
                    m["conteudo"],
                    m["tom"],
                    m["cols"]
                )

                st.markdown(
f"""
<div class='page-container'>
<div style='
font-family:Courier New;
font-size:{m["fonte"]}pt;
line-height:1;
'>
""",
unsafe_allow_html=True
                )

                st.markdown(
f"### {m['titulo']}"
                )

                bloco=""

                for linha in texto.split("\n"):

                    if linha.strip()=="":
                        linha=" "

                    html=linha.replace(
                        " ",
                        "&nbsp;"
                    )

                    bloco+=f"""
<div class='cifra-renderizada'>
{html}
</div>
"""

                st.markdown(
                    bloco,
                    unsafe_allow_html=True
                )

                st.markdown(
"""
</div>
</div>
""",
unsafe_allow_html=True
                )

                if st.button(
                    "🗑️Excluir",
                    key=f"del{i}"
                ):
                    st.session_state.book.pop(i)
                    st.session_state.musica_focada=None
                    st.rerun()



# ----------------------------------
# EXPORTAR
# ----------------------------------
elif aba=="Exportar":

    st.header(
        "📂 Exportar Livro"
    )

    if st.session_state.book:

        if st.button(
            "Gerar PDF"
        ):

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
                    m["titulo"],
                    ln=True
                )

                pdf.set_font(
                    "Courier",
                    size=m["fonte"]
                )

                texto=processar_texto(
                    m["conteudo"],
                    m["tom"],
                    m["cols"]
                )

                pdf.multi_cell(
                    0,
                    4,
                    texto
                )

            arquivo=bytes(
                pdf.output(
                    dest="S"
                )
            )

            st.download_button(
                "📥 Baixar PDF",
                data=arquivo,
                file_name="MeuRepertorio.pdf",
                mime="application/pdf"
            )
