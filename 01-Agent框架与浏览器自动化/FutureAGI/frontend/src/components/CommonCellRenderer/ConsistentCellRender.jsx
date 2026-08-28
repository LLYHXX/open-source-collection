import React from "react";
import { Box, Chip, keyframes } from "@mui/material";
import PropTypes from "prop-types";
import { palette } from "src/theme/palette";
import SvgColor from "src/components/svg-color";

const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const customLabels = {
  NotStarted: "Not Started",
};

const formatChipLabel = (label) => customLabels[label] || label;

const statusStyles = {
  NotStarted: {
    backgroundColor: palette("light").black["o10"],
    color: palette("light").black["500"],
    borderColor: palette("light").black["o30"],
    icon: "/assets/icons/ic_call_pending.svg",
  },
  Queued: {
    backgroundColor: palette("light").orange["o10"],
    color: palette("light").orange["700"],
    borderColor: palette("light").orange["o30"],
    icon: "/assets/icons/ic_queued_header.svg",
  },
  Running: {
    backgroundColor: palette("light").blue["o10"],
    borderColor: palette("light").blue["o30"],
    color: palette("light").blue["800"],
    icon: "/assets/icons/ic_queued_header.svg",
  },
  Completed: {
    backgroundColor: palette("light").green["o10"],
    color: palette("light").green["500"],
    borderColor: palette("light").green["300"],
    icon: "/assets/icons/ic_completed.svg",
  },
  Cancelled: {
    backgroundColor: palette("light").red["o10"],
    color: palette("light").red["800"],
    borderColor: palette("light").red["o30"],
    icon: "/assets/icons/ic_close.svg",
  },

  Editing: {
    backgroundColor: palette("light").pink["o10"],
    color: palette("light").pink["500"],
    borderColor: palette("light").pink["o30"],
    icon: "/assets/icons/ic_edit_pencil.svg",
  },
  Inactive: {
    backgroundColor: palette("light").black["o10"],
    color: palette("light").black["500"],
    borderColor: palette("light").black["o30"],
    icon: "/assets/icons/ic_clock.svg",
  },
  Failed: {
    backgroundColor: palette("light").red["o10"],
    color: palette("light").red["800"],
    borderColor: palette("light").red["o30"],
    icon: "/assets/icons/ic_failed.svg",
  },
  default: {
    backgroundColor: palette("light").purple["o10"],
    color: palette("light").purple["700"],
    borderColor: palette("light").purple["o30"],
    icon: "/assets/icons/ic_clock.svg",
  },
};

const ConsistentCellRender = ({ value }) => {
  const style =
    statusStyles[value] ??
    statusStyles[value?.toLowerCase()] ??
    statusStyles.default;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
      }}
    >
      <Chip
        variant="soft"
        label={formatChipLabel(value)}
        size="medium"
        icon={
          style.icon ? (
            <SvgColor
              src={style.icon}
              sx={{
                height: "16px",
                width: "16px",
                ...(value === "Running" && {
                  animation: `${spin} 1s linear infinite`,
                  willChange: "transform",
                }),
              }}
            />
          ) : undefined
        }
        sx={{
          typography: "s2_1",
          height: "24px",
          border: "1px solid",
          borderRadius: 0,
          fontWeight: "fontWeightMedium",
          ...style,
          "&:hover": {
            backgroundColor: style.backgroundColor,
            borderColor: style.borderColor,
            color: style.color,
          },
          "& .MuiChip-icon": {
            color: style.color,
          },
        }}
      />
    </Box>
  );
};

ConsistentCellRender.propTypes = {
  value: PropTypes.string,
};

export default ConsistentCellRender;
