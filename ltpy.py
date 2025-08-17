##
# 
#pip install gtts
#pip install  pandas 
#pip install  PyPDF2 
#pip install  google-generativeai
#pip install   dotenv 
##
##

import os
import datetime
import streamlit as st
from gtts import gTTS
import pandas as pd
from PyPDF2  import PdfReader
import google.generativeai as genai
from  dotenv import load_dotenv 
from google.generativeai import configure
from typing import Optional
import io

if "translated" not in st.session_state:
    st.session_state.translated = ""
lang_options_pair = {"Hindi" : "hi",
                "English":"en",
                "Spanish": "es"
               }
lang_options = list(lang_options_pair.keys())

def Read_files(fileupload) -> str:
    print("Read_files")
    if fileupload is None: return ""

    filenamelower = fileupload.name.lower()
    filetype = fileupload.type
    if filenamelower.endswith("docx"):
        fileupload.seek(0)
        doc = Document(fileupload)
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" ".join(cell.text for cell in row.cells))
        return "\n".join(t for t in parts if t.strip() )
    if filenamelower.endswith("pdf"):
        readpdf = PdfReader(fileupload)  
        pages = []
        for p in readpdf.pages:
            pages.append(p.extract_text() or "")
        return "\n".join(pages)



def Translate_files_Text(text_conv : str ,lang_options: str ) ->str:
    print("Translates the files/textusing LLM")
    load_dotenv()
    genaikey = os.getenv("GOOGLE_API_KEY", "").strip()
    genai.configure(api_key = genaikey)
    _genai_client_inited = True
    model =genai.GenerativeModel("gemini-1.5-flash")

    genaiPrompt = f"You are a language traslation engine , Translate the providedtext {text_conv} in targetlanguage {lang_options} do not return any thing apart from translated text " 

    response = model.generate_content([{"role": "user", "parts": genaiPrompt}])
    translated = getattr(response, "text", None)
    if not translated and getattr(response, "candidates", None):
            parts = response.candidates[0].content.parts
            translated = "".join(getattr(p, "text", "") for p in parts)
    return (translated or "").strip()


def Convert_to_speech(text_conv: str , lang_code: str) -> Optional[bytes]:
        print("Translates the files/textusing LLM")
        tts = gTTS(text=text_conv, lang=lang_code)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()



with st.sidebar:
    st.header("Language translation")
    st.info("The tool is created to translate language ")
    st.info("Start with Entering Text or uploading files")
    st.info("Select language to conver to, from options")
    st.info(" \n Then hit Convert text")

    st.subheader("1.) Upload a file or enter text")
    col1,col2  = st.columns(2)
    selected_lang = st.selectbox("Select a language",lang_options,0)
    clicktranslate = st.button("Convert text")

with col1:
    textupload = st.text_area("text here",height =100) 

with col2:
    fileupload = st.file_uploader("Select a file for conversion , PDF or Docx",type=["pdf","docx"])
    filetext = Read_files(fileupload) if fileupload is not None else ""
    text_conv = filetext if filetext.strip() else textupload



if clicktranslate:
    translated = Translate_files_Text(text_conv, selected_lang)
    st.session_state.translated = translated or ""
    if st.session_state.translated:
        st.success("Translated.")
        st.text_area("Translated text", st.session_state.translated, height=200)
    else:
        st.warning("No translated text returned.")
    

st.info("Convert to speech")
tts_lang_code = lang_options_pair.get(selected_lang,"en")
if st.session_state.translated: 
    audio_bytes = Convert_to_speech( st.session_state.translated, tts_lang_code)
    if audio_bytes:
            #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"translation_{tts_lang_code}_{timestamp}.mp3"
            st.success("Download Audio.")
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                label="Download MP3",
                data=audio_bytes,
                file_name=filename,
                mime="audio/mpeg",
                use_container_width=True,
            )
            