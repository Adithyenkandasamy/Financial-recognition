import React, { useState } from 'react';

const QuestionInput = ({ onSubmit }) => {
  const [question, setQuestion] = useState("");

  const handleSubmit = () => {
    onSubmit(question);
  };

  return (
    <div>
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question"
      />
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
};

export default QuestionInput;
