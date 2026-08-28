import { Box, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect, useRef, useState } from "react";
import ImporvedPromptHeader from "./ImporvedPromptHeader";
import MarkdownWithVariableHighlight from "../ReactMarkdownWithHighlight";
import PromptLoadingStages from "../PromptLoadingStages/PromptLoadingStages";
import { IMPROVE_PROMPT_LOADING_STAGES } from "src/utils/constants";
import { ShowComponent } from "src/components/show";

const GeneratedMarkdown = ({ variables, content = "" }) => {
  return (
    <Box
      sx={{
        typography: "s1",
        color: "text.primary",
        fontWeight: "fontWeightRegular",
      }}
    >
      <MarkdownWithVariableHighlight variables={variables} content={content} />
    </Box>
  );
};

GeneratedMarkdown.propTypes = {
  content: PropTypes.string,
  variables: PropTypes.array,
};

export default function ImprovedPrompt({
  handleClose,
  variables = [],
  improvedPrompt,
  promptController,
  loadingStage,
  streamedText,
}) {
  const theme = useTheme();

  const boxRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (streamedText && boxRef.current && autoScroll) {
      boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }
  }, [streamedText, autoScroll]);

  const handleScroll = () => {
    if (boxRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = boxRef.current;
      const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;

      // If user scrolls up, disable auto-scroll
      // If user scrolls back to bottom, re-enable auto-scroll
      setAutoScroll(isAtBottom);
    }
  };

  return (
    <Box
      sx={{
        height: "100%",
        width: "550px",
        padding: theme.spacing(2),
        borderLeft: `1px solid ${theme.palette.divider}`,
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing(2),
      }}
    >
      <ImporvedPromptHeader
        handleClose={handleClose}
        promptController={promptController}
      />

      <Box
        ref={boxRef}
        onScroll={handleScroll}
        sx={{
          border: "1px solid",
          borderColor: theme.palette.divider,
          overflowY: "auto",
          padding: theme.spacing(2),
          minHeight: "95%",
          borderRadius: theme.spacing(0.5),
        }}
      >
        {streamedText && (
          <GeneratedMarkdown variables={variables} content={streamedText} />
        )}

        <ShowComponent condition={!streamedText}>
          {promptController?.isImprovingPrompt ? (
            <PromptLoadingStages
              stages={IMPROVE_PROMPT_LOADING_STAGES}
              // onFinish={onLoadingComplete}
              stage={loadingStage}
            />
          ) : (
            <GeneratedMarkdown content={improvedPrompt} variables={variables} />
          )}
        </ShowComponent>
      </Box>
    </Box>
  );
}

ImprovedPrompt.propTypes = {
  handleClose: PropTypes.func,
  variables: PropTypes.array,
  improvedPrompt: PropTypes.string,
  loadingStage: PropTypes.string,
  promptController: PropTypes.shape({
    hasNext: PropTypes.bool,
    hasPrevious: PropTypes.bool,
    onNext: PropTypes.func,
    onPrevious: PropTypes.func,
    copyCurrent: PropTypes.func,
    apply: PropTypes.func,
    isImprovingPrompt: PropTypes.bool,
  }),
  streamedText: PropTypes.string,
};
