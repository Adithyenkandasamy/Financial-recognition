import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import spacy
from spacy.matcher import PhraseMatcher
import fitz  # PyMuPDF
import docx
import re
import pandas as pd
from collections import defaultdict
from forex_python.converter import CurrencyCodes

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xls', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load spaCy model
nlp = spacy.load("/home/jinwoo/Desktop/Financial-recognition/output/model-best")
if "sentencizer" not in nlp.pipe_names:
    nlp.add_pipe("sentencizer")

# Load default spaCy model for fallback
try:
    nlp_default = spacy.load("en_core_web_sm")
except Exception:
    nlp_default = None

# Financial terms
FINANCIAL_TERMS = sorted([
    "total assets", "total liabilities", "net income", "cash flow", "EBITDA", "EPS",
    "revenue", "assets", "liabilities", "dividend", "profit", "cost", "expenses", "loss"
], key=len, reverse=True)

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

# Money regex
money_regex = re.compile(
    r"([₹$€£¥₣₹]|(?:INR|USD|EUR|GBP|CAD|AUD|JPY|CNY|CHF|RUB|ZAR|SAR))\s?[\d,.]+(?:\s?(crore|million|billion|lakhs))?(?:\s?(per share))?\.?",
    re.IGNORECASE
)

# --- File handlers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext == "docx":
        return extract_text_from_docx(filepath)
    elif ext == "txt":
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext in {"xls", "xlsx"}:
        return extract_text_from_excel(filepath)
    return ""

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_excel(excel_path):
    try:
        dfs = pd.read_excel(excel_path, sheet_name=None)
        text = ""
        for name, df in dfs.items():
            text += f"\n\nSheet: {name}\n"
            text += df.to_string(index=False)
        return text
    except Exception as e:
        return f"Error reading Excel file: {e}"

# --- NLP Logic ---
def extract_company_name(doc):
    for ent in doc.ents:
        if ent.label_ == "COMPANY":
            return ent.text
    # Fallback to default model
    if nlp_default:
        doc_default = nlp_default(doc.text)
        for ent in doc_default.ents:
            if ent.label_ == "ORG":
                return ent.text
    return "Unknown Company"

def extract_financial_entities(text):
    doc = nlp(text[:1000000])
    matches = matcher(doc)
    financial_data = defaultdict(str)
    company_name = extract_company_name(doc)

    # Extract FIN_TERM and MONEY entities from NER
    ner_terms = {}
    ner_money = {}
    for ent in doc.ents:
        if ent.label_ == "FIN_TERM":
            ner_terms[ent.text.lower()] = ent.start_char
        elif ent.label_ == "MONEY":
            ner_money[ent.start_char] = ent.text

    # Attempt to pair FIN_TERM and MONEY entities by proximity
    for term, t_pos in ner_terms.items():
        closest_money = None
        min_dist = float('inf')
        for m_pos, m_text in ner_money.items():
            if m_pos > t_pos and m_pos - t_pos < min_dist:
                closest_money = m_text
                min_dist = m_pos - t_pos
        if closest_money:
            financial_data[term] = closest_money

    # Existing logic: Group monetary values by sentence
    money_by_sent = {}
    for sent in doc.sents:
        money_matches = list(money_regex.finditer(sent.text))
        if money_matches:
            money_by_sent[sent.start] = [(m.group(), m.start() + sent.start_char) for m in money_matches]

    for match_id, start, end in matches:
        term = doc[start:end].text.lower()
        sent = doc[start].sent
        sent_start = sent.start
        money_matches = money_by_sent.get(sent_start, [])
        if money_matches and not financial_data[term]:
            financial_data[term] = money_matches[0][0]

    # Fallback regex patterns
    fallback_mapping = {
        "EBITDA": r"EBITDA.*?(₹|rs\.?|INR|\$|€)\s?[\d,.]+",
        "EPS": r"EPS.*?\d+(\.\d+)?",
        "profit": r"(profit|profitability).*?(₹|rs\.?|INR|\$|€)?\s?[\d,.]+",
        "expenses": r"expenses.*?(₹|rs\.?|INR|\$|€)\s?[\d,.]+",
        "cost": r"cost.*?(₹|rs\.?|INR|\$|€)\s?[\d,.]+",
        "loss": r"loss.*?(₹|rs\.?|INR|\$|€)\s?[\d,.]+"
    }

    for term, pattern in fallback_mapping.items():
        if financial_data[term] == "":
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = money_regex.search(match.group())
                if value:
                    financial_data[term] = value.group()

    # Fallback: Use default NER for money if still not found
    if nlp_default:
        doc_default = nlp_default(text)
        for ent in doc_default.ents:
            if ent.label_ == "MONEY":
                for term in FINANCIAL_TERMS:
                    if financial_data[term] == "":
                        financial_data[term] = ent.text

    final_data = {}
    for term in FINANCIAL_TERMS:
        if term in financial_data and financial_data[term]:
            final_data[term] = financial_data[term]
        else:
            final_data[term] = "❌ Not Found"

    return {
        "company_name": company_name,
        "financial_details": final_data
    }

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = ""
        if 'financial_text' in request.form and request.form['financial_text'].strip():
            text = request.form['financial_text']
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                text = extract_text_from_file(filepath)

        if text.strip():
            result = extract_financial_entities(text)

    return render_template("index.html", result=result, terms=FINANCIAL_TERMS)

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
