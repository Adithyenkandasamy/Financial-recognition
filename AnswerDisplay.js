import React from 'react';

const AnswerDisplay = ({ answer }) => {
  return <div>{answer && <p>Answer: {answer}</p>}</div>;
};

export default AnswerDisplay;
