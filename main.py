from sentence_transformers import SentenceTransformer, util
import pandas as pd
import torch
import os

# Load the pre-trained model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Load your dataset
df = pd.read_csv('/home/jinwoo/Desktop/Financial-recognition/extracted_financial_entities.csv')

# Combine all relevant columns into a single string per row
df['combined'] = df.fillna('').apply(lambda row: ' '.join([str(val) for val in row.values]), axis=1)

# Encode the dataset rows
corpus_embeddings = model.encode(df['combined'].tolist(), convert_to_tensor=True)

# 🔍 Your input financial text (can replace with any extracted financial string)
input_text = """
The company reported ₹5,200 crore in revenue and ₹600 crore net income. 
Assets totaled ₹12,300 crore while liabilities stood at ₹3,500 crore.
"""

# Encode the input
query_embedding = model.encode(input_text, convert_to_tensor=True)

# Compute cosine similarity
cos_scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)[0]

# Get the most similar entry
top_result = torch.topk(cos_scores, k=1)

# Show best match
index = int(top_result[1][0])
print("\n✅ Closest Match from CSV Dataset:")
print(df.iloc[index][['company_name', 'revenue', 'net income', 'assets', 'liabilities']])
