import React from "react";
import CellActionToolTip from "../CellActionToolTip/CellActionToolTip";
import PropTypes from "prop-types";
import { Box } from "@mui/material";

const RunButtonContent = ({ onClick, component }) => {
  return (
    <Box
      onClick={onClick}
      sx={{
        padding: "8px",
      }}
    >
      {component}
    </Box>
  );
};

RunButtonContent.propTypes = {
  onClick: PropTypes.func,
  component: PropTypes.node,
};

const CellRunButton = ({ onClick, component, children, show = true }) => {
  if (!show) return <>{children}</>;

  return (
    <CellActionToolTip
      title={<RunButtonContent onClick={onClick} component={component} />}
      placement="right"
    >
      {children}
    </CellActionToolTip>
  );
};

export default CellRunButton;

CellRunButton.propTypes = {
  onClick: PropTypes.func,
  component: PropTypes.node,
  children: PropTypes.node,
  show: PropTypes.bool,
};
