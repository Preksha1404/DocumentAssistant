from langchain.tools import tool
from transformers import pipeline
from google.generativeai import GenerativeModel

llm = GenerativeModel("gemini-2.5-flash")

summarizer = pipeline(
    "summarization",
    model="google/pegasus-xsum"
)

topic_classifier = pipeline(
    "zero-shot-classification",
    model="typeform/distilbert-base-uncased-mnli"
)

sentiment = pipeline(
    "text-classification",
    model="emilyalsentzer/Bio_ClinicalBERT"
)

@tool
def summarize_tool(text: str):
    """Summarize physiotherapy document text."""
    summary = summarizer(text)[0]["summary_text"]
    return f"Summary:\n{summary}"

@tool
def topic_tool(text: str):
    """Classify topic of document text."""
    labels = ["exercise therapy", "manual therapy", "electrotherapy", "pain management", "rehabilitation"]
    result = topic_classifier(text, labels)
    topic = result["labels"][0]
    return f"Detected Topic: {topic}"

@tool
def sentiment_tool(text: str):
    """Perform sentiment analysis on clinical text."""
    output = sentiment(text)[0]
    label = output["label"]
    score = round(output["score"], 3)
    return f"Sentiment: {label} (confidence: {score})"