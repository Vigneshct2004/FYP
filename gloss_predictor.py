import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import re
import spacy
from nltk.corpus import stopwords
import nltk
from nltk.tokenize import sent_tokenize

# Download once
nltk.download('punkt')
nltk.download('stopwords')

# Load NLP tools
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words("english"))

MODEL_PATH = r"C:\Users\vignesh\Downloads\mt5_gloss_model\mt5_gloss_model"

print("Loading Gloss Transformer...")

device = torch.device("cpu")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

model.to(device)
model.eval()

print("✅ Gloss model loaded!")

############################################
# PREPROCESSING (PER SENTENCE)
############################################

def preprocess_text(text):

    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)

    words = text.split()
    text = " ".join(words)

    doc = nlp(text)
    lemmas = [token.lemma_ for token in doc]

    return " ".join(lemmas)


############################################
# ISL CLEANUP
############################################

def isl_cleanup(gloss_text):

    gloss_text = gloss_text.upper()

    remove_tokens = ["X-", "IX-", "CL-", "ROLE-", "DESC-"]

    for token in remove_tokens:
        gloss_text = gloss_text.replace(token, "")

    be_words = [" AM ", " IS ", " ARE ", " WAS ", " WERE ", " BE "]

    for w in be_words:
        gloss_text = gloss_text.replace(w, " ")

    gloss_text = " ".join(gloss_text.split())

    return gloss_text


############################################
# PARAGRAPH → GLOSS (CORRECTED)
############################################

def predict_gloss_paragraph(text, model, tokenizer, device):

    # 🔥 Step 1: Split BEFORE preprocessing
    sentences = sent_tokenize(text)

    all_gloss = []

    for sent in sentences:
        print("\n🔹 Original Sentence:", sent)
        # 🔥 Step 2: Preprocess EACH sentence
        clean_sent = preprocess_text(sent)
        print("\n🔹 Preprocessed Sentence:", clean_sent)
        input_text = "Translate English to Gloss: " + clean_sent

        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=96
        ).to(device)

        with torch.no_grad():

            # 🔥 Step 3: FIX truncation
            input_len = inputs["input_ids"].shape[1]

            outputs = model.generate(
                **inputs,
                max_length=input_len + 60,   # ✅ dynamic
                num_beams=4
            )

        gloss = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 🔥 Step 4: cleanup per sentence
        gloss = isl_cleanup(gloss)

        all_gloss.append(gloss)

    return " ".join(all_gloss)


############################################
# FINAL FUNCTION (USED BY UI)
############################################

def predict_gloss(text):

    # print("🔹 Original Text:", text)

    gloss = predict_gloss_paragraph(text, model, tokenizer, device)

    print("✅ FULL GLOSS:", gloss)

    return gloss.split()