import React from "react";
import { Box, DialogContent, TextField } from "@mui/material";
import { styled } from "@mui/system";
import PropTypes from "prop-types";

const StyledBox = styled(Box)(() => ({
  gap: 2,
  display: "flex",
  alignItems: "center",
  padding: "16px 0 0",
  "& .MuiFormControl-root": {
    "& .MuiFormLabel-root": {
      "&.Mui-focused": {
        color: "text.secondary",
      },
    },
    "& .MuiInputBase-root": {
      "&.Mui-focused": {
        "& .MuiOutlinedInput-notchedOutline": {
          borderColor: "background.neutral",
        },
      },
    },
  },
}));

const DuplicateRowAction = ({ setNoOfCopies }) => {
  return (
    <DialogContent sx={{ padding: 0, margin: 0 }}>
      <StyledBox>
        <TextField
          InputLabelProps={{}}
          fullWidth
          label="No.of copies of each rows"
          id="outlined-start-adornment"
          type="number"
          size="small"
          onChange={(e) => setNoOfCopies(e.target.value)}
        />
      </StyledBox>
    </DialogContent>
  );
};

DuplicateRowAction.propTypes = {
  setNoOfCopies: PropTypes.func,
};

export default DuplicateRowAction;
