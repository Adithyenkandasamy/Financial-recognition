# financial_extractor.py
import re
import spacy
import pandas as pd
from pathlib import Path
from collections import defaultdict
from spacy.matcher import PhraseMatcher

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Define financial terms for taxonomy tagging
FINANCIAL_TERMS = [
    "revenue", "net income", "EBITDA", "EPS", "assets", "liabilities",
    "dividend", "profit", "cost", "cash flow", "expenses", "total assets",
    "total liabilities"
]

# Phrase matcher for financial terms
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

# Regex to capture monetary expressions with currency symbols and units
money_regex = re.compile(
    r"(\u20B9|\$|\u20AC|Rs\.?|\u00A5|\u20A9|\u20A6)\s?[0-9,]+(?:\.\d+)?(?:\s?(crore|million|billion|lakhs)?)",
    re.IGNORECASE
)

# Extract money expressions

def extract_money_expressions(text):
    return [(m.start(), m.end(), m.group()) for m in money_regex.finditer(text)]

# Extract company name

def extract_company_name(doc):
    for ent in doc.ents:
        if ent.label_ == "ORG":
            return ent.text
    return "Unknown Company"

# Main function to extract financial entities

def extract_financial_entities(text):
    doc = nlp(text[:1000000])  # Limit for performance
    matches = matcher(doc)
    financial_data = defaultdict(list)
    company_name = extract_company_name(doc)
    money_matches = extract_money_expressions(text)

    for _, start, end in matches:
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

# Batch process all TXT files and export CSV

def main():
    input_dir = Path("/home/jinwoo/Desktop/Financial-recognition/sec_reports")
    output_csv = "/home/jinwoo/Desktop/Financial-recognition/extracted_financial_entities.csv"
    results = []

    for txt_file in input_dir.glob("*.txt"):
        try:
            with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                data = extract_financial_entities(text)
                result_row = {
                    "filename": txt_file.name,
                    "company_name": data["company_name"]
                }
                for term in FINANCIAL_TERMS:
                    result_row[term] = ", ".join(data["financial_details"].get(term.lower(), []))
                results.append(result_row)
                print(f"\u2705 Processed: {txt_file.name}")
        except Exception as e:
            print(f"\u26A0\ufe0f Error processing {txt_file.name}: {e}")

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"\n\u2705 All done! Extracted financial data saved to: {output_csv}")

if __name__ == "__main__":
    main()
