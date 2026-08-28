import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect, useRef, useState } from "react";
import MarkdownWithVariableHighlight from "../ReactMarkdownWithHighlight";
import PromptLoadingStages from "../PromptLoadingStages/PromptLoadingStages";
import { GENERATE_PROMPT_LOADING_STAGES } from "src/utils/constants";
import { ShowComponent } from "src/components/show";

export default function GeneratedPromptField({
  generatedPrompt,
  allColumns = [],
  loadingStage,
  streamedText,
}) {
  const variables = allColumns?.map((col) => col.headerName) ?? [];
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

  function onLoadingComplete() {
    // console.log("Loading complete");
  }

  return (
    <Box
      ref={boxRef}
      onScroll={handleScroll}
      sx={(theme) => ({
        border: "1px solid",
        borderColor: theme.palette.divider,
        overflowY: "auto",
        padding: theme.spacing(2),
        minHeight: "95%",
        borderRadius: theme.spacing(0.5),
      })}
    >
      {streamedText && (
        <Box
          sx={{
            typography: "s1",
            color: "text.primary",
            fontWeight: "fontWeightRegular",
          }}
        >
          <MarkdownWithVariableHighlight
            variables={variables}
            content={streamedText}
          />
        </Box>
      )}
      <ShowComponent condition={!streamedText}>
        {generatedPrompt ? (
          <Box
            sx={{
              typography: "s1",
              color: "text.primary",
              fontWeight: "fontWeightRegular",
            }}
          >
            <MarkdownWithVariableHighlight
              variables={variables}
              content={generatedPrompt}
            />
          </Box>
        ) : (
          <PromptLoadingStages
            stages={GENERATE_PROMPT_LOADING_STAGES}
            onFinish={onLoadingComplete}
            stage={loadingStage}
          />
        )}
      </ShowComponent>
    </Box>
  );
}

GeneratedPromptField.propTypes = {
  generatedPrompt: PropTypes.string,
  allColumns: PropTypes.array,
  loadingStage: PropTypes.string,
  streamedText: PropTypes.string,
};
