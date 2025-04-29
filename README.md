FYP PROPOSAL
==
This document contains complete detail of our project.


Intent.Json
==
This is the “intent,json” file which contains tags and patterns of questions , the chatbot may be asked by the user regarding web scrapping.


Training.py
==
This Python script trains a chatbot model using a neural network. It processes user input patterns from a JSON file, tokenizes and lemmatizes the words, and creates a bag-of-words representation. The model is built using TensorFlow, with dense layers and dropout for regularization. The output is a one-hot encoded vector representing the user's intent. The model is trained using stochastic gradient descent and saved for later use.


Chatbot.py
==
This Python script is used for predicting the intent of a user input in a chatbot. It loads pre-trained models and data (words, classes, and the model). The clean_up_sentence function tokenizes and lemmatizes the input, while bag_of_words converts the input into a binary bag-of-words representation. The predict_class function uses the model to predict the most likely intent based on the user's input, filtering results with a probability threshold and returning the top intents with their probabilities.

FYP POSTER
==
This PDF document contains the Final Year Project Poster of our Project named Web Scraper Bot. This Poster contains the Project's Abstract, Objectives, Methodology, System Architectre of how our project works, furthermore there are results and analysis that concludes the Project.
