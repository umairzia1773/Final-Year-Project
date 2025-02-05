CHATBOT RAG VERSION 1
=========================

**For the front-end : app.py**

**PDF parsing and indexing : brain.py**

**API keys are maintained over data button secret management**

**Indexed are stored over session state**

 

**Oversimplified explanation : (Retrieval) Fetch the top N similar contexts via similarity search from the indexed PDF files 
-> concatanate those to the prompt (Prompt Augumentation) 
-> Pass it to the LLM -> which further generates response (Generation) like any LLM does.**
