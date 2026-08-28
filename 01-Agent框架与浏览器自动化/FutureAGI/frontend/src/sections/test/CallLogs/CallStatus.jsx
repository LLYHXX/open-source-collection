import { Chip } from "@mui/material";
import React from "react";
import { palette } from "src/theme/palette";
import PropTypes from "prop-types";
import _ from "lodash";
import SvgColor from "src/components/svg-color";

const statusStyles = {
  completed: {
    backgroundColor: palette("light").green["o10"],
    color: palette("light").green["700"],
    icon: "/assets/icons/agent/call_completed.svg",
  },
  failed: {
    backgroundColor: palette("light").red["o10"],
    color: palette("light").red["700"],
    icon: "/assets/icons/ic_failed.svg",
  },
  pending: {
    backgroundColor: (theme) =>
      theme.palette.mode === "dark"
        ? palette("light").orange["o10"]
        : palette("light").orange["50"],
    color: (theme) =>
      theme.palette.mode === "dark"
        ? palette("light").orange["400"]
        : palette("light").orange["700"],
    icon: "/assets/icons/ic_call_pending.svg",
  },
  registered: {
    backgroundColor: palette("light").pink["o10"],
    color: palette("light").pink["700"],
    icon: "/assets/icons/ic_call_registered.svg",
  },
  ongoing: {
    backgroundColor: palette("light").blue["o10"],
    color: palette("light").blue["700"],
    icon: "/assets/icons/ic_call_ongoing.svg",
  },
  cancelled: {
    backgroundColor: palette("light").red["o10"],
    color: palette("light").red["700"],
    icon: "/assets/icons/ic_call_cancelled.svg",
  },
  evaluating: {
    backgroundColor: palette("light").green["o10"],
    color: palette("light").green["700"],
    icon: "/assets/icons/agent/call_completed.svg",
  },
  running: {
    backgroundColor: palette("light").blue["o10"],
    color: palette("light").blue["700"],
    icon: "/assets/icons/ic_call_running.svg",
  },
  "in-progress": {
    backgroundColor: palette("light").orange["o10"],
    color: palette("light").orange["700"],
    icon: "/assets/icons/navbar/ic_new_clock.svg",
  },
  analyzing: {
    backgroundColor: palette("light").blue["o10"],
    color: palette("light").blue["700"],
    icon: "/assets/icons/app/ic_search.svg",
  },
  queued: {
    backgroundColor: palette("light").pink["o10"],
    color: palette("light").pink["700"],
    icon: "/assets/icons/ic_call_queued.svg",
  },

  default: {
    backgroundColor: palette("light").black["o5"],
    color: palette("light").black["800"],
    icon: "/assets/icons/ic_call_pending.svg",
  },
};

const CallStatus = ({ value }) => {
  const key = value?.toLowerCase();

  const style = statusStyles[key] ?? statusStyles.default;

  return (
    <Chip
      variant="medium"
      label={_.capitalize(value)}
      size="small"
      icon={<SvgColor sx={{ width: 16 }} src={style.icon} />}
      sx={{
        typography: "s1",
        fontWeight: "fontWeightMedium",
        ...style,
        borderRadius: 0.25,
        paddingX: 1,
        "& .MuiChip-icon": {
          color: style.color,
        },
      }}
    />
  );
};

CallStatus.propTypes = {
  value: PropTypes.string,
};

export default CallStatus;
