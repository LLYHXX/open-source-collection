import { Box } from "@mui/material";
import React from "react";
import SvgColor from "src/components/svg-color";
import PropTypes from "prop-types";

const AddNode = ({ id }) => {
  const className = `add-node-border-${id}`;
  return (
    <>
      <Box
        sx={{
          position: "absolute",
          bottom: "-72px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "30px",
          height: "30px",
          backgroundColor: "primary.main",
          borderRadius: "50%",
          opacity: 0,
          transition: "opacity 0.1s ease-in-out",
          "&:hover": {
            opacity: 1,
          },
          [`&:hover + .${className}`]: {
            opacity: 1,
          },
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
        }}
        className={`add-node-${id}`}
      >
        <SvgColor
          src="/assets/icons/components/ic_add.svg"
          sx={{ width: "16px", height: "16px", color: "common.white" }}
        />
      </Box>
      <Box
        sx={{
          borderRight: "2px solid",
          borderColor: "primary.main",
          height: "42px",
          position: "absolute",
          left: "50%",
          transform: "translateX(-50%)",
          bottom: "-42px",
          opacity: 0,
        }}
        className={className}
      />
    </>
  );
};

AddNode.propTypes = {
  id: PropTypes.string,
};

export default AddNode;
