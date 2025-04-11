import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import spacy
from spacy.matcher import PhraseMatcher
import re
from collections import defaultdict
import fitz  
import docx

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
FINANCIAL_TERMS = [
    "revenue", "net income", "EBITDA", "EPS", "assets", "liabilities",
    "dividend", "profit", "cost", "cash flow", "expenses", "total assets",
    "total liabilities", "loss"
]
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])
money_regex = re.compile(r"(₹|rs\.?|INR|\$|€)\s?[0-9,.]+(?:\s?(crore|million|billion|lakhs)?)", re.IGNORECASE)

# ----------------- UTILS -----------------

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

# ----------------- NLP -----------------

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
    money_matches = extract_money_expressions(text)

    for match_id, start, end in matches:
        term = doc[start:end].text.lower()
        token_start_char = doc[start].idx

        closest = None
        closest_distance = float("inf")
        for m_start, m_end, value in money_matches:
            distance = abs(m_start - token_start_char)
            if distance < closest_distance:
                closest = value
                closest_distance = distance

        if closest and term not in financial_data:
            financial_data[term] = closest

    # Add defaults for not found
    final_data = {}
    for term in FINANCIAL_TERMS:
        if term in financial_data:
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

# ----------------- ROUTES -----------------

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        if 'financial_text' in request.form and request.form['financial_text'].strip():
            text = request.form['financial_text']
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                text = extract_text_from_file(filepath)
            else:
                text = ""
        else:
            text = ""

        if text:
            result = extract_financial_entities(text)
    return render_template("index.html", result=result, terms=FINANCIAL_TERMS)

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True,host="0.0.0.0",port=5000)
