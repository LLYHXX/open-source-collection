export const fileIcons = {
  docx: "/icons/fileIcons/docx.svg",
  doc: "/icons/fileIcons/doc.svg",
  txt: "/icons/fileIcons/txt.svg",
  pdf: "/icons/fileIcons/pdf.svg",
  rtf: "/icons/fileIcons/rtf.svg",
  default: "/icons/fileIcons/default.svg",
};

export const getFileIcon = (fileType, defaultIcon = "default") => {
  return fileIcons[fileType] || fileIcons[defaultIcon];
};

export const statusIcons = {
  Processing: "/assets/icons/ic_processing.svg",
  Failed: "/assets/icons/ic_failed.svg",
  Completed: "/assets/icons/ic_completed.svg",
};
