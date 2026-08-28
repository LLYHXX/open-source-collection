import React from "react";
import PropTypes from "prop-types";
import { Box, Alert, Button, Stack } from "@mui/material";
import Iconify from "src/components/iconify";

const PageErrorState = ({ message, onRetry }) => (
  <Box display="flex" justifyContent="center" alignItems="center" py={8} px={3}>
    <Stack
      spacing={2}
      alignItems="center"
      sx={{ maxWidth: 480, width: "100%" }}
    >
      <Alert severity="error" sx={{ width: "100%" }}>
        {message || "Something went wrong. Please try again."}
      </Alert>
      {onRetry && (
        <Button
          variant="outlined"
          startIcon={<Iconify icon="mdi:refresh" width={20} />}
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </Stack>
  </Box>
);

PageErrorState.propTypes = {
  message: PropTypes.string,
  onRetry: PropTypes.func,
};

export default PageErrorState;
