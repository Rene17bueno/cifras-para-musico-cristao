# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import re

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
line-height:1 !important;
}

.stButton > button{
width:100%;
border-radius:5px;
}

.page-container{
background:#0e1117;
padding:20px;
border-radius:10px;
border:1px solid #333;
color:white;
margin-bottom:20px;
}

.cifra-renderizada{
font-family:'Courier New', monospace !important;
font-size:inherit !important;
line-height:1 !important;
margin:0 !important;
padding:0 !important;
display:block;
}

div[data-testid="stMarkdownContainer"] p{
margin:0 !important;
padding:0 !important;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
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


# -------------------------------------------------
# TRANSPOSIÇÃO
# -------------------------------------------------
NOTAS=[
'C','C#','D','D#','E',
'F','F#','G','G#','A','A#','B'
]

def transpor_acorde(acorde,semitons):

    def sub(match):
        nota=match.group(1)
        resto=match.group(2)

        if nota in NOTAS:
            idx=(NOTAS.index(nota)+semitons)%12
            return NOTAS[idx]+resto

        return match.group(0)

    return re.sub(
        r'([A-G]#?)([^A-G\s]*)',
        sub,
        acorde
    )


def processar_texto(
texto,
semitons,
colunas
):

    if not texto:
        return ""

    linhas=texto.split("\n")
    linhas_t=[]

    for linha in linhas:

        nova=""
        pos=0

        for m in re.finditer(
            r'\S+',
            linha
        ):

            nova += (
                " "*(m.start()-pos)
                + transpor_acorde(
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

        esq=linhas_t[:meio]
        dir=linhas_t[meio:]

        largura=max(
            len(x)
            for x in esq
        ) if esq else 0

        final=[]

        for i in range(
            max(
                len(esq),
                len(dir)
            )
        ):

            a=esq[i] if i<len(esq) else ""
            b=dir[i] if i<len(dir) else ""

            final.append(
                a.ljust(largura+8)+b
            )

        return "\n".join(final)

    return "\n".join(linhas_t)



# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
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


def set_fonte(v):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]["fonte"]=v


def ajustar_tom(delta):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]["tom"]+=delta


def set_tom(v):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]["tom"]=v


def set_layout(v):
    if st.session_state.musica_focada is not None:
        st.session_state.book[
            st.session_state.musica_focada
        ]["cols"]=v



st.sidebar.write("Tamanho da Letra")
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


st.sidebar.write("Tom")
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


st.sidebar.write("Layout")
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



# -------------------------------------------------
# ADICIONAR
# -------------------------------------------------
if aba=="Adicionar Música":

    st.header("🔍 Capturar Cifra")

    url=st.text_input(
        "Link da cifra",
        key=f"url_{st.session_state.limpador}"
    )

    if st.button("Capturar"):

        try:
            res=requests.get(
                url,
                headers={
                    "User-Agent":"Mozilla/5.0"
                },
                timeout=10
            )

            soup=BeautifulSoup(
                res.text,
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

            cifra=soup.find("pre").get_text()

            st.session_state.temp_titulo=titulo
            st.session_state.temp_conteudo=cifra

            st.rerun()

        except:
            st.error(
                "Erro ao capturar cifra."
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

        st.success("Adicionado.")
        st.rerun()



# -------------------------------------------------
# VISUALIZAR
# -------------------------------------------------
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

                for linha in texto_proc.split("\n"):

                    if linha.strip()=="":
                        linha=" "

                    linha=linha.replace(
                        " ",
                        "&nbsp;"
                    )

                    bloco += f"""
<div class='cifra-renderizada'>
{linha}
</div>
"""

                st.markdown(
                    bloco,
                    unsafe_allow_html=True
                )

                st.markdown(
"</div></div>",
unsafe_allow_html=True
                )


                if st.button(
                    "🗑️ Excluir Música",
                    key=f"del_{i}"
                ):
                    st.session_state.book.pop(i)
                    st.session_state.musica_focada=None
                    st.rerun()



# -------------------------------------------------
# EXPORTAR
# -------------------------------------------------
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
                    m["titulo"],
                    ln=True
                )

                pdf.set_font(
                    "Courier",
                    size=m["fonte"]
                )

                txt=processar_texto(
                    m["conteudo"],
                    m["tom"],
                    m["cols"]
                )

                pdf.multi_cell(
                    0,
                    5,
                    txt
                )

            pdf_bytes=bytes(
                pdf.output(dest="S")
            )

            st.download_button(
                "📥 Baixar PDF",
                data=pdf_bytes,
                file_name="MeuRepertorio.pdf",
                mime="application/pdf"
            )
