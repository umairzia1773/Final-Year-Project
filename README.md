REQUIREMENT.TXT
======

The requirements.txt file specifies the dependencies required for the project:

**openai:** Provides access to OpenAI's GPT models for generating embeddings and processing natural language queries.

**langchain:** A framework for building applications that integrate large language models (LLMs) with external data sources, such as vector databases.

**faiss-cpu:** A library for efficient similarity search and clustering of dense vectors, enabling fast vector-based lookups on CPU.

**pypdf:** A library for reading and extracting text from PDF files.

**tiktoken:** A tokenizer library used to process text input efficiently, often in the context of LLM-based applications.


PYCACHE
=====

The __pycache__ directory is used by Python to store compiled bytecode files. 
These files have the extension .pyc and are created automatically when a Python script is run.


Thumbnail
====
**The image provides a high-level overview of a Retrieval-Augmented Generation (RAG) pipeline, illustrating the following process:**

**User Query:** A query is submitted by the user to retrieve relevant information.

**Similarity Search:** The query is used to perform a search in a Vector Database, retrieving the top 3 most similar results.

**Concatenation:** The retrieved results are concatenated and sent as Context to a Large Language Model (LLM).

**LLM Processing:** The LLM uses the provided context and the original query to Generate a Response.

This flow demonstrates how the RAG system combines external knowledge retrieval with language model capabilities to deliver contextual and accurate responses.

App
==
This app.py file implements a Streamlit-based chatbot application enhanced with Retrieval-Augmented Generation (RAG). Here's a brief description:

**Key Features:**
Title and API Key Setup:

Sets up the OpenAI API key using environment variables or databutton secrets.

Displays the title "RAG enhanced Chatbot" on the Streamlit interface.

**PDF Upload and Processing:**

Users can upload multiple PDF files using Streamlit's file uploader.
Extracts and processes the contents of the PDFs into a vector database (vectordb) for similarity search.

**Chatbot Prompt Design:**

Provides a predefined system prompt template to ensure responses are:
Based on PDF metadata (filename and page).
Concise and relevant to the user’s question.
Indicating irrelevance with "Not applicable."

**User Interaction:**

Displays previous chat messages and allows users to ask questions.
Checks if PDFs are uploaded; otherwise, prompts the user to upload them.

**Response Generation:**

Uses the vector database to find relevant PDF content based on user queries.
Calls OpenAI's ChatGPT in streaming mode to generate and display responses in real time.

**Session Management:**
Stores prompts and the vector database in Streamlit's session state to maintain chat history and context.

**Purpose:**
This app is designed to allow users to upload PDF documents and ask context-based questions. The chatbot fetches relevant content from the uploaded documents and provides answers with metadata references, offering a highly focused and interactive experience.
