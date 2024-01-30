from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders.csv_loader import CSVLoader
import csv

from dotenv import load_dotenv
import os

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

if google_api_key is None:
    raise ValueError("GOOGLE_API_KEY not found in the environment variables.")


file_path = 'codebasics_faqs.csv'
encoding = 'Windows-1252'  
source_column = "prompt"

vectordb_file_path = "faiss_index"


llm = ChatGoogleGenerativeAI(model="gemini-pro",google_api_key=google_api_key, temperature=0.2)
embeddings = HuggingFaceEmbeddings()


def create_vector_db():

    loader = CSVLoader(file_path=file_path, source_column=source_column, encoding=encoding)

    try:
        data1 = loader.load()
    except UnicodeDecodeError as e:
        print(f"Error loading CSV file: {e}")
    except csv.Error as e:
        print(f"CSV error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Create a FAISS instance for vector database from 'data'
    vectordb = FAISS.from_documents(documents=data1,
                                    embedding=embeddings)

    # Save vector database locally
    vectordb.save_local(vectordb_file_path)


def get_qa_chain():
    # Load the vector database from the local folder
    vectordb = FAISS.load_local(vectordb_file_path, embeddings)

    # Create a retriever for querying the vector database
    retriever = vectordb.as_retriever(score_threshold=0.7)

    prompt_template = """Given the following context and a question, generate an answer based on this context only.
    In the answer try to provide as much text as possible from "response" section in the source document context without making much changes.
    If the answer is not found in the context, kindly state "I don't know." Don't try to make up an answer.

    CONTEXT: {context}

    QUESTION: {question}"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain = RetrievalQA.from_chain_type(llm=llm,
                                        chain_type="stuff",
                                        retriever=retriever,
                                        input_key="query",
                                        return_source_documents=True,
                                        chain_type_kwargs={"prompt": PROMPT})

    return chain



if __name__ == "__main__":
    create_vector_db()
    chain = get_qa_chain()
    print(chain("Do you have javascript course?"))


