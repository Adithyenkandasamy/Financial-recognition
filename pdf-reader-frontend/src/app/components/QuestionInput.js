import React, { useState } from 'react';

const QuestionInput = ({ onAskQuestion }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    onAskQuestion(question);
    setQuestion('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Ask a Question</h2>
      <input
        type="text"
        placeholder="Type your question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        required
      />
      <button type="submit">Ask</button>
    </form>
  );
};

export default QuestionInput;
