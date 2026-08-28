import { Box } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const ShortString = ({ children, maxLength = 30, ...options }) => {
  const getText = () => {
    if (typeof children !== "string" && typeof children !== "number")
      return "-";
    if (children.length > maxLength) {
      return (
        <>
          {children.slice(0, maxLength)}
          {"..."}
        </>
      );
    }

    return children;
  };

  return <Box {...options}>{getText()}</Box>;
};

ShortString.propTypes = {
  children: PropTypes.node,
  maxLength: PropTypes.number,
};

export default ShortString;
