import React from "react";
import CardWrapper from "./CardWrapper";
import PropTypes from "prop-types";
import { Box, Grid, Stack, Typography } from "@mui/material";
import {
  getIcon,
  getIconColor,
  getLabel,
  getSubtext,
  getSuffix,
  getTooltipMessage,
} from "./common";
import SvgColor from "../../../components/svg-color/svg-color";
import CustomTooltip from "src/components/tooltip";

const renderLabelWithIcon = (label = "", tooltipMessage) => {
  const words = label?.split(" ");
  const lastWord = words?.pop();
  const rest = words?.join(" ");

  return (
    <Typography
      color="text.primary"
      typography="s3"
      fontWeight="fontWeightMedium"
      sx={{
        wordBreak: "break-word",
        display: "inline",
      }}
    >
      {rest}{" "}
      <span
        style={{
          whiteSpace: "nowrap",
          display: "inline-flex",
          alignItems: "center",
        }}
      >
        {lastWord}
        {tooltipMessage && (
          <CustomTooltip size="small" show title={tooltipMessage}>
            <SvgColor
              sx={{
                height: "12px",
                width: "12px",
                cursor: "pointer",
                ml: 0.25,
                flexShrink: 0,
              }}
              src="/assets/icons/ic_info.svg"
            />
          </CustomTooltip>
        )}
      </span>
    </Typography>
  );
};

function SystemMetricCard({ keyName, value }) {
  const subtext = getSubtext(keyName);
  const tooltipMessage = getTooltipMessage(keyName);
  return (
    <Stack direction={"row"} gap={1.5}>
      <Box
        sx={{
          height: "32px",
          width: "32px",
          bgcolor: "background.neutral",
          borderRadius: 0.5,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <SvgColor
          sx={{
            height: "16px",
            width: "16px",
            bgcolor: getIconColor(keyName),
          }}
          src={getIcon(keyName)}
        />
      </Box>
      <Stack direction={"column"} gap={0.5} justifyContent={"flex-start"}>
        {renderLabelWithIcon(getLabel(keyName), tooltipMessage)}

        <Typography
          color={"text.primary"}
          typography={"l3"}
          fontWeight={"fontWeightRegular"}
        >
          {`${value}${getSuffix(keyName)}`}
        </Typography>
        {subtext && (
          <Typography
            sx={{
              typography: "s2",
              fontWeight: "fontWeightRegular",
              color: "text.primary",
            }}
          >
            {subtext}
          </Typography>
        )}
      </Stack>
    </Stack>
  );
}

SystemMetricCard.propTypes = {
  keyName: PropTypes.string,
  value: PropTypes.string,
};

export default function SystemMetrics({ data, expanded }) {
  const keysLength = Object.keys(data)?.length;
  return (
    <CardWrapper expanded={expanded} title={`System Metrics (${keysLength})`}>
      <Grid
        container
        spacing={2}
        sx={{
          my: 1.375,
        }}
      >
        {Object.entries(data)?.map(([key, value]) => (
          <Grid key={key} item xs={6}>
            <SystemMetricCard value={value} keyName={key} />
          </Grid>
        ))}
      </Grid>
    </CardWrapper>
  );
}

SystemMetrics.propTypes = {
  data: PropTypes.object.isRequired,
  expanded: PropTypes.bool,
};
