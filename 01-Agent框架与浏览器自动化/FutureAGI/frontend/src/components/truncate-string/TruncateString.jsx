import React, { useRef, useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";

const TruncatedText = ({ children, maxLines = 1, sx }) => {
  const textRef = useRef(null);
  const [truncated, setTruncated] = useState(false);

  useEffect(() => {
    const checkTruncation = () => {
      if (textRef.current) {
        const lineHeight = parseInt(
          getComputedStyle(textRef.current).lineHeight,
        );
        const maxHeight = lineHeight * maxLines;
        setTruncated(textRef.current.scrollHeight > maxHeight);
      }
    };

    checkTruncation();
    window.addEventListener("resize", checkTruncation);

    return () => {
      window.removeEventListener("resize", checkTruncation);
    };
  }, [children, maxLines]);

  if (typeof children !== "string") {
    return <div style={{ width: "100%" }}>-</div>;
  }

  return (
    <Box
      ref={textRef}
      style={{
        width: "100%",
        overflow: "hidden",
        textOverflow: "ellipsis",
        display: "-webkit-box",
        WebkitLineClamp: maxLines,
        WebkitBoxOrient: "vertical",
      }}
      sx={sx}
    >
      {children}
      {truncated && (
        <span style={{ display: "inline-block", width: 0 }}>...</span>
      )}
    </Box>
  );
};

TruncatedText.propTypes = {
  children: PropTypes.any,
  maxLines: PropTypes.number,
  sx: PropTypes.object,
};

export default TruncatedText;
