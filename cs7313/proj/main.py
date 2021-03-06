import time
from joblib import Parallel, delayed

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.ensemble import RandomForestClassifier

from fastai import *
from fastai.text import *

import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from models.BERTSentiment import BERTSentimentClassifier
from datasets.dataset_creator import get_val_dataloader_for_dataset, get_train_dataloader_for_dataset, get_val_path_and_name, get_trn_path_and_name

number_of_samples = 50

def train_bert(dataset, freeze_base, max_len, batch_size, learning_rate, print_per_n_lines, max_epochs):
    gpu = 0
    if torch.cuda.is_available():
        gpu = 1
    return "implement me"
    
def evaluate_bert(dataset):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if torch.cuda.is_available():
        net.cuda(gpu)
        
    start_time = time.time()
    print("Evaluating BERT on the " + dataset + " dataset using the " + str(device) + ".")
    dataloader = get_val_dataloader_for_dataset(dataset)
    criterion = nn.BCEWithLogitsLoss()
    net = BERTSentimentClassifier() # for now, we will automatically do BERT, later will generalize to any 
    net.eval()
    
    mean_accuracy, mean_loss = 0, 0
    count = 0

    with torch.no_grad():
        for seq, attention_masks, labels in dataloader:
            if torch.cuda.is_available():
                seq, attention_masks, labels = seq.cuda(), attention_masks.cuda(), labels.cuda()
            logits = net(seq, attention_masks)
            mean_loss += criterion(logits.squeeze(-1), labels.float()).item()
            mean_accuracy += get_accuracy_from_logits(logits, labels)
            count += 1
    
    print("Accuracy: ")
    print(mean_accuracy / count)
    print("Avg loss: ")
    print(mean_loss / count)
    print("Done in {} seconds".format(time.time() - start_time))

def get_accuracy_from_logits(logits, labels):
    probs = torch.sigmoid(logits.unsqueeze(-1))
    soft_probs = (probs > 0.5).long()
    acc = (soft_probs.squeeze() == labels).float().mean()
    return acc

def create_token_dict(df, all_words):
    t = [
            ( 
                {
                    word: (word in word_tokenize(getattr(row, "text"))) for word in all_words
                }, getattr(row, "label")
            ) 
            for row in df.itertuples(index=True, name='Pandas')
        ]
    return t

def train_nb(dataset):
    print("Training a Naive Bayes classifier on ", dataset)
    start_time = time.time()
    dataset_path, file_name = get_trn_path_and_name(dataset)
    train_df = pd.read_csv(dataset_path + file_name)
   
    dataset_path, file_name = get_val_path_and_name(dataset)
    val_df = pd.read_csv(dataset_path + file_name)
    
    df = pd.concat([train_df, val_df])
    
    list_of_docs = list(df['text'])
    all_words = set(word.lower() for doc in list_of_docs for word in word_tokenize(doc))
    
    print("Tokenizing took {} seconds".format(time.time() - start_time))
    start_time = time.time()
    print("Starting token dictionary creation of ", len(train_df), " entries.")
    t = create_token_dict(train_df.head(number_of_samples), all_words)
    print("Creating a token dictionary took {} seconds".format(time.time() - start_time))
    start_time = time.time()
    classifier = nltk.NaiveBayesClassifier.train(t)
    print("Training took {} seconds".format(time.time() - start_time))
    return classifier, all_words
    
def evaluate_nb(dataset, classifier, all_words):
    print("Evaluating a Naive Bayes classifier on ", dataset)
    start_time = time.time()
    dataset_path, file_name = get_val_path_and_name(dataset)
    df = pd.read_csv(dataset_path + file_name)
    
    val_set = list(df['text'])[0:number_of_samples]
    tokenized_val_set = [{ word: (word in word_tokenize(test_sample.lower())) for word in all_words } for test_sample in val_set]
    print("Tokenizing took {} seconds".format(time.time() - start_time))
    start_time = time.time()
    results = [ classifier.classify(test_sample) for test_sample in tokenized_val_set ]
    
    print("Classification took {} seconds".format(time.time() - start_time))
    ground_truth = list(df['label'])
    
    differences = [results[i] - ground_truth[i] for i in range(len(results))]
    accuracy = differences.count(0) / len(results)
    print("Accuracy: ", accuracy)

    
def process_features_for_rf(features):
    # this processing function is taken from the following source:
    # https://stackabuse.com/python-for-nlp-sentiment-analysis-with-scikit-learn/
    
    processed_features = []
    for sentence in range(0, len(features)):
        # Remove all the special characters
        processed_feature = re.sub(r'\W', ' ', str(features[sentence]))

        # remove all single characters
        processed_feature= re.sub(r'\s+[a-zA-Z]\s+', ' ', processed_feature)

        # Remove single characters from the start
        processed_feature = re.sub(r'\^[a-zA-Z]\s+', ' ', processed_feature) 

        # Substituting multiple spaces with single space
        processed_feature = re.sub(r'\s+', ' ', processed_feature, flags=re.I)

        # Removing prefixed 'b'
        processed_feature = re.sub(r'^b\s+', '', processed_feature)

        # Converting to Lowercase
        processed_feature = processed_feature.lower()

        processed_features.append(processed_feature)
    return processed_features

def train_and_evaluate_rf(dataset):
    print("Training a Random Forrest classifier on ", dataset)
    start_time = time.time()
    dataset_path, file_name = get_trn_path_and_name(dataset)
    train_df = pd.read_csv(dataset_path + file_name)
   
    dataset_path, file_name = get_val_path_and_name(dataset)
    val_df = pd.read_csv(dataset_path + file_name)
    
    df = pd.concat([train_df, val_df])
    
    features = df.text.values
    labels = df.labels.values
    
    processed_features = process_features_for_rf(features)
    print("Processing features took took {} seconds".format(time.time() - start_time))
    start_time = time.time()
    
    vectorizer = TfidfVectorizer(max_features=2500, min_df=7, max_df=0.8, stop_words=stopwords.words('english'))
    processed_features = vectorizer.fit_transform(processed_features).toarray()
    
    X_train, X_test, y_train, y_test = train_test_split(processed_features, labels, test_size=0.2, random_state=0)
    
    print("Vectorizing took {} seconds".format(time.time() - start_time))
    start_time = time.time()
    
    text_classifier = RandomForestClassifier(n_estimators=200, random_state=0)
    text_classifier.fit(X_train, y_train)
    
    print("Training took {} seconds".format(time.time() - start_time))
    
    print(confusion_matrix(y_test,predictions))
    print(classification_report(y_test,predictions))
    print(accuracy_score(y_test, predictions))
    