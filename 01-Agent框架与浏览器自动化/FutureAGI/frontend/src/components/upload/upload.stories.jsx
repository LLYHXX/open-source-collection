import logger from "src/utils/logger";
import Upload from "./upload";

const meta = {
  component: Upload,
  title: "UI Components/Upload",
};

export default meta;

const Template = (args) => {
  return <Upload {...args} />;
};

export const Default = Template.bind({});

Default.args = {
  multiple: false,
  error: false,
  file: null,
  files: [],
  helperText: "I am helper Text",
  onDelete: () => logger.debug("Delete file"),
  onRemove: () => logger.debug("Remove file"),
  onRemoveAll: () => logger.debug("Remove all files"),
  onUpload: () => logger.debug("Upload files"),
  thumbnail: false,
  showIllustration: true,
};

export const MultipleFiles = Template.bind({});

MultipleFiles.args = {
  multiple: true,
  error: false,
  file: null,
  files: [
    { name: "file1.txt", size: 1024 },
    { name: "file2.txt", size: 2048 },
  ],
  helperText: null,
  onDelete: () => logger.debug("Delete file"),
  onRemove: () => logger.debug("Remove file"),
  onRemoveAll: () => logger.debug("Remove all files"),
  onUpload: () => logger.debug("Upload files"),
  thumbnail: false,
  showIllustration: true,
};

export const Error = Template.bind({});

Error.args = {
  multiple: false,
  error: true,
  file: null,
  files: [],
  helperText: "Error message",
  onDelete: () => logger.debug("Delete file"),
  onRemove: () => logger.debug("Remove file"),
  onRemoveAll: () => logger.debug("Remove all files"),
  onUpload: () => logger.debug("Upload files"),
  thumbnail: false,
  showIllustration: true,
};
