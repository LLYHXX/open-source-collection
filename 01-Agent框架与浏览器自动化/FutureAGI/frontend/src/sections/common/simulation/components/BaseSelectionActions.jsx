import { Box, Button, Chip } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";
import SvgColor from "src/components/svg-color";

/**
 * Base selection actions component for execution grids
 * Displays selected count with Run Evals and Cancel actions
 *
 * @param {Object} props
 * @param {number} props.selectedCount - Number of selected items
 * @param {Function} props.onRunEvals - Callback when "Run Evals" is clicked
 * @param {Function} props.onDelete - Callback when "Delete" is clicked
 * @param {Function} props.onClearSelection - Callback when "Cancel" is clicked
 */
const BaseSelectionActions = ({
  selectedCount,
  onRunEvals,
  onDelete,
  onClearSelection,
}) => {
  if (selectedCount === 0) return null;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,
      }}
    >
      <Chip
        label={`${selectedCount} selected`}
        size="small"
        sx={{
          height: 28,
          fontSize: "0.8rem",
          color: "purple.500",
          borderColor: "purple.500",
          backgroundColor: "purple.o5",

          ":hover": {
            backgroundColor: "purple.o5",
          },
        }}
      />
      <Button
        size="small"
        variant="outlined"
        startIcon={<Iconify icon="mdi:play" width={16} />}
        onClick={onRunEvals}
        sx={{
          py: 0.75,
          fontSize: "0.8rem",
          whiteSpace: "nowrap",
          color: "primary.main",
          borderColor: "primary.main",
          "&:hover": {
            borderColor: "primary.main",
            backgroundColor: "action.hover",
          },
        }}
      >
        Run Evals
      </Button>
      <Button
        size="small"
        variant="outlined"
        startIcon={
          <SvgColor
            // @ts-ignore
            sx={{ height: 2, width: 2, mt: -0.5 }}
            src={"/assets/icons/ic_delete.svg"}
          />
        }
        onClick={onDelete}
        sx={{
          py: 0.75,
          fontSize: "0.8rem",
          whiteSpace: "nowrap",
          "&:hover": {
            borderColor: "purple.600",
            backgroundColor: "purple.o5",
          },
        }}
      >
        Delete
      </Button>
      <Button
        size="small"
        variant="text"
        onClick={onClearSelection}
        sx={{
          py: 0.75,
          fontSize: "0.8rem",
          color: "text.secondary",
          "&:hover": {
            backgroundColor: "action.hover",
          },
        }}
      >
        Cancel
      </Button>
    </Box>
  );
};

BaseSelectionActions.propTypes = {
  selectedCount: PropTypes.number.isRequired,
  onRunEvals: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onClearSelection: PropTypes.func.isRequired,
};

export default BaseSelectionActions;
