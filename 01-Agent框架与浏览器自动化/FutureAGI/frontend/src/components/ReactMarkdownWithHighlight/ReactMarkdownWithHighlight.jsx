import PropTypes from "prop-types";
import React from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeRaw from "rehype-raw";
import { useTheme } from "@mui/material";
import remarkGfm from "remark-gfm";
import "./reactMarkdownWithHighlight.css";

// Add 'style' to allowed properties for <span>
const customSanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    span: [...(defaultSchema.attributes?.span || []), "style"],
  },
};

const preprocessContent = (text, variables, theme) => {
  return text?.replace(/\{\{(.*?)\}\}/g, (match, p1) => {
    const isValid = variables.includes(p1.trim());
    const color = isValid
      ? theme?.palette?.green["600"]
      : theme?.palette?.red["600"];
    return `<span style="color: ${color}">${match}</span>`;
  });
};

const MarkdownWithVariableHighlight = ({ content, variables = [] }) => {
  const theme = useTheme();
  const processedContent = preprocessContent(content, variables, theme);

  return (
    <div
      style={{
        width: "100%",
        overflowX: "hidden",
        overflowY: "auto",
      }}
    >
      <div className="md-root">
        <ReactMarkdown
          remarkPlugins={[[remarkGfm, { singleTilde: false }]]}
          rehypePlugins={[rehypeRaw, [rehypeSanitize, customSanitizeSchema]]}
          components={{
            span: ({ node, ...props }) => <span {...props} />,
            a: ({ node, ...props }) => (
              <a {...props} target="_blank" rel="noopener noreferrer" />
            ),
            p: ({ node, ...props }) => <p {...props} style={{ margin: 0 }} />,
          }}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    </div>
  );
};

MarkdownWithVariableHighlight.propTypes = {
  content: PropTypes.string,
  variables: PropTypes.array,
};

export default MarkdownWithVariableHighlight;
