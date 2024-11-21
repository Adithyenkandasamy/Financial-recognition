import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import QuestionInput from './components/QuestionInput';
import AnswerDisplay from './components/AnswerDisplay';

const App = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [answer, setAnswer] = useState('');

  const handleFileUpload = (file) => {
    console.log('Uploaded file:', file);
    setUploadedFile(file);
  };

  const handleAskQuestion = async (question) => {
    if (!uploadedFile) {
      alert('Please upload a PDF first.');
      return;
    }

    const formData = new FormData();
    formData.append('pdf', uploadedFile);
    formData.append('question', question);

    try {
      const response = await fetch('http://localhost:5000/api/ask', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      console.error('Error fetching the answer:', error);
      alert('Failed to fetch the answer.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>PDF Reader App</h1>
      <FileUpload onFileUpload={handleFileUpload} />
      <QuestionInput onAskQuestion={handleAskQuestion} />
      <AnswerDisplay answer={answer} />
    </div>
  );
};

export default App;
