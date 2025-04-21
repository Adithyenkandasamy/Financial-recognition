import pandas as pd
import re
import random

# Path to your dataset
DATASET_PATH = 'Financial Statements.xls'  # Change if needed
if DATASET_PATH.endswith('.csv'):
    df = pd.read_csv(DATASET_PATH, encoding='utf-8-sig')
else:
    df = pd.read_excel(DATASET_PATH)
df.columns = [col.strip() for col in df.columns]

# Map dataset columns to entity labels
ENTITY_LABELS = {
    'Company': 'COMPANY',
    'Revenue': 'REVENUE',
    'Net income': 'NET_INCOME',
    'Ebitda': 'EBITDA',
    'Eps': 'EPS',
    'Assets': 'ASSETS',
    'Liabilities': 'LIABILITIES',
    'Dividend': 'DIVIDEND',
    'Profit': 'PROFIT',
    'Cost': 'COST',
    'Cash flow': 'CASH_FLOW',
    'Expenses': 'EXPENSES',
    'Total assets': 'TOTAL_ASSETS',
    'Total liabilities': 'TOTAL_LIABILITIES',
    'Loss': 'LOSS',
}

TEMPLATES = [
    "{Company} reported a revenue of {Revenue} and a net income of {Net income}.",
    "{Company} has assets worth {Assets} and liabilities of {Liabilities}.",
    "The profit of {Company} was {Profit} with expenses of {Expenses}.",
    "{Company} declared a dividend of {Dividend} per share.",
    "{Company} reported total assets of {Total assets} and total liabilities of {Total liabilities} in the last fiscal year.",
    "{Company} had an EBITDA of {Ebitda} and EPS of {Eps}.",
    "{Company} had a cash flow of {Cash flow} and a loss of {Loss}.",
]

TRAIN_DATA = []

for idx, row in df.iterrows():
    for template in TEMPLATES:
        # Only generate if all required fields in template are present
        skip = False
        for field in re.findall(r"{(.*?)}", template):
            if field not in row or pd.isnull(row[field]):
                skip = True
                break
        if skip:
            continue
        text = template.format(**row)
        entities = []
        for field, label in ENTITY_LABELS.items():
            value = str(row[field]) if field in row and pd.notnull(row[field]) else None
            if value and value in text:
                start = text.index(value)
                end = start + len(value)
                entities.append((start, end, label))
        if entities:
            TRAIN_DATA.append((text, {"entities": entities}))

# Shuffle for training randomness
random.shuffle(TRAIN_DATA)

# Save as .py file for spaCy training
with open('spacy_train_data.py', 'w', encoding='utf-8') as f:
    f.write('TRAIN_DATA = ' + repr(TRAIN_DATA))

print(f"Generated {len(TRAIN_DATA)} training examples for spaCy NER.")
