import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useLayoutEffect, useMemo, useRef } from "react";
import { computeAlignedDiff } from "./diffUtils";
import PromptPanel from "./PromptPanel";

function useSyncRowHeights(leftRef, rightRef, deps) {
  useLayoutEffect(() => {
    const leftRows = leftRef.current?.children;
    const rightRows = rightRef.current?.children;
    if (!leftRows || !rightRows) return;

    for (let i = 0; i < leftRows.length; i += 1) {
      leftRows[i].style.minHeight = "24px";
    }
    for (let i = 0; i < rightRows.length; i += 1) {
      rightRows[i].style.minHeight = "24px";
    }

    const count = Math.min(leftRows.length, rightRows.length);
    for (let i = 0; i < count; i += 1) {
      const leftH = leftRows[i].scrollHeight;
      const rightH = rightRows[i].scrollHeight;
      const maxH = Math.max(leftH, rightH, 24);
      leftRows[i].style.minHeight = `${maxH}px`;
      rightRows[i].style.minHeight = `${maxH}px`;
    }
  }, deps);
}

const PromptDiffView = ({ originalPrompt, optimizedPrompt }) => {
  const leftRef = useRef(null);
  const rightRef = useRef(null);

  const { leftLines, rightLines } = useMemo(
    () => computeAlignedDiff(originalPrompt, optimizedPrompt),
    [originalPrompt, optimizedPrompt],
  );

  useSyncRowHeights(leftRef, rightRef, [leftLines, rightLines]);

  if (!originalPrompt && !optimizedPrompt) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 4,
          color: "text.disabled",
        }}
      >
        <Typography typography="s1">No prompts available</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", gap: 1, height: "100%" }}>
      <Box sx={{ flex: 1 }}>
        <PromptPanel
          title="AGENT PROMPT"
          prompt={originalPrompt}
          diffLines={leftLines}
          panelRef={leftRef}
        />
      </Box>
      <Box sx={{ flex: 1 }}>
        <PromptPanel
          title="OPTIMIZED AGENT PROMPT"
          prompt={optimizedPrompt}
          diffLines={rightLines}
          panelRef={rightRef}
        />
      </Box>
    </Box>
  );
};

PromptDiffView.propTypes = {
  originalPrompt: PropTypes.string,
  optimizedPrompt: PropTypes.string,
};

export default PromptDiffView;
