import React from "react";
import { Box, Button, Tooltip, Typography } from "@mui/material";
import { Helmet } from "react-helmet-async";
import Iconify from "src/components/iconify";
import PersonaListView from "src/sections/persona/PersonaListView";

const Personas = () => {
  return (
    <>
      <Helmet>
        <title>Personas</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: "background.paper",
          height: "100%",
          p: 2,
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Typography variant="h6" fontWeight={600}>
              Personas
            </Typography>
            <Tooltip
              title="Create and manage personas — activate or deactivate them to control scenario generation for your voice and chat simulations."
              arrow
              placement="right"
            >
              <Box sx={{ display: "flex", cursor: "help" }}>
                <Iconify
                  icon="solar:info-circle-line-duotone"
                  width={16}
                  sx={{ color: "text.disabled" }}
                />
              </Box>
            </Tooltip>
          </Box>
          <Button
            size="small"
            variant="outlined"
            component="a"
            href="https://docs.futureagi.com/docs/simulation/concepts/personas"
            target="_blank"
            rel="noopener noreferrer"
            startIcon={<Iconify icon="solar:document-text-linear" width={16} />}
            sx={{
              textTransform: "none",
              fontSize: "13px",
              height: "32px",
              borderColor: "divider",
              color: "text.secondary",
            }}
          >
            View Docs
          </Button>
        </Box>
        <PersonaListView />
      </Box>
    </>
  );
};

export default Personas;
