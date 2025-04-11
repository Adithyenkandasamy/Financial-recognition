import pandas as pd
import webbrowser
import requests

# Load Excel file
file_path = '/home/jinwoo/Desktop/Financial-recognition/cik_list.xlsx'
df = pd.read_excel(file_path)

# Base SEC URL
base_url = 'https://www.sec.gov/Archives/'

# Add a new column with full URLs
df['SEC_FULL_URL'] = base_url + df['SECFNAME']

# Optional: Check which URLs are working
def check_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# You can uncomment this line to filter only valid links
# df['is_valid'] = df['SEC_FULL_URL'].apply(check_url)
# df_valid = df[df['is_valid']]

# Optional: Open first 5 links in browser
for url in df['SEC_FULL_URL'].head(5):  # You can increase or change this range
    print(f"Opening: {url}")
    webbrowser.open(url)

# Save updated DataFrame with full URLs
df.to_excel('/home/jinwoo/Desktop/Financial-recognition/cik_list_with_links.xlsx', index=False)
print("✅ Done! Updated file with links saved.")
