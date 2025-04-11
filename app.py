import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
import fitz  # PyMuPDF
import docx
import re
from collections import defaultdict

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Create PhraseMatcher for financial terms
FINANCIAL_TERMS = sorted([
    "total assets", "total liabilities", "net income", "cash flow", "EBITDA", "EPS",
    "revenue", "assets", "liabilities", "dividend", "profit", "cost", "expenses", "loss"
], key=len, reverse=True)

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

# Regex to match monetary values (supports trailing periods or per share info)
money_regex = re.compile(r"(₹|rs\.?|INR|\$|€)\s?[\d,.]+(?:\s?(crore|million|billion|lakhs))?(?:\s?(per share))?\.?", re.IGNORECASE)

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

# --- NLP Logic ---
def extract_company_name(doc):
    for ent in doc.ents:
        if ent.label_ == "ORG":
            return ent.text
    return "Unknown Company"

def extract_money_expressions(text):
    return [(m.start(), m.end(), m.group()) for m in money_regex.finditer(text)]

def extract_financial_entities(text):
    doc = nlp(text[:1000000])
    matches = matcher(doc)
    financial_data = defaultdict(str)
    company_name = extract_company_name(doc)

    # Group money mentions per sentence
    money_by_sent = {}
    for sent in doc.sents:
        sent_text = sent.text
        money_found = money_regex.findall(sent_text)
        money_matches = money_regex.finditer(sent_text)
        if money_found:
            money_by_sent[sent.start] = [(m.group(), m.start() + sent.start_char) for m in money_matches]

    for match_id, start, end in matches:
        term = doc[start:end].text.lower()
        sent = doc[start].sent
        sent_start = sent.start

        money_matches = money_by_sent.get(sent_start, [])
        if money_matches:
            financial_data[term] = money_matches[0][0]

    # Heuristic for fallback matching
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

    # Fill defaults
    final_data = {}
    for term in FINANCIAL_TERMS:
        if term in financial_data and financial_data[term]:
            final_data[term] = financial_data[term]
        else:
            if re.search(rf"{term}.*(not found|not available|not disclosed)", text, re.IGNORECASE):
                final_data[term] = "❌ Not Available"
            else:
                final_data[term] = "❌ Not Found"

    return {
        "company_name": company_name,
        "financial_details": final_data
    }

# --- Flask routes ---
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
    app.run(debug=True, host="0.0.0.0", port=5000)
