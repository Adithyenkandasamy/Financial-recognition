import spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding
import random
import shutil
from spacy_train_data import TRAIN_DATA

# Set your model output directory
OUTPUT_DIR = "custom_financial_ner"

# Delete old model if exists
import os
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)

# Create blank English model
nlp = spacy.blank("en")

# Add NER pipeline if not present
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# Add all labels from training data
for _, annotations in TRAIN_DATA:
    for ent in annotations.get("entities"):
        ner.add_label(ent[2])

# Disable other pipes for training
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
with nlp.disable_pipes(*other_pipes):
    optimizer = nlp.begin_training()
    for itn in range(20):
        random.shuffle(TRAIN_DATA)
        losses = {}
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.5))
        for batch in batches:
            texts, annotations = zip(*batch)
            examples = [Example.from_dict(nlp.make_doc(text), ann) for text, ann in batch]
            nlp.update(examples, drop=0.2, losses=losses)
        print(f"Iteration {itn+1}, Losses: {losses}")

# Save the trained model
nlp.to_disk(OUTPUT_DIR)
print(f"Model saved to {OUTPUT_DIR}")
