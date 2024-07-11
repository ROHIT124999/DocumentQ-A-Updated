import React, { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [context, setContext] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [isVectorStoreReady, setIsVectorStoreReady] = useState(false);
  const fileInputRef = useRef(null);

  const uploadFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setFileName(file.name);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (response.data.success) {
        setIsVectorStoreReady(true);
        alert(response.data.success);
      } else {
        alert(response.data.error);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('An error occurred while uploading the file');
    }
    setUploading(false);
  };

  const queryDocuments = async () => {
    if (!isVectorStoreReady) {
      alert('Please upload a PDF first');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/query', {
        question
      });
      setAnswer(response.data.answer);
      setContext(response.data.context);
    } catch (error) {
      console.error('Error querying documents:', error);
      alert('An error occurred while querying documents');
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header>
        <h1>Document Q&A</h1>
      </header>
      <main>
        <section className="upload-section">
          <input
            type="file"
            onChange={uploadFile}
            accept=".pdf"
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          <button onClick={() => fileInputRef.current.click()} disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>
          {fileName && <p>Uploaded: {fileName}</p>}
        </section>
        <section className="query-section">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the document"
          />
          <button onClick={queryDocuments} disabled={loading || !question || !isVectorStoreReady}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </section>
        {answer && (
          <section className="answer-section">
            <h2>Answer:</h2>
            <p>{answer}</p>
          </section>
        )}
        {context.length > 0 && (
          <section className="context-section">
            <h2>Related Excerpts:</h2>
            {context.map((text, index) => (
              <div key={index} className="context-item">
                <p>{text}</p>
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;