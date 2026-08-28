import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import ImageEmbed from "../EmbedComponents/ImageEmbed";
import { useFieldArray, useWatch } from "react-hook-form";
import AudioEmbed from "../EmbedComponents/AudioEmbed";
import { ShowComponent } from "src/components/show";
import PdfEmbed from "../EmbedComponents/PdfEmbed";

const ImagePreview = ({ files, links, remove, removeLink }) => {
  return (
    <>
      {files?.map((file, index) => (
        <ImageEmbed
          key={file.id}
          url={file.previewUrl}
          name={file.name}
          size={file.size}
          onDelete={() => remove(index)}
        />
      ))}
      {links?.map((link, index) => (
        <ImageEmbed
          key={link.id}
          url={link.url}
          name={`Image ${index + 1}`}
          onDelete={() => removeLink(index)}
        />
      ))}
    </>
  );
};

ImagePreview.propTypes = {
  files: PropTypes.array,
  links: PropTypes.array,
  remove: PropTypes.func,
  removeLink: PropTypes.func,
};

const AudioPreview = ({ files, links, remove, removeLink }) => {
  return (
    <>
      {files?.map((file, index) => (
        <AudioEmbed
          key={file.id}
          url={file.previewUrl}
          name={file.name}
          size={file.size}
          onDelete={() => remove(index)}
          mimeType={file.type}
        />
      ))}
      {links?.map((link, index) => (
        <AudioEmbed
          key={link.id}
          url={link.url}
          name={`Audio ${index + 1}`}
          onDelete={() => removeLink(index)}
          mimeType={link.type}
        />
      ))}
    </>
  );
};

AudioPreview.propTypes = {
  files: PropTypes.array,
  links: PropTypes.array,
  remove: PropTypes.func,
  removeLink: PropTypes.func,
};

const PdfPreview = ({ files, links, remove, removeLink }) => {
  return (
    <>
      {files?.map((file, index) => (
        <PdfEmbed
          key={file.id}
          url={file.previewUrl}
          name={file.name}
          size={file.size}
          onDelete={() => remove(index)}
        />
      ))}
      {links?.map((link, index) => (
        <PdfEmbed
          key={link.id}
          url={link.url}
          name={`Pdf ${index + 1}`}
          onDelete={() => removeLink(index)}
        />
      ))}
    </>
  );
};

PdfPreview.propTypes = {
  files: PropTypes.array,
  links: PropTypes.array,
  remove: PropTypes.func,
  removeLink: PropTypes.func,
};

const UploadPreview = ({ control, type }) => {
  const { remove } = useFieldArray({
    name: "files",
    control,
  });

  const files = useWatch({
    control,
    name: "files",
  });

  const links = useWatch({
    control,
    name: "links",
  });

  const { remove: removeLink } = useFieldArray({
    name: "links",
    control,
  });

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1,
        overflow: "auto",
        flex: 1,
      }}
    >
      <ShowComponent condition={type === "image"}>
        <ImagePreview
          files={files}
          links={links}
          remove={remove}
          removeLink={removeLink}
        />
      </ShowComponent>
      <ShowComponent condition={type === "audio"}>
        <AudioPreview
          files={files}
          links={links}
          remove={remove}
          removeLink={removeLink}
        />
      </ShowComponent>
      <ShowComponent condition={type === "pdf"}>
        <PdfPreview
          files={files}
          links={links}
          remove={remove}
          removeLink={removeLink}
        />
      </ShowComponent>
    </Box>
  );
};

UploadPreview.propTypes = {
  control: PropTypes.object.isRequired,
  type: PropTypes.string.isRequired,
};

export default UploadPreview;
