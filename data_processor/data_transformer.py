import spacy
import re
from nltk.tokenize import word_tokenize, sent_tokenize

# function for converting a text into the relationships
def get_low_level_concepts(text):
    return_value = []
    
    for char in text:
        # exclude spaces and special characters
        if char.isalnum():
            return_value.append(char)

    return return_value

def get_medium_level_concepts(text, stopwords):
    return_value = []
    
    # Example: Split text into words and filter out short words
    for word in text.split():
        # possible conditions to filter out words like stopwords...
        
        # possible post-processing to remove punctuation
        word = word.strip(".,;:!?()[]{}\"'")  # Remove common punctuation

        if word.lower() not in stopwords:
            return_value.append(word)

    return return_value

def get_german_stopwords():
    with open("german_stopwords_full.txt", "r", encoding="utf-8") as file:
        stopwords = file.read().splitlines()

    for i in range(len(stopwords)):
        stopwords[i] = stopwords[i].strip()

    return stopwords

def get_english_stopwords():
    with open("stopwords-en.txt", "r", encoding="utf-8") as file:
        stopwords = file.read().splitlines()

    for i in range(len(stopwords)):
        # if string starts with #, ignore it
        if stopwords[i].startswith("#"):
            continue
        stopwords[i] = stopwords[i].strip()

    return stopwords

def get_spacy_sentences(nlp, text):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return sentences

def get_spacy_entities(nlp, text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
    return entities

def get_spacy_tokens(nlp, text):
    doc = nlp(text)
    tokens = [token.text for token in doc]
    return tokens

def get_nltk_tokens(text):
    words = word_tokenize(text)
    return words

def get_nltk_sentences(text):
    sentences = sent_tokenize(text)
    return sentences

def get_hlc_entities(session, text):
    # get the text and id from entities in the database

    result = session.run(
        "MATCH (e:Entity) "
        "return e.text as text, e.id as id"
    )
    entities = {record["id"]: record["text"] for record in result}

    # filter the entities based on the text
    hlc_entities = []
    for entity_id, entity_text in entities.items():
        if entity_text in text:
            hlc_entities.append({
                "text": entity_text, 
                "id": entity_id,
                "recommended_by": "HLC",
                })
    return hlc_entities

def main():
    stopwords = get_german_stopwords()

    text = "Bruce Lee (chinesisch 李小龍 / 李小龙, Pinyin Lǐ Xiǎolóng, Jyutping Lei5 Siu2lung4, kantonesisch Lee Siu-lung, * 27. November 1940 in San Francisco; † 20. Juli 1973 in Hongkong; geboren als Lee Jun-fan 李振藩, Lǐ Zhènfán, Jyutping Lei5 Zan3faan4) war ein sinoamerikanischer Schauspieler, Kampfkünstler und Kampfkunst-Ausbilder.[1] Er gilt als Ikone des Martial-Arts-Films und wird von vielen als größter Kampfkünstler des 20. Jahrhunderts angesehen.[2][3] Er entwickelte den Kampfkunststil Jeet Kune Do."
    llc = get_low_level_concepts(text)
    print("Low-Level Concepts:", llc)

    mlc = get_medium_level_concepts(text, stopwords)
    print("Medium-Level Concepts:", mlc)

if __name__ == "__main__":
    main()