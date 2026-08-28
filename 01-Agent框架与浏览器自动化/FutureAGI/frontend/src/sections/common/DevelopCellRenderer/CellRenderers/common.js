import _ from "lodash";

export const getFileTypeFromMime = (mimeType) => {
  const mimeMap = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
      "docx",
    "application/msword": "doc",
    "text/plain": "txt",
  };
  return mimeMap[mimeType] || "file";
};

export const getExtensionFromMime = (mimeType) => {
  const mimeMap = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
      "docx",
    "application/msword": "doc",
    "text/plain": "txt",
  };
  return mimeMap[mimeType] || "file";
};

export const extractFilenameFromDataURL = (dataURL) => {
  try {
    // Try to extract filename from data URL if it contains name parameter
    const nameMatch = dataURL.match(/name=([^;,]+)/);
    if (nameMatch) {
      return decodeURIComponent(nameMatch[1]);
    }

    // If no name parameter, generate from MIME type
    const mimeMatch = dataURL.match(/data:([^;]+)/);
    if (mimeMatch) {
      const mimeType = mimeMatch[1];
      const extension = getExtensionFromMime(mimeType);
      return `document.${extension}`;
    }

    return "document";
  } catch (error) {
    return "document";
  }
};

export const acceptedFilesForDataset = ["docx", "doc", "pdf", "txt"];

export const getFileType = (value) => {
  if (acceptedFilesForDataset.includes(_.toLower(value))) {
    return value;
  } else {
    return "pdf";
  }
};
