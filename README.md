FYP PROPOSAL
==
This document contains complete detail of our project.

Intent.Json
==
This is the “intent,json” file which contains tags and patterns of questions , the chatbot may be asked by the user regarding web scrapping.

Training.py
==
This Python script trains a chatbot model using a neural network. It processes user input patterns from a JSON file, tokenizes and lemmatizes the words, and creates a bag-of-words representation. The model is built using TensorFlow, with dense layers and dropout for regularization. The output is a one-hot encoded vector representing the user's intent. The model is trained using stochastic gradient descent and saved for later use.
