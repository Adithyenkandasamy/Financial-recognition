import pandas as pd
import re
import random

# Path to your dataset
DATASET_PATH = 'Financial Statements.csv'  # Change if needed
if DATASET_PATH.endswith('.csv'):
    df = pd.read_csv(DATASET_PATH, encoding='utf-8-sig')
elif DATASET_PATH.endswith('.xlsx'):
    df = pd.read_excel(DATASET_PATH, engine='openpyxl')
elif DATASET_PATH.endswith('.xls'):
    df = pd.read_excel(DATASET_PATH, engine='xlrd')
else:
    raise ValueError('Unsupported file format for dataset!')
df.columns = [col.strip() for col in df.columns]

# Use all columns as entity labels (except maybe 'Year' or similar, user can edit if needed)
ENTITY_LABELS = {col: col.upper().replace(' ', '_') for col in df.columns}

TEMPLATES = [
    # Dynamically generate templates for each row
]

# Generate a simple sentence per row using all columns
for idx, row in df.iterrows():
    parts = []
    for col in df.columns:
        if pd.notnull(row[col]):
            parts.append(f"{col}: {row[col]}")
    text = "; ".join(parts)
    entities = []
    start = 0
    for col in df.columns:
        value = str(row[col]) if pd.notnull(row[col]) else None
        if value and value in text:
            idx_start = text.index(value, start)
            idx_end = idx_start + len(value)
            entities.append((idx_start, idx_end, ENTITY_LABELS[col]))
            start = idx_end  # move start forward to avoid duplicate matches
    if entities:
        TEMPLATES.append((text, {"entities": entities}))

TRAIN_DATA = TEMPLATES
random.shuffle(TRAIN_DATA)

# Save as .py file for spaCy training
with open('spacy_train_data.py', 'w', encoding='utf-8') as f:
    f.write('TRAIN_DATA = ' + repr(TRAIN_DATA))

print(f"Generated {len(TRAIN_DATA)} training examples for spaCy NER.")
print(f"Entity labels: {list(ENTITY_LABELS.values())}")
