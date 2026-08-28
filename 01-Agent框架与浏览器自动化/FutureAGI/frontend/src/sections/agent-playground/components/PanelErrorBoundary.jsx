import React from "react";
import { Box, Typography, Button } from "@mui/material";
import PropTypes from "prop-types";
import logger from "src/utils/logger";

/**
 * Error boundary for agent playground panels (output detail, node forms, etc.).
 * Catches rendering errors in children and shows a fallback UI with a retry button
 * instead of crashing the entire builder.
 */
class PanelErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    const source = this.props.name || "PanelErrorBoundary";
    logger.error(`[${source}] Rendering error caught`, error, errorInfo);
  }

  handleRetry = () => {
    // Let the parent clean up any state that may have caused the crash
    // (e.g. deselect a broken node, clear bad execution data).
    // If no onRetry is provided, we still reset and attempt a re-render.
    this.props.onRetry?.();
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 1.5,
            p: 3,
            height: "100%",
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Something went wrong while rendering this panel.
          </Typography>
          <Button variant="outlined" size="small" onClick={this.handleRetry}>
            Retry
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

PanelErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  /** Identifier used in error logs to pinpoint which panel crashed */
  name: PropTypes.string,
  /** Called before resetting the boundary — use to clean up parent state that caused the crash */
  onRetry: PropTypes.func,
};

export default PanelErrorBoundary;
