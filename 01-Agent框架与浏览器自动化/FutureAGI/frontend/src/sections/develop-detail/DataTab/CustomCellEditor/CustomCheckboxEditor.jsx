import { Box, Checkbox } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect } from "react";

const CustomCheckboxEditor = (props) => {
  const { value, onValueChange } = props;
  const handleChange = (event) => {
    event.stopPropagation();
    event.preventDefault();
    onValueChange(event.target.checked);
    props.stopEditing();
  };

  useEffect(() => {
    const handleEscape = () => {
      props.stopEditing();
    };
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);
  return (
    <Box
      sx={{
        height: "100%",
        lineHeight: "1.5",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <Box>
        <Checkbox
          checked={value === "true" || value === "Passed" || value === true}
          onChange={handleChange}
        />
      </Box>
    </Box>
  );
};

CustomCheckboxEditor.propTypes = {
  value: PropTypes.bool,
  onValueChange: PropTypes.func,
  stopEditing: PropTypes.func,
};

export default CustomCheckboxEditor;
