import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { formatDuration } from "src/utils/format-time";
import { format } from "date-fns";
import { formatRole } from "src/sections/test/common";

const ColorMap = (role) => {
  switch (role) {
    case "system": {
      return {
        borderColor: "orange.200",
        backgroundColor: "orange.o10",
        headerColor: "orange.500",
        textColor: "orange.600",
      };
    }
    case "user": {
      return {
        borderColor: "green.100",
        backgroundColor: "blue.o10",
        headerColor: "green.500",
        textColor: "green.600",
      };
    }
    case "agent":
    case "bot": {
      return {
        borderColor: "blue.100",
        backgroundColor: "#E9C00C1A",
        headerColor: "blue.500",
        textColor: "blue.600",
      };
    }
    default: {
      return {
        borderColor: "background.default",
        backgroundColor: "background.default",
        headerColor: "text.disabled",
        textColor: "text.secondary",
      };
    }
  }
};

const TranscriptConversationCard = ({
  role,
  duration,
  content,
  align,
  timeStamp,
  agentName,
  simulatorName,
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        maxWidth: "80%",
        backgroundColor: ColorMap(role)?.backgroundColor,
        borderRadius: 0.5,
        padding: 1,
        flexDirection: "column",
        gap: 1,
        alignSelf: align,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          justifyContent: "space-between",
          width: "100%",
        }}
      >
        <Typography
          typography="s1"
          fontWeight="fontWeightMedium"
          sx={{ color: "text.primary" }}
        >
          {formatRole(role, agentName, simulatorName)}
        </Typography>
        <Typography typography="s2" color="text.disabled">
          {formatDuration(duration)}
        </Typography>
      </Box>
      <Box>
        <Typography typography="s2" color={"text.disabled"}>
          {content}
        </Typography>
      </Box>
      <Box>
        <Typography typography="s2" color="text.disabled">
          {format(new Date(timeStamp), "h:mm a 'on' MM/dd/yyyy")}
        </Typography>
      </Box>
    </Box>
  );
};

TranscriptConversationCard.propTypes = {
  role: PropTypes.string,
  duration: PropTypes.number,
  content: PropTypes.string,
  align: PropTypes.string,
  timeStamp: PropTypes.string,
  agentName: PropTypes.string,
  simulatorName: PropTypes.string,
};

export default TranscriptConversationCard;
