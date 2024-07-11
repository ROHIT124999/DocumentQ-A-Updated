from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

load_dotenv()

groq_api_key = os.getenv('GROQ_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")

prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the basis of provided pdf context only. Please provide the most accurate and a concise response less than 1000 words, based on the question
    <context>
    {context}
    </context>
    Question: {input}
    """
)

vector_store = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def vector_embedding(file_path):
    global vector_store
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    if not docs:
        return {"error": "No documents were loaded. Please check if the PDF file is readable."}
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(docs)
    
    if not final_documents:
        return {"error": "No text could be extracted from the document. Please check the content of your PDF file."}
    
    try:
        vector_store = FAISS.from_documents(final_documents, embeddings)
        return {"success": "Vector Store DB Is Ready"}
    except Exception as e:
        return {"error": f"An error occurred while creating the vector store: {str(e)}"}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        result = vector_embedding(file_path)
        os.remove(file_path)  # Remove the file after processing
        return jsonify(result)
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/query', methods=['POST'])
def query_documents():
    global vector_store
    data = request.json
    question = data.get('question')
    
    if not question or vector_store is None:
        return jsonify({"error": "Missing question or vector store not ready"}), 400
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vector_store.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    response = retrieval_chain.invoke({'input': question})
    
    return jsonify({
        "answer": response['answer'],
        "context": [doc.page_content for doc in response["context"]]
    })

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)