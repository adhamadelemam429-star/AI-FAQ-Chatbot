import difflib
import json
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or os.getenv("API_KEY") or "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAQ_PATH = BASE_DIR / "faqs.json"

try:
    with FAQ_PATH.open(encoding="utf-8") as faq_file:
        FAQS = json.load(faq_file)
except (OSError, json.JSONDecodeError):
    FAQS = []


def normalize_arabic(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def find_faq_answer(query):
    normalized_query = normalize_arabic(query)
    best_match = None
    best_score = 0.0

    for faq in FAQS:
        question = faq.get("question", "")
        normalized_question = normalize_arabic(question)
        score = difflib.SequenceMatcher(None, normalized_query, normalized_question).ratio()
        if score > best_score:
            best_match = faq
            best_score = score

    if best_match and best_score >= 0.76:
        return best_match.get("answer")
    return None

st.set_page_config(page_title="المساعد الذكي الشامل", page_icon="🤖")
st.title("🤖 المساعد الذكي الشامل")


@st.cache_resource
def load_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.load_local(
        str(BASE_DIR / "faiss_index"),
        embeddings,
        allow_dangerous_deserialization=True,
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

if not GROQ_API_KEY:
    st.info("المفتاح غير مضبوط حاليًا؛ يمكنك استخدام الأسئلة الشائعة المحلية، وأضف مفتاح Groq صالحًا للأسئلة العامة.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("اسألني عن أي شيء..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير..."):
            faq_answer = find_faq_answer(user_query)
            if faq_answer:
                answer = faq_answer
            elif not GROQ_API_KEY:
                answer = "السؤال غير موجود ضمن الأسئلة الشائعة المحلية. أضف مفتاح Groq صالحًا إلى ملف .env لتفعيل الإجابة عن الأسئلة العامة."
            else:
                context_text = ""
                try:
                    vector_store = load_vector_store()
                    retrieved_docs = vector_store.similarity_search(user_query, k=3)
                    context_text = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)
                except Exception:
                    pass

                if context_text.strip():
                    sys_msg = "أنت مساعد ذكي ومفيد. أجب على سؤال المستخدم مستعيناً بالمعلومات المتاحة بشكل رئيسي، وأكمل من معرفتك العامة إن لزم."
                    user_msg = f"المعلومات المتاحة:\n{context_text}\n\nالسؤال: {user_query}"
                else:
                    sys_msg = "أنت مساعد ذكي ومفيد جداً. أجب على سؤال المستخدم بأسلوب شامل وطبيعي بناءً على معرفتك العامة."
                    user_msg = user_query

                messages = [SystemMessage(content=sys_msg), HumanMessage(content=user_msg)]
                try:
                    llm = ChatGroq(
                        model=GROQ_MODEL,
                        groq_api_key=GROQ_API_KEY,
                        temperature=0.7,
                    )
                    response = llm.invoke(messages)
                    answer = response.content
                except Exception as error:
                    if "401" in str(error) or "Invalid API Key" in str(error):
                        answer = "مفتاح Groq غير صالح أو منتهي. حدّث GROQ_API_KEY في ملف .env بمفتاح جديد؛ الأسئلة الشائعة المحلية ما زالت تعمل."
                    else:
                        answer = f"تعذر الاتصال بـ Groq. تحقق من اتصال الإنترنت وإعدادات الخدمة. التفاصيل: {error}"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})