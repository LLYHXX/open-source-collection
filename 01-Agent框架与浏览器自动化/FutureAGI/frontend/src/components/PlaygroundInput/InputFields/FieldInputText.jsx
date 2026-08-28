import { Box, TextField } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const FieldInputText = ({ value, onChange, ...rest }) => {
  return (
    <Box>
      <TextField
        {...rest}
        value={value}
        onChange={onChange}
        variant="standard"
        multiline
        rows={3}
        InputProps={{ disableUnderline: true }}
        sx={{
          width: "100%",
          flexGrow: 1,
          fontSize: "16px",
          "& .MuiInputBase-input": {
            padding: "0px",
            border: "1px solid",
            // borderColor: "divider",
            borderColor: "transparent",
          },
        }}
      />
    </Box>
  );
};

FieldInputText.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
};

export default FieldInputText;
