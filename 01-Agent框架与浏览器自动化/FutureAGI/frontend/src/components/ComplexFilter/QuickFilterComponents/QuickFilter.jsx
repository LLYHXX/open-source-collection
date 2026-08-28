import { Box } from "@mui/material";
import React from "react";
import SvgColor from "../../svg-color";
import PropTypes from "prop-types";
import CellActionToolTip from "src/components/CellActionToolTip/CellActionToolTip";

const FilterButtonContent = ({ onClick }) => {
  return (
    <Box
      onClick={onClick}
      sx={{
        boxSizing: "border-box",
        flexShrink: 0,
        width: "24px",
        minWidth: "24px",
        maxWidth: "24px",
        height: "24px",
        minHeight: "24px",
        maxHeight: "24px",
        p: 0,
        m: 0,
        bgcolor: "background.paper",
        borderRadius: "6px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        cursor: "pointer",
        boxShadow: (theme) =>
          theme.palette.mode === "dark"
            ? "0 0 0 1px rgba(255,255,255,0.08)"
            : "0 1px 2px rgba(0,0,0,0.08)",
        "&:hover": {
          bgcolor: "action.hover",
        },
      }}
    >
      <SvgColor
        src={`/assets/icons/components/ic_filter.svg`}
        sx={{ color: "text.primary", width: "12px", height: "12px" }}
      />
    </Box>
  );
};

FilterButtonContent.propTypes = {
  onClick: PropTypes.func,
};

const QuickFilter = ({ onClick, children, show = true }) => {
  if (!show) return <>{children}</>;

  return (
    <CellActionToolTip
      title={<FilterButtonContent onClick={onClick} />}
      placement="top-end"
      slotProps={{
        popper: {
          modifiers: [
            {
              name: "offset",
              options: {
                offset: [10, -50],
              },
            },
          ],
        },
      }}
    >
      {children}
    </CellActionToolTip>
  );
};

QuickFilter.propTypes = {
  onClick: PropTypes.func,
  children: PropTypes.node,
  show: PropTypes.bool,
};

export default QuickFilter;
