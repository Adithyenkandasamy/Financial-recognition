import React from 'react';

const AnswerDisplay = ({ answer }) => {
  return (
    <div>
      <h2>Answer</h2>
      {answer ? <p>{answer}</p> : <p>No answer available yet.</p>}
    </div>
  );
};

export default AnswerDisplay;
