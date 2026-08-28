import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Collapse, Typography, keyframes } from "@mui/material";
import Iconify from "src/components/iconify";
import MarkdownWithVariableHighlight from "src/components/ReactMarkdownWithHighlight";
import { PROMPT_RESULT_TYPES } from "../common";

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
`;

const ThinkingBlock = ({ content, isThinking, outputType, sx = {} }) => {
  const [expanded, setExpanded] = useState(true);
  return (
    <Box
      sx={{
        mb: 1.5,
        border: "1px solid",
        borderColor: "border.default",
        borderRadius: 1,
        p: 1.5,
        py: 0.5,
        ...sx,
      }}
    >
      <Box
        onClick={() => setExpanded((prev) => !prev)}
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 0.5,
          cursor: "pointer",
          userSelect: "none",
          color: "text.secondary",
          py: 0.5,
        }}
      >
        <Iconify
          icon="material-symbols:arrow-forward-ios-rounded"
          width={14}
          sx={{
            transform: expanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        />
        <Typography
          typography="s2_1"
          color="text.secondary"
          fontWeight="fontWeightMedium"
          sx={
            isThinking
              ? { animation: `${pulse} 1.5s ease-in-out infinite` }
              : undefined
          }
        >
          {isThinking ? "Thinking..." : "Thoughts"}
        </Typography>
      </Box>
      <Collapse in={expanded}>
        <Box
          sx={{
            pl: 1.5,
          }}
        >
          {outputType === PROMPT_RESULT_TYPES.MARKDOWN ? (
            <Box
              sx={{
                my: 1.5,
              }}
            >
              <MarkdownWithVariableHighlight content={content} />
            </Box>
          ) : (
            <Typography
              component="pre"
              typography="s2_1"
              color="text.secondary"
              sx={{ whiteSpace: "pre-wrap", wordWrap: "break-word" }}
            >
              {content}
            </Typography>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

ThinkingBlock.propTypes = {
  content: PropTypes.string,
  isThinking: PropTypes.bool,
  outputType: PropTypes.string,
  sx: PropTypes.object,
};

export default ThinkingBlock;
