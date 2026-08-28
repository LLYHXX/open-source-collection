import { Box, Stack, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";
import { callStatusCellStyle } from "../constants";
import _ from "lodash";
export const CallLogsStatus = ({ value }) => {
  const theme = useTheme();
  if (!value) return "-";

  const statusKey = _.toLower(value);
  const statusConfig = callStatusCellStyle[statusKey];

  if (!statusConfig) return value; // fallback if status not mapped

  return (
    <Box
      sx={{
        height: "100%",
        display: "flex",
        alignItems: "center",
      }}
    >
      <Stack
        sx={{
          ...statusConfig.sx,
          padding: theme.spacing(0.5, 1.5),
          display: "flex",
          flexDirection: "row",
          justifyContent: "flex-start",
          alignItems: "center",
          height: "max-content",
          borderRadius: theme.spacing(0.5),
        }}
        gap={1}
      >
        <SvgColor src={statusConfig.icon} sx={{ height: 16, width: 16 }} />
        <Typography typography="s3" fontWeight="fontWeightMedium">
          {_.capitalize(value.replace(/-/g, " "))}
        </Typography>
      </Stack>
    </Box>
  );
};

CallLogsStatus.propTypes = {
  value: PropTypes.string,
};
