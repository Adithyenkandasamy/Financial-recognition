import os
from flask import Flask, render_template, request
import pandas as pd
import pdfplumber
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'xls', 'xlsx', 'csv', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load your own dataset (e.g., Financial Statements.xls)
DATASET_PATH = '../Financial Statements.xls'  # Adjust if needed
if DATASET_PATH.endswith('.csv'):
    df = pd.read_csv(DATASET_PATH, encoding='utf-8-sig')
else:
    df = pd.read_excel(DATASET_PATH)
df.columns = [col.strip() for col in df.columns]

FINANCIAL_FIELDS = [
    'Company', 'Revenue', 'Net income', 'Ebitda', 'Eps', 'Assets', 'Liabilities',
    'Dividend', 'Profit', 'Cost', 'Cash flow', 'Expenses', 'Total assets',
    'Total liabilities', 'Loss'
]

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

def extract_from_dataset(text):
    # Try to find a company from the dataset in the text
    company_found = None
    for company in df['Company'].dropna().unique():
        if str(company).lower() in text.lower():
            company_found = company
            break
    result = {field: 'Not Found' for field in FINANCIAL_FIELDS}
    if company_found:
        row = df[df['Company'].str.lower() == company_found.lower()].iloc[0]
        for field in FINANCIAL_FIELDS:
            if field in row and pd.notnull(row[field]):
                result[field] = row[field]
        result['Company'] = company_found
    return result

@app.route('/', methods=['GET', 'POST'])
def index():
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
        result = extract_from_dataset(extracted_text)
        return render_template('result.html', result=result, raw_text=extracted_text)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
