import React, { useState } from 'react';
import FileUpload from './FileUpload';
import QuestionInput from './QuestionInput';
import AnswerDisplay from './AnswerDisplay';

function App() {
  const [answer, setAnswer] = useState("");

  const handleQuestionSubmit = async (question) => {
    const response = await fetch(`http://localhost:8000/ask/?question=${question}`);
    const data = await response.json();
    setAnswer(data.answer);
  };

  return (
    <div>
      <FileUpload />
      <QuestionInput onSubmit={handleQuestionSubmit} />
      <AnswerDisplay answer={answer} />
    </div>
  );
}

export default App;
