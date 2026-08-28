import { IconButton } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import { styled } from "@mui/system";

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  width: 36,
  height: 36,
  border: "1px solid var(--border-default)",
  borderRadius: "8px",
  backgroundColor: theme.palette.background.neutral,
  color: theme.palette.text.secondary,
  "&:hover": {
    backgroundColor: theme.palette.background.neutral,
    borderColor: theme.palette.divider,
  },
}));

const ActionButtons = ({ icon, ...rest }) => {
  return (
    <StyledIconButton {...rest} disableTouchRipple disableFocusRipple>
      {icon}
    </StyledIconButton>
  );
};

ActionButtons.propTypes = {
  icon: PropTypes.string,
};

export default ActionButtons;
