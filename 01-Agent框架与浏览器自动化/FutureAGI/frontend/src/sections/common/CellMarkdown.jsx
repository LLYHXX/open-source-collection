import Markdown from "react-markdown";
import React from "react";
import PropTypes from "prop-types";
import styled from "@emotion/styled";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";

const customSanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    span: [...(defaultSchema.attributes?.span || []), "style"],
    a: [...(defaultSchema.attributes?.a || []), "target", "rel"],
    table: [...(defaultSchema.attributes?.table || [])],
    thead: [...(defaultSchema.attributes?.thead || [])],
    tbody: [...(defaultSchema.attributes?.tbody || [])],
    tr: [...(defaultSchema.attributes?.tr || [])],
    th: [...(defaultSchema.attributes?.th || []), "align"],
    td: [...(defaultSchema.attributes?.td || []), "align"],
  },
  tagNames: [
    ...(defaultSchema.tagNames || []),
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
  ],
};

const MarkdownContainer = styled.div`
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  &::-webkit-scrollbar-track {
    box-shadow: none !important;
    background: transparent !important;
  }
  &::-webkit-scrollbar {
    background: transparent !important;
  }
  scrollbar-width: none;
  scrollbar-color: transparent;
  //negative margins are causing text overlapping
  p {
    margin: 0 0 ${({ spacing }) => spacing}px 0; // Add bottom margin
    padding: 0;
    font-size: ${({ fontSize }) => fontSize}px;
  }

  p + ul,
  p + ol {
    margin-top: ${({ spacing }) => spacing}px; // ✅ Positive spacing
  }

  li > ul,
  li > ol {
    margin-top: ${({ spacing }) => spacing / 2}px; // ✅ Half spacing for nested
  }

  li {
    margin-bottom: ${({ spacing }) => spacing}px;
    line-height: 1.6; /* Better vertical spacing between list items */
    display: list-item; /* Ensure proper list item display */
    list-style-position: outside; /* Keep bullet/number outside text */
  }

  ul,
  ol {
    margin: ${({ spacing }) => spacing}px 0;
    padding-left: 20px; /* Minimal padding for bullet alignment */
    font-size: ${({ fontSize }) => fontSize}px;
    list-style-position: outside; /* Bullets align on same x-axis as text */
  }
  h1 {
    font-size: ${({ headingSizes }) => headingSizes.h1}px;
  }

  h2 {
    font-size: ${({ headingSizes }) => headingSizes.h2}px;
  }

  h3 {
    font-size: ${({ headingSizes }) => headingSizes.h3}px;
  }

  h4 {
    font-size: ${({ headingSizes }) => headingSizes.h4}px;
  }

  h5 {
    font-size: ${({ headingSizes }) => headingSizes.h5}px;
  }

  h6 {
    font-size: ${({ headingSizes }) => headingSizes.h6}px;
  }

  pre {
    white-space: pre-wrap;
    word-break: break-word;
  }

  code {
    font-size: ${({ headingSizes }) => headingSizes.code}px;
  }

  p,
  li,
  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    white-space: normal;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  pre {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  code {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: break-word;
    font-size: ${({ headingSizes }) => headingSizes.code}px;
  }

  table {
    border-collapse: collapse;
    width: 100%;
    max-width: 100%;
    margin: 16px 0;
    font-size: ${({ fontSize }) => fontSize}px;
    table-layout: auto;
  }

  th,
  td {
    border: 1px solid var(--border-default);
    padding: 8px;
    text-align: left;
    overflow-wrap: break-word;
    word-break: break-word;
  }

  th {
    font-weight: bold;
  }
`;

const preprocessMarkdown = (text) => {
  if (!text || typeof text !== "string") return "";

  let processedText = text.trim();

  // Strip HTML document structure if present (LLM sometimes outputs full HTML)
  if (processedText.includes("<!DOCTYPE") || processedText.includes("<html")) {
    const bodyMatch = processedText.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) {
      processedText = bodyMatch[1];
    } else {
      processedText = processedText
        .replace(/<!DOCTYPE[^>]*>/gi, "")
        .replace(/<\/?html[^>]*>/gi, "")
        .replace(/<head>[\s\S]*?<\/head>/gi, "")
        .replace(/<\/?body[^>]*>/gi, "");
    }
  }

  // Comprehensive HTML tag cleanup - handles malformed tags with spaces
  processedText = processedText
    .replace(/<\s*\/\s*([a-z]+)\s*>/gi, "</$1>") // "< / li >" → "</li>" (closing tags)
    .replace(/<\s+/g, "<") // "< " → "<" (opening bracket with spaces)
    .replace(/\s+>/g, ">"); // " >" → ">" (closing bracket with spaces)

  const formattedString = processedText
    .trim()
    .replace(/\\n/g, "\n") // Unescape newlines
    .replace(/[ \t]+/g, " ") // Collapse multiple spaces/tabs
    .replace(/\n[ \t]+/g, "\n") // Remove space at line start
    .replace(/\n\s*\n\s*\n/g, "\n\n") // Collapse multiple newlines
    .replace(/(#+\s)/g, "\n$1") // Add newline before headers
    .replace(/(?:^|\s)--\s(.+?)(?=(?:\s--|\s-\s|$))/g, "\n  - $1") // Format dashes as bullets
    .replace(/(?:^|\s)-\s(.+?)(?=(?:\s--|\s-\s|$))/g, "\n- $1") // Format hyphens as bullets
    .replace(/^(\d+)\.\s+/gm, "$1. ") // Preserve ordered list numbering (e.g., "1. ", "2. ")
    .replace(/^[`"'""'']+/, "") // Remove leading quotes
    .replace(/[`"'""'']+$/, "") // Remove trailing quotes
    .replace(/^\s+/, "") // Remove leading whitespace
    .replace(/^```[\w]*\n?/, "") // Remove opening code fence
    .replace(/\n?```$/, "") // Remove closing code fence
    .replace(/\*\*\*+/g, "---"); // Normalize triple symbols

  return String(formattedString);
};

// Custom link component to open in new tab
const LinkComponent = ({ href, children, ...props }) => (
  <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
    {children}
  </a>
);

LinkComponent.propTypes = {
  href: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

const CellMarkdown = ({
  text,
  fontSize = 14,
  spacing = 8,
  headingSizes = {
    h1: 14,
    h2: 13,
    h3: 12,
    h4: 11,
    h5: 10,
    h6: 9,
    code: 12,
  },
}) => {
  return (
    <MarkdownContainer
      fontSize={fontSize}
      spacing={spacing}
      headingSizes={headingSizes}
    >
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, customSanitizeSchema]]}
        components={{
          a: LinkComponent,
        }}
      >
        {preprocessMarkdown(text)}
      </Markdown>
    </MarkdownContainer>
  );
};

CellMarkdown.propTypes = {
  text: PropTypes.string,
  fontSize: PropTypes.number,
  spacing: PropTypes.number,
  headingSizes: PropTypes.shape({
    h1: PropTypes.number,
    h2: PropTypes.number,
    h3: PropTypes.number,
    h4: PropTypes.number,
    h5: PropTypes.number,
    h6: PropTypes.number,
    code: PropTypes.number,
  }),
};

export default CellMarkdown;
