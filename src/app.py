import os
from flask import Flask, render_template, request
import spacy
import pdfplumber
import pandas as pd
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'xls', 'xlsx', 'csv', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the latest trained spaCy model
nlp = spacy.load('../custom_financial_ner')
if 'sentencizer' not in nlp.pipe_names:
    nlp.add_pipe('sentencizer')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ''
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text

def extract_text_from_xls(filepath):
    df_file = pd.read_excel(filepath)
    return df_file.to_csv(index=False)

def extract_text_from_csv(filepath):
    df_file = pd.read_csv(filepath)
    return df_file.to_csv(index=False)

def extract_financial_entities_grouped(text):
    doc = nlp(text)
    # Group entities by sentence, and within each sentence by company
    results = []
    for sent in doc.sents:
        sent_ents = [ent for ent in sent.ents]
        companies = [ent for ent in sent_ents if ent.label_ == 'COMPANY']
        # If no company, treat as 'Unknown'
        if not companies:
            group = {'COMPANY': 'Unknown'}
            for ent in sent_ents:
                group[ent.label_] = ent.text.strip()
            results.append(group)
        else:
            for company in companies:
                group = {'COMPANY': company.text.strip()}
                for ent in sent_ents:
                    if ent is company:
                        continue
                    if ent.label_ != 'COMPANY':
                        group[ent.label_] = ent.text.strip()
                results.append(group)
    # Remove duplicates
    unique_results = []
    seen = set()
    for group in results:
        key = tuple(sorted(group.items()))
        if key not in seen:
            unique_results.append(group)
            seen.add(key)
    return unique_results

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_labels = []
    groups = []
    raw_text = ''
    labels = []
    if request.method == 'POST':
        input_text = request.form.get('input_text', '').strip()
        file = request.files.get('file')
        extracted_text = ''
        filename = None
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            ext = filename.rsplit('.', 1)[1].lower()
            if ext == 'pdf':
                extracted_text = extract_text_from_pdf(filepath)
            elif ext in ['xls', 'xlsx']:
                extracted_text = extract_text_from_xls(filepath)
            elif ext == 'csv':
                extracted_text = extract_text_from_csv(filepath)
            elif ext == 'txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
        elif input_text:
            extracted_text = input_text
        else:
            return render_template('index.html', error='Please upload a file or paste text.')
        groups = extract_financial_entities_grouped(extracted_text)
        # Collect all labels for checkboxes
        all_labels = set()
        for group in groups:
            all_labels.update(group.keys())
        labels = sorted(all_labels)
        raw_text = extracted_text
        # Handle label selection
        selected_labels = request.form.getlist('selected_labels')
        if not selected_labels:
            selected_labels = labels  # default: show all
        # Filter group fields
        filtered_groups = []
        for group in groups:
            filtered = {k: v for k, v in group.items() if k in selected_labels}
            filtered_groups.append(filtered)
        return render_template('result.html', groups=filtered_groups, labels=labels, selected_labels=selected_labels, raw_text=raw_text)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
