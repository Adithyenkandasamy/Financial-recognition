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

def extract_financial_entities(text):
    doc = nlp(text)
    results = []
    for ent in doc.ents:
        results.append({'text': ent.text, 'label': ent.label_})
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_labels = []
    entities = []
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
        entities = extract_financial_entities(extracted_text)
        labels = sorted(set(ent['label'] for ent in entities))
        raw_text = extracted_text
        # Handle label selection
        selected_labels = request.form.getlist('selected_labels')
        if not selected_labels:
            selected_labels = labels  # default: show all
        # Filter entities
        entities = [ent for ent in entities if ent['label'] in selected_labels]
        return render_template('result.html', entities=entities, labels=labels, selected_labels=selected_labels, raw_text=raw_text)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
