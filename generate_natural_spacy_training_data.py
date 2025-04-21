import pandas as pd
import random
import re

DATASET_PATH = 'Financial Statements.csv'  # Adjust if needed
if DATASET_PATH.endswith('.csv'):
    df = pd.read_csv(DATASET_PATH, encoding='utf-8-sig')
elif DATASET_PATH.endswith('.xlsx'):
    df = pd.read_excel(DATASET_PATH, engine='openpyxl')
elif DATASET_PATH.endswith('.xls'):
    df = pd.read_excel(DATASET_PATH, engine='xlrd')
else:
    raise ValueError('Unsupported file format for dataset!')
df.columns = [col.strip() for col in df.columns]

# Define natural templates for financial sentences
TEMPLATES = [
    "{Company} reported a revenue of {Revenue} crore for the year {Year}.",
    "The net income of {Company} in {Year} was {Net income} crore.",
    "{Company} had assets totaling {Assets} crore and liabilities of {Liabilities} crore.",
    "In {Year}, {Company} paid a dividend of {Dividend} per share.",
    "The EBITDA for {Company} stood at {Ebitda} crore.",
    "{Company}'s earnings per share (EPS) in {Year} was {Eps}.",
    "{Company} reported total expenses of {Expenses} crore in {Year}.",
    "{Company} had a cash flow of {Cash flow} crore and a loss of {Loss} crore.",
    "The ROE for {Company} in {Year} was {ROE} percent.",
]

# Map columns to entity labels
ENTITY_LABELS = {col: col.upper().replace(' ', '_') for col in df.columns}

TRAIN_DATA = []

for idx, row in df.iterrows():
    # For each row, randomly select up to 3 templates to generate diverse examples
    templates = random.sample(TEMPLATES, k=min(3, len(TEMPLATES)))
    for template in templates:
        # Check if all required fields are present in this row
        needed_fields = re.findall(r"{(.*?)}", template)
        skip = False
        for field in needed_fields:
            if field not in row or pd.isnull(row[field]):
                skip = True
                break
        if skip:
            continue
        # Fill template
        text = template.format(**row)
        entities = []
        for field in needed_fields:
            value = str(row[field])
            # Find all occurrences for robustness
            for match in re.finditer(re.escape(value), text):
                entities.append((match.start(), match.end(), ENTITY_LABELS[field]))
        if entities:
            TRAIN_DATA.append((text, {"entities": entities}))

random.shuffle(TRAIN_DATA)

with open('spacy_train_data.py', 'w', encoding='utf-8') as f:
    f.write('TRAIN_DATA = ' + repr(TRAIN_DATA))

print(f"Generated {len(TRAIN_DATA)} natural training examples for spaCy NER.")
print(f"Entity labels: {list(ENTITY_LABELS.values())}")
