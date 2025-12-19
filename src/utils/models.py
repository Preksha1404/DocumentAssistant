from google.generativeai import GenerativeModel
from langchain_huggingface import HuggingFaceEmbeddings

class Models:
    _llm = None
    _embeddings = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = GenerativeModel("gemini-2.5-flash")
        return self._llm

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name="pritamdeka/S-Biomed-Roberta-snli-multinli-stsb",
                model_kwargs={"device": "cpu"}
            )
        return self._embeddings

models = Models()




# Local HuggingFace models
# from transformers import pipeline
# from google.generativeai import GenerativeModel
# from langchain_huggingface import HuggingFaceEmbeddings

# class Models:
#     _llm = None
#     _summarizer = None
#     _topic_classifier = None
#     _sentiment = None
#     _embedding_model = None
#     _langchain_embeddings = None

#     @property
#     def llm(self):
#         if self._llm is None:
#             self._llm = GenerativeModel("gemini-2.5-flash")
#         return self._llm

#     @property
#     def summarizer(self):
#         if self._summarizer is None:
#             self._summarizer = pipeline(
#                 "summarization",
#                 model="sshleifer/distilbart-cnn-12-6"
#             )
#         return self._summarizer

#     @property
#     def topic_classifier(self):
#         if self._topic_classifier is None:
#             self._topic_classifier = pipeline(
#                 "zero-shot-classification",
#                 model="valhalla/distilbart-mnli-12-3"
#             )
#         return self._topic_classifier

#     @property
#     def sentiment(self):
#         if self._sentiment is None:
#             self._sentiment = pipeline(
#                 "text-classification",
#                 model="distilbert-base-uncased-finetuned-sst-2-english"
#             )
#         return self._sentiment

#     @property
#     def langchain_embeddings(self):
#         if self._langchain_embeddings is None:
#             self._langchain_embeddings = HuggingFaceEmbeddings(
#                 model_name="pritamdeka/S-Biomed-Roberta-snli-multinli-stsb"
#             )
#         return self._langchain_embeddings

# # Instantiate a single global object
# models = Models()