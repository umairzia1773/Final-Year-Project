# import os
# import pdfplumber
# import ollama
# from werkzeug.utils import secure_filename

# # Extract text from the uploaded PDF
# def extract_text_from_pdf(pdf_path):
#     try:
#         with pdfplumber.open(pdf_path) as pdf:
#             text = ""
#             for page in pdf.pages:
#                 page_text = page.extract_text()
#                 if page_text:
#                     text += page_text
#         return text
#     except Exception as e:
#         return f"Error during PDF extraction: {str(e)}"

# # Generate a response from Ollama
# def get_answer_from_ollama(question, context=""):
#     try:
#         # Combine context (PDF text) with the user question
#         full_prompt = f"{context}\n\nQuestion: {question}\nAnswer:"
#         response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": full_prompt}])

#         # Extract and return the answer from the response
#         if response and response.message and response.message.content:
#             answer = response.message.content.strip()

#             # Return the answer as is, with formatting applied (if necessary)
#             return format_structured_response(answer)
#         else:
#             return "Error: Unable to retrieve a valid response from the model."
#     except Exception as e:
#         return f"Error: {str(e)}"

# # Function to format the response with points or headings (without changing the content)
# def format_structured_response(response):
#     # Clean up unnecessary characters and whitespace
#     cleaned_response = response.strip()

#     # Split the response into distinct points if it contains lists or headings
#     if "1." in cleaned_response or "2." in cleaned_response or "3." in cleaned_response:
#         # Split the response into parts based on common point structures
#         parts = cleaned_response.split("\n")
#         structured_response = ""
#         for part in parts:
#             if part.strip():  # Only add non-empty lines
#                 structured_response += f"{part.strip()}\n"
#         return structured_response.strip()

#     # If it's not in a list or point format, simply return the cleaned response
#     return cleaned_response if cleaned_response else "Sorry, I couldn't understand that."

# # Main function to process PDF and question
# def get_answer_from_pdf(pdf_path, question):
#     try:
#         # Extract PDF text
#         pdf_text = extract_text_from_pdf(pdf_path)
#         if not pdf_text:
#             return "Error: Could not extract text from the uploaded PDF."

#         # Generate a response using Ollama with the PDF context and user question
#         answer = get_answer_from_ollama(question, context=pdf_text)
#         return answer
#     except Exception as e:
#         return f"Error: {str(e)}"
import os
import pdfplumber
import ollama
from werkzeug.utils import secure_filename

# Extract text from the uploaded PDF
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        return f"Error during PDF extraction: {str(e)}"

# Generate a response from Ollama
def get_answer_from_ollama(question, context=""):
    try:
        # Combine context (PDF text) with the user question
        full_prompt = f"{context}\n\nQuestion: {question}\nAnswer:"
        response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": full_prompt}])

        # Extract and return the answer from the response
        if response and response.message and response.message.content:
            return response.message.content.strip()
        else:
            return "Error: Unable to retrieve a valid response from the model."
    except Exception as e:
        return f"Error: {str(e)}"


# Main function to process PDF and question
def get_answer_from_pdf(pdf_path, question):
    try:
        # Extract PDF text
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            return "Error: Could not extract text from the uploaded PDF."

        # Generate a response using Ollama with the PDF context and user question
        answer = get_answer_from_ollama(question, context=pdf_text)
        return answer
    except Exception as e:
        return f"Error: {str(e)}"
