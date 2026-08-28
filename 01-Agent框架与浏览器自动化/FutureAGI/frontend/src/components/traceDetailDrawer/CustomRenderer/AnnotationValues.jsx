import { Box, Chip, useTheme } from "@mui/material";
import React from "react";
import Iconify from "../../iconify";
import PropTypes from "prop-types";
import { ShowComponent } from "src/components/show";

const AnnotationValues = ({ value, annotationType, maxChips, settings }) => {
  const theme = useTheme();

  const renderCategorical = () => {
    const categoricalValues = value || [];

    if (maxChips === undefined) {
      return categoricalValues?.map((v) => (
        <Chip
          key={v}
          label={v}
          size="small"
          color="primary"
          sx={{
            backgroundColor: theme.palette.action.hover,
            color: theme.palette.primary.main,
            fontWeight: 400,
          }}
        />
      ));
    }

    const chips = [];

    categoricalValues?.slice(0, maxChips)?.forEach((v) => {
      chips.push(
        <Chip
          key={v}
          label={v}
          size="small"
          color="primary"
          sx={{
            backgroundColor: theme.palette.action.hover,
            color: theme.palette.primary.main,
            fontWeight: 400,
          }}
        />,
      );
    });

    if (categoricalValues?.length > maxChips) {
      chips.push(
        <Chip
          label={`+${categoricalValues?.length - maxChips}`}
          size="small"
          color="primary"
          sx={{
            backgroundColor: theme.palette.action.hover,
            color: theme.palette.primary.main,
            fontWeight: 400,
          }}
        />,
      );
    }

    return chips;
  };

  if (!value || value === "") {
    return <Box>-</Box>;
  }

  if (annotationType === "number" || annotationType === "text") {
    return <Box>{value}</Box>;
  }

  if (annotationType === "thumbs_up_down") {
    return (
      <Box
        sx={{ display: "flex", alignItems: "center", gap: 1, height: "100%" }}
      >
        <Iconify
          icon="octicon:thumbsup-24"
          color={value === "up" ? "green.500" : "divider"}
        />
        <Iconify
          icon="octicon:thumbsdown-24"
          color={value === "down" ? "red.500" : "divider"}
        />
      </Box>
    );
  }

  if (annotationType === "star") {
    return (
      <Box
        sx={{ display: "flex", alignItems: "center", gap: 1, height: "100%" }}
      >
        {Array.from({ length: parseInt(value) }).map((_, index) => (
          <Iconify
            key={index}
            icon="material-symbols:star"
            sx={{ fontSize: "inherit", flexShrink: 0 }}
            width={25}
            color="orange.300"
          />
        ))}
        <ShowComponent condition={settings?.noOfStars !== undefined}>
          {Array.from({
            length: parseInt(settings?.noOfStars) - parseInt(value),
          }).map((_, index) => (
            <Iconify
              key={index}
              icon="material-symbols:star-outline"
              width={25}
              sx={{
                fontSize: "inherit",
                color: "text.secondary",
                flexShrink: 0,
              }}
            />
          ))}
        </ShowComponent>
      </Box>
    );
  }

  if (annotationType === "categorical") {
    return (
      <Box
        sx={{ display: "flex", gap: 1, height: "100%", alignItems: "center" }}
      >
        {renderCategorical()}
      </Box>
    );
  }

  return <Box>{value}</Box>;
};

AnnotationValues.propTypes = {
  value: PropTypes.string,
  annotationType: PropTypes.string,
  maxChips: PropTypes.any,
  settings: PropTypes.object,
};

export default AnnotationValues;
