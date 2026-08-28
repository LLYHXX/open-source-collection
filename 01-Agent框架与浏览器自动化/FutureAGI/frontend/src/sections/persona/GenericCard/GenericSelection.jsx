import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { ShowComponent } from "src/components/show";
import SvgColor from "src/components/svg-color";

const GenericSelection = ({ selected, onToggleSelect }) => {
  return (
    <Box
      sx={{
        width: "18px",
        height: "18px",
        borderRadius: "50%",
        border: "1.5px solid",
        borderColor: selected ? "primary.main" : "divider",
        backgroundColor: selected ? "primary.main" : "transparent",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all 0.2s ease",
      }}
      onClick={(e) => {
        e.stopPropagation();
        onToggleSelect(!selected);
      }}
    >
      <ShowComponent condition={selected}>
        <SvgColor
          src="/assets/icons/ic_check.svg"
          sx={{ width: "15px", height: "15px", color: "common.white" }}
        />
      </ShowComponent>
    </Box>
  );
};

GenericSelection.propTypes = {
  selected: PropTypes.bool,
  onToggleSelect: PropTypes.func,
};

export default GenericSelection;
