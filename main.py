import sys
from src.train import train_topic_extractor
from src.extract import extract_topics_from_text

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <csv_file> <text_to_extract>")
        sys.exit(1)
    csv_file = sys.argv[1]
    input_text = sys.argv[2]
    # Train the topic extractor model
    train_topic_extractor(csv_file)
    # Extract topics and values from the input text
    result = extract_topics_from_text(input_text, csv_path=csv_file)
    print("Extracted information from text:")
    for k, v in result.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
