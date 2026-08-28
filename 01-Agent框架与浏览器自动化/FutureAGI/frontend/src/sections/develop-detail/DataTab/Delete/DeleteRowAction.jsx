import React from "react";
import { Box, DialogContent } from "@mui/material";
import { styled } from "@mui/system";
import PropTypes from "prop-types";
import HelperText from "../../Common/HelperText";

const StyledBox = styled(Box)(() => ({
  gap: 2,
  display: "flex",
  alignItems: "center",
  py: 1,
}));

const DeleteRowAction = ({ selectedCount }) => {
  return (
    <DialogContent sx={{ padding: 0, margin: "2px 0 0" }}>
      <StyledBox>
        <HelperText
          text={`Are you sure you want to delete the selected ${selectedCount} row${selectedCount > 1 ? "s" : ""}?`}
        />
      </StyledBox>
    </DialogContent>
  );
};

DeleteRowAction.propTypes = {
  selectedCount: PropTypes.number,
};

export default DeleteRowAction;
