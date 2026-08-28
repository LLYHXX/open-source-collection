import React from "react";
import { Box, Typography } from "@mui/material";
import SvgColor from "../svg-color";
import PropTypes from "prop-types";
import { useAuthContext } from "src/auth/hooks";
import { ROLES } from "src/utils/rolePermissionMapping";

const AddRowStatusPanel = ({ handleAddRow, disabled }) => {
  const { role } = useAuthContext();
  const isViewerRole = role === ROLES.VIEWER || role === ROLES.WORKSPACE_VIEWER;
  const isDisabled = disabled || isViewerRole;
  return (
    <Box
      sx={{
        paddingX: 2,
        paddingY: "4px",
        backgroundColor: (theme) => theme.palette.background.neutral,

        width: "100%",
        flex: 1,
        display: "flex",
        alignItems: "center",
        gap: "4px",
        cursor: isDisabled ? "default" : "pointer",
        opacity: isDisabled ? 0.5 : 1,
        pointerEvents: isDisabled ? "none" : "auto",
      }}
      onClick={() => !isDisabled && handleAddRow()}
    >
      <SvgColor
        src="/assets/icons/components/ic_add.svg"
        sx={{ width: "16px", height: "16px", color: "text.disabled" }}
      />
      <Typography typography="s2" fontWeight="fontWeightMedium">
        Add row
      </Typography>
    </Box>
  );
};

AddRowStatusPanel.propTypes = {
  handleAddRow: PropTypes.func,
  disabled: PropTypes.bool,
};

export default AddRowStatusPanel;
