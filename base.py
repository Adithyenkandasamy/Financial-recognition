import os
import re
import spacy
from spacy.matcher import PhraseMatcher
from collections import defaultdict
import pandas as pd

# Load spaCy model and increase max length limit
nlp = spacy.load("en_core_web_sm")
nlp.max_length = 600000000  # Adjust this based on your largest file size

# Financial terms and matcher
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
FINANCIAL_TERMS = [
    "revenue", "net income", "EBITDA", "EPS", "assets", "liabilities",
    "dividend", "profit", "cost", "cash flow", "expenses", "total assets",
    "total liabilities"
]
matcher.add("FIN_TERMS", [nlp.make_doc(term) for term in FINANCIAL_TERMS])

# Money pattern (₹, $, €, Rs., crore, etc.)
money_regex = re.compile(
    r"(₹|\$|€|Rs\.?)\s?[0-9,]+(?:\.\d+)?(?:\s?(crore|million|billion|lakhs)?)",
    re.IGNORECASE
)

def extract_money_expressions(text):
    return [(m.start(), m.end(), m.group()) for m in money_regex.finditer(text)]

def extract_company_name(doc):
    for ent in doc.ents:
        if ent.label_ == "ORG":
            return ent.text
    return "Unknown Company"

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

def analyze_folder(folder_path):
    results = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                if len(text) > nlp.max_length:
                    print(f"⚠️ Skipping '{filename}' due to excessive length ({len(text)} characters).")
                    continue
                data = extract_financial_entities(text)
                result_row = {"filename": filename, "company_name": data["company_name"]}
                for term in FINANCIAL_TERMS:
                    result_row[term] = ", ".join(data["financial_details"].get(term.lower(), []))
                results.append(result_row)
    return results

def main():
    folder = "2025q1"
    output_file = "financial_extracted_results.csv"
    result_data = analyze_folder(folder)
    df = pd.DataFrame(result_data)
    df.to_csv(output_file, index=False)
    print(f"✅ Extraction completed. Results saved to '{output_file}'")

if __name__ == "__main__":
    main()
