import React from "react";
import FileThumbnail from "./file-thumbnail";
import logger from "src/utils/logger";

const meta = {
  component: FileThumbnail,
  title: "UI Components/FileThumbnail",
};

export default meta;

const Template = (args) => <FileThumbnail {...args} />;

export const Default = Template.bind({});
Default.args = {
  file: {
    name: "example.jpg",
    path: "https://via.placeholder.com/150",
    preview: "https://via.placeholder.com/150",
  },
  tooltip: true,
  imageView: true,
  onDownload: () => logger.debug("Download button clicked"),
};

export const ImageFile = Template.bind({});
ImageFile.args = {
  file: {
    name: "example.jpg",
    path: "https://via.placeholder.com/150",
    preview: "https://via.placeholder.com/150",
  },
  tooltip: true,
  imageView: true,
  onDownload: () => logger.debug("Download button clicked"),
};

export const NonImageFile = Template.bind({});
NonImageFile.args = {
  file: {
    name: "example.pdf",
    path: "https://via.placeholder.com/150",
    preview: "",
  },
  tooltip: true,
  imageView: false,
  onDownload: () => logger.debug("Download button clicked"),
};

export const WithoutTooltip = Template.bind({});
WithoutTooltip.args = {
  file: {
    name: "example.jpg",
    path: "https://via.placeholder.com/150",
    preview: "https://via.placeholder.com/150",
  },
  tooltip: false,
  imageView: true,
  onDownload: () => logger.debug("Download button clicked"),
};

export const WithoutDownloadButton = Template.bind({});
WithoutDownloadButton.args = {
  file: {
    name: "example.jpg",
    path: "https://via.placeholder.com/150",
    preview: "https://via.placeholder.com/150",
  },
  tooltip: true,
  imageView: true,
};
