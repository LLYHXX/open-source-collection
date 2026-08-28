import React from "react";
import PropTypes from "prop-types";
import { Box, Typography, TableCell, styled } from "@mui/material";
import Image from "src/components/image";
import "yet-another-react-lightbox/styles.css";
import TruncatedText from "src/components/truncate-string/TruncateString";

const PerformanceTableCell = styled(TableCell)({
  padding: "8px",
  fontSize: "12px",
});

const ModelInputOutputCell = ({ contentType, content, onImageClick }) => {
  return contentType === "text" ? (
    <PerformanceTableCell sx={{ minWidth: "250px", maxWidth: "250px" }}>
      <TruncatedText maxLines={3}>{content}</TruncatedText>
    </PerformanceTableCell>
  ) : (
    <PerformanceTableCell sx={{ minWidth: "200px", maxWidth: "200px" }}>
      <Box>
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 1,
            flexDirection: "row",
          }}
        >
          {content
            ?.filter((o) => o["url"] !== undefined)
            .map(({ url }) => (
              <Image
                onClick={(e) => {
                  e.stopPropagation();
                  onImageClick?.(url);
                }}
                key={url}
                height={50}
                src={url}
                style={{ cursor: "pointer", borderRadius: "8px" }}
              />
            ))}
        </Box>
        <Box
          sx={{
            paddingY: 1,
            display: "flex",
            gap: 0.5,
            flexDirection: "column",
          }}
        >
          {content
            ?.filter((v) => v?.text?.length)
            ?.map(({ text }) => (
              <Typography key={text} fontSize="12px">
                <TruncatedText>{text}</TruncatedText>
              </Typography>
            ))}
        </Box>
      </Box>
    </PerformanceTableCell>
  );
};

export default ModelInputOutputCell;

ModelInputOutputCell.propTypes = {
  contentType: PropTypes.string,
  content: PropTypes.any,
  onImageClick: PropTypes.func,
};
