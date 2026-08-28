import React from "react";
import { Helmet } from "react-helmet-async";
import { Box, Typography } from "@mui/material";
import IntegrationsList from "src/sections/settings/integrations/IntegrationsList";

export default function WorkspaceIntegrations() {
  return (
    <>
      <Helmet>
        <title>Workspace Integrations</title>
      </Helmet>
      <Box sx={{ px: "2px" }}>
        <Typography
          sx={{
            typography: "m2",
            fontWeight: "fontWeightSemiBold",
            color: "text.primary",
          }}
        >
          Integrations
        </Typography>
        <Typography
          sx={{
            typography: "s1",
            fontWeight: "fontWeightRegular",
            color: "text.secondary",
            mt: 0.5,
            mb: 3,
          }}
        >
          Manage workspace integrations
        </Typography>
        <IntegrationsList />
      </Box>
    </>
  );
}
