from flask import Flask, render_template, request
import spacy
from spacy.matcher import PhraseMatcher
import re
from collections import defaultdict

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

FINANCIAL_TERMS = [
    "revenue", "net income", "gross profit", "operating income", "EBITDA",
    "earnings per share", "EPS", "assets", "liabilities", "debt",
    "cash flow", "free cash flow", "interest", "dividend", "expenses",
    "cost of goods sold", "COGS", "equity", "operating expenses",
    "shareholder", "balance sheet", "income statement", "tax", "R&D",
    "capital expenditure", "profit margin", "return on equity", "ROE",
    "current ratio", "total assets", "total liabilities", "depreciation"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

money_regex = re.compile(r"(₹|\$|€|Rs\.?)\s?[0-9,]+(?:\.\d+)?(?:\s?(crore|million|billion|lakhs)?)", re.IGNORECASE)

def extract_company_name(doc):
    for ent in doc.ents:
        if ent.label_ == "ORG":
            return ent.text
    return "Unknown Company"

def extract_money_expressions(text):
    return [(m.start(), m.end(), m.group()) for m in money_regex.finditer(text)]

def extract_financial_entities(text):
    doc = nlp(text)
    matches = matcher(doc)
    financial_data = defaultdict(list)
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

        if closest:
            financial_data[term].append(closest)

    return {
        "company_name": company_name,
        "financial_details": dict(financial_data)
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = request.form["financial_text"]
        result = extract_financial_entities(text)
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
