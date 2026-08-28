import { Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const textBgColorByStatus = {
  added: "var(--diff-added-bg)",
  removed: "var(--diff-removed-bg)",
  default: "transparent",
};

const textColorByStatus = {
  added: "var(--diff-added-text)",
  removed: "var(--diff-removed-text)",
  default: "inherit",
};

const GenerateDiffText = ({ cellText }) => {
  return (
    <Typography
      typography="s2"
      component="p"
      fontWeight="fontWeightRegular"
      sx={{ wordBreak: "break-word", whiteSpace: "normal" }}
    >
      {cellText?.map(({ text, status }, index) => {
        const prevStatus = cellText[index - 1]?.status;
        const nextStatus = cellText[index + 1]?.status;

        const isBoundary = (prev, current) =>
          (prev === "removed" && current !== "removed") ||
          (prev === "added" && current !== "added");

        const addPreSpace = index > 0 && isBoundary(prevStatus, status);
        const addNextSpace =
          index < cellText.length - 1 && isBoundary(nextStatus, status);

        return (
          <React.Fragment key={`${text}-${index}`}>
            {addPreSpace && " "}
            <Typography
              typography="s2"
              fontWeight="fontWeightRegular"
              component="span"
              sx={{
                backgroundColor: textBgColorByStatus[status || "default"],
                display: "inline-block",
                color: textColorByStatus[status || "default"],
                whiteSpace: "pre-wrap",
              }}
            >
              {text}
              {!addNextSpace && " "}
            </Typography>
            {addNextSpace && " "}
          </React.Fragment>
        );
      })}
    </Typography>
  );
};

GenerateDiffText.propTypes = {
  cellText: PropTypes.array,
};

export default GenerateDiffText;
