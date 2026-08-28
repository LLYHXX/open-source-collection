import React from "react";
import CardWrapper from "./CardWrapper";
import PropTypes from "prop-types";
import { Box, Stack, Typography } from "@mui/material";
import {
  getChatOverrides,
  getIcon,
  getIconColor,
  getLabel,
  getSuffix,
} from "./common";
import SvgColor from "../../../components/svg-color/svg-color";
import { AGENT_TYPES } from "src/sections/agents/constants";

const getMetricConfig = (key, agentType) => {
  if (agentType === AGENT_TYPES.CHAT && getChatOverrides[key]) {
    return getChatOverrides[key];
  }

  return {
    label: getLabel(key),
    icon: getIcon(key),
    iconColor: getIconColor(key),
    suffix: getSuffix(key),
  };
};

function CallCard({
  keyName: _keyName,
  value,
  onClick,
  label,
  icon,
  iconColor,
  suffix,
}) {
  return (
    <Box
      onClick={onClick}
      sx={{
        display: "flex",
        flexDirection: "row",
        gap: 1,
        alignItems: "center",
        cursor: onClick ? "pointer" : "default",
      }}
    >
      <Box
        sx={{
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 0.8,
          width: "63px",
          height: "32px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 1,
          flexShrink: 0,
        }}
      >
        {onClick && (
          <SvgColor
            sx={{
              height: "16px",
              width: "16px",
              bgcolor: iconColor,
            }}
            src={icon}
          />
        )}
        <Typography
          sx={{
            fontFamily: "Inter",
            fontSize: "16px",
            lineHeight: "32px",
            color: "text.primary",
          }}
        >
          {value}
          {suffix}
        </Typography>
      </Box>
      <Typography
        typography="s1"
        color="text.primary"
        fontWeight="fontWeightMedium"
      >
        {label}
      </Typography>
    </Box>
  );
}

CallCard.propTypes = {
  keyName: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  label: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  iconColor: PropTypes.string.isRequired,
  suffix: PropTypes.string.isRequired,
};

const CallDetails = ({ data, expanded, handleSetFilter, agentType }) => {
  const cardTitle =
    agentType === AGENT_TYPES.CHAT ? "Chat Details" : "Call Details";

  const handleCardClick = (key) => {
    if (key === "calls_connected_percentage") return;
    handleSetFilter(key);
  };

  return (
    <CardWrapper expanded={expanded} title={cardTitle}>
      <Stack direction="column" gap={3} sx={{ my: 1.375 }}>
        {Object.entries(data).map(([key, value]) => {
          const { label, icon, iconColor, suffix } = getMetricConfig(
            key,
            agentType,
          );
          return (
            <CallCard
              key={key}
              keyName={key}
              value={value}
              onClick={
                key === "calls_connected_percentage"
                  ? null
                  : () => handleCardClick(key)
              }
              label={label}
              icon={icon}
              iconColor={iconColor}
              suffix={suffix}
            />
          );
        })}
      </Stack>
    </CardWrapper>
  );
};

CallDetails.propTypes = {
  data: PropTypes.object.isRequired,
  expanded: PropTypes.bool,
  handleSetFilter: PropTypes.func.isRequired,
  agentType: PropTypes.string.isRequired,
};

export default CallDetails;
