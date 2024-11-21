import React from 'react';

const FileUpload = () => {
  const uploadFile = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    await fetch("http://localhost:8000/upload-pdf/", {
      method: "POST",
      body: formData,
    });
  };

  return <input type="file" accept="application/pdf" onChange={uploadFile} />;
};

export default FileUpload;
