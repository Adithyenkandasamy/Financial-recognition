import pandas as pd
import spacy
from spacy.tokens import DocBin

# Load the CSV file
df = pd.read_csv("/home/jinwoo/Desktop/Financial-recognition/Financial Statements.csv")

# Drop rows with missing essential data
df = df.dropna(subset=["Company ", "Year"])

# Create a blank spaCy model
nlp = spacy.blank("en")
doc_bin = DocBin()

# Mapping from ticker to full company name
TICKER_TO_NAME = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOG": "Alphabet Inc.",
    "PYPL": "PayPal Holdings, Inc.",
    "AIG": "American International Group",
    "PCG": "PG&E Corporation",
    "SHLDQ": "Sears Holdings Corporation",
    "MCD": "McDonald's Corporation",
    "BCS": "Barclays PLC",
    "NVDA": "NVIDIA Corporation",
    "INTC": "Intel Corporation",
    "AMZN": "Amazon.com, Inc.",
    # Add more mappings as needed
}

# Define financial columns you're interested in
financial_columns = [
    "Revenue", "Net Income", "EBITDA", "Gross Profit", "Earning Per Share",
    "Cash Flow from Operating", "Cash Flow from Investing", "Cash Flow from Financial Activities",
    "Free Cash Flow per Share", "Share Holder Equity"
]

DIVERSE_TEMPLATES = [
    "{company} reported a {term} of {value} in {year}.",
    "In {year}, {company} had a {term} of {value}.",
    "The {term} for {company} in {year} was {value}.",
    "{value} was reported as {term} by {company} in {year}.",
    "{company}'s {term} for {year}: {value}.",
    "{company} achieved a {term} of {value} in the year {year}.",
    "During {year}, {company} posted a {term} of {value}."
]

for idx, row in df.iterrows():
    year = str(row["Year"]).strip()
    ticker = str(row["Company "]).strip()
    company = TICKER_TO_NAME.get(ticker, ticker)  # Default to ticker if not mapped

    for col in financial_columns:
        value = row.get(col)
        if pd.isna(value):
            continue
        term = col.lower()
        value_str = str(value).strip()

        for template in DIVERSE_TEMPLATES:
            sentence = template.format(company=company, term=term, value=value_str, year=year)
            doc = nlp.make_doc(sentence)
            ents = []

            # Tag company
            c_start = sentence.find(company)
            c_end = c_start + len(company)
            ents.append(doc.char_span(c_start, c_end, label="COMPANY"))

            # Tag financial term
            t_start = sentence.find(term)
            t_end = t_start + len(term)
            ents.append(doc.char_span(t_start, t_end, label="FIN_TERM"))

            # Tag value
            v_start = sentence.find(value_str)
            v_end = v_start + len(value_str)
            ents.append(doc.char_span(v_start, v_end, label="MONEY"))

            ents = [e for e in ents if e is not None]

            if len(ents) == 3:
                doc.ents = ents
                doc_bin.add(doc)

# Save the training data
output_path = "/home/jinwoo/Desktop/Financial-recognition/train.spacy"
doc_bin.to_disk(output_path)

print(f" Training data saved to {output_path}")
