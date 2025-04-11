import re
import spacy
from spacy.matcher import PhraseMatcher
from collections import defaultdict

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Define financial terms to match
FINANCIAL_TERMS = [
    "revenue", "net income", "gross profit", "operating income", "EBITDA",
    "earnings per share", "EPS", "assets", "liabilities", "debt",
    "cash flow", "free cash flow", "interest", "dividend", "expenses",
    "cost of goods sold", "COGS", "equity", "operating expenses",
    "shareholder", "balance sheet", "income statement", "tax", "R&D",
    "capital expenditure", "profit margin", "return on equity", "ROE",
    "current ratio", "total assets", "total liabilities", "depreciation"
]

# Regex pattern for ₹, $, € + number + optional "crore"/"million"/"billion"
money_regex = re.compile(r"(₹|\$|€|Rs\.?)\s?[0-9,]+(?:\.\d+)?(?:\s?(crore|million|billion|lakhs)?)", re.IGNORECASE)

# spaCy PhraseMatcher setup
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

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

        # Find closest money match by character index
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

# 🧪 Sample usage
if __name__ == "__main__":
    text = """
    ABC Tech Solutions Ltd. reported $9,845 crore in revenue for FY 2023, with a net income of $1,941 crore.
    The EBITDA stood at $3,396 crore, while the EPS reached $48.53. Total assets were $19,820 crore,
    and total liabilities amounted to $11,235 crore. The company also announced a dividend of $20.75 per share.
    """

    result = extract_financial_entities(text)

    print("\n🏢 Company Name:", result["company_name"])
    print("📊 Financial Highlights:")
    for key, values in result["financial_details"].items():
        print(f" - {key.title()}: {', '.join(values)}")
