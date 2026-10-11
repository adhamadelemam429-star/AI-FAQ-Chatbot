import json
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "domain_data"
FAQ_PATH = BASE_DIR / "faqs.json"
INDEX_PATH = BASE_DIR / "faiss_index"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DATA_PATH.mkdir(exist_ok=True)

print("جاري تحميل ملفات PDF وTXT...")
pdf_loader = DirectoryLoader(str(DATA_PATH), glob="*.pdf", loader_cls=PyPDFLoader)
txt_loader = DirectoryLoader(
    str(DATA_PATH),
    glob="*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)

documents = pdf_loader.load() + txt_loader.load()

if FAQ_PATH.exists():
    with FAQ_PATH.open(encoding="utf-8") as faq_file:
        faqs = json.load(faq_file)

    if not isinstance(faqs, list):
        raise ValueError("يجب أن يحتوي faqs.json على قائمة من الأسئلة والأجوبة.")

    for index, faq in enumerate(faqs, start=1):
        if not isinstance(faq, dict) or not faq.get("question") or not faq.get("answer"):
            raise ValueError(f"السؤال رقم {index} في faqs.json ينقصه question أو answer.")
        documents.append(
            Document(
                page_content=f"السؤال: {faq['question']}\nالإجابة: {faq['answer']}",
                metadata={"source": FAQ_PATH.name, "question": faq["question"]},
            )
        )

if not documents:
    raise SystemExit("لا توجد بيانات للفهرسة. أضف أسئلة إلى faqs.json أو ملفات PDF/TXT إلى domain_data.")

print(f"جاري تجهيز {len(documents)} مستند/سؤال...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = FAISS.from_documents(docs, embeddings)
vector_store.save_local(str(INDEX_PATH))

print("✅ تم بناء قاعدة المعرفة الخاصة بتخصصك بنجاح!")