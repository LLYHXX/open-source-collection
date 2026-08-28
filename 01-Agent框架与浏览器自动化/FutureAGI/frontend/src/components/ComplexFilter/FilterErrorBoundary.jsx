import React from "react";
import { Box, Typography, Button } from "@mui/material";
import PropTypes from "prop-types";
import logger from "src/utils/logger";

class FilterErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    logger.error("Filter error caught by boundary:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        <Box
          sx={{
            border: "1px solid",
            borderColor: "error.main",
            borderRadius: "8px",
            padding: 2,
            backgroundColor: "error.light",
            display: "flex",
            flexDirection: "column",
            gap: 2,
            alignItems: "center",
          }}
        >
          <Typography variant="h6" color="error.main">
            Filter Error
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Something went wrong with the filter component. Please try
            refreshing the page or contact support if the issue persists.
          </Typography>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => {
              this.setState({ hasError: false, error: null, errorInfo: null });
              // Optionally refresh the page or reset filters
              if (this.props.onError) {
                this.props.onError();
              }
            }}
            sx={{ mt: 1 }}
          >
            Reset Filters
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

FilterErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  onError: PropTypes.func,
};

export default FilterErrorBoundary;
