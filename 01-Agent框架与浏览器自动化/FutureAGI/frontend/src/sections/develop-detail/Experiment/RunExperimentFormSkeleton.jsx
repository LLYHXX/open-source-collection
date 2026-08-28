import React from "react";
import {
  Box,
  Stack,
  Skeleton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";

const RunExperimentFormSkeleton = () => {
  return (
    <Box
      sx={{
        gap: "20px",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
      }}
    >
      {/* Header Section */}
      <Box
        display="flex"
        flexDirection="row"
        alignItems="flex-start"
        justifyContent="space-between"
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.5,
          }}
        >
          <Skeleton variant="text" width={180} height={32} />
          <Skeleton variant="text" width={320} height={20} />
        </Box>
        <Stack direction="row" alignItems="center" gap={1.5}>
          <Skeleton variant="rounded" width={110} height={32} />
          <Skeleton variant="circular" width={32} height={32} />
        </Stack>
      </Box>

      {/* Form Content */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          gap: 2,
          pt: 1,
          flexDirection: "column",
        }}
      >
        {/* Name Field */}
        <Box>
          <Skeleton variant="text" width={60} height={20} sx={{ mb: 0.5 }} />
          <Skeleton variant="rounded" width="100%" height={40} />
        </Box>

        {/* Select Baseline Column */}
        <Stack direction="column">
          <Box>
            <Skeleton variant="text" width={150} height={20} sx={{ mb: 0.5 }} />
            <Skeleton variant="rounded" width="100%" height={40} />
          </Box>
          <Skeleton variant="text" width={280} height={16} sx={{ mt: 0.5 }} />
        </Stack>

        {/* Prompt Template Section */}
        <Box>
          <Skeleton variant="text" width={120} height={24} sx={{ mb: 1 }} />
          <Box
            sx={{
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 1,
              p: 2,
            }}
          >
            <Stack gap={2}>
              <Skeleton variant="text" width={100} height={20} />
              <Skeleton variant="rounded" width="100%" height={120} />
              <Skeleton variant="rounded" width="100%" height={40} />
              <Skeleton variant="rounded" width="100%" height={40} />
            </Stack>
          </Box>
        </Box>

        {/* Add Another Prompt Button */}
        <Skeleton variant="rounded" width={180} height={36} />

        {/* Evaluation Accordion */}
        <Stack direction="column" gap={0.5}>
          <Accordion defaultExpanded>
            <AccordionSummary>
              <Skeleton variant="text" width={100} height={24} />
            </AccordionSummary>
            <AccordionDetails sx={{ padding: 2 }}>
              <Stack gap={2}>
                <Skeleton variant="rounded" width="100%" height={60} />
                <Skeleton variant="rounded" width="100%" height={60} />
              </Stack>
            </AccordionDetails>
          </Accordion>
        </Stack>
      </Box>

      {/* Action Buttons */}
      <Box
        sx={{
          display: "flex",
          gap: 2,
          width: "100%",
          paddingTop: 2,
          position: "sticky",
          bottom: 0,
          backgroundColor: "background.paper",
          zIndex: 10,
        }}
      >
        <Skeleton variant="rounded" width="50%" height={40} />
        <Skeleton variant="rounded" width="50%" height={40} />
      </Box>
    </Box>
  );
};

export default RunExperimentFormSkeleton;
