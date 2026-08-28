import React from "react";
import {
  Box,
  Grid,
  Stack,
  Typography,
  useTheme,
  Skeleton,
} from "@mui/material";
import PropTypes from "prop-types";
import SvgColor from "../../../components/svg-color/svg-color";
import { ICON_MAPPER, ICON_STYLES } from "./common";
import { ShowComponent } from "../../../components/show/ShowComponent";

function MetricCard({
  id,
  title,
  value,
  subtitle,
  percentageChange,
  changeLabel,
  changeType,
  isLoading = false,
}) {
  const theme = useTheme();

  if (isLoading) {
    return (
      <Box
        sx={{
          padding: 1,
          paddingBottom: 2.5,
          borderRadius: 0.5,
          border: "1px solid",
          borderColor: "divider",
          display: "flex",
          flexDirection: "column",
          gap: 0.5,
        }}
      >
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="flex-start"
        >
          <Skeleton variant="text" width={80} height={24} />
          <Skeleton variant="circular" width={30} height={31} />
        </Stack>
        <Skeleton variant="text" width="60%" height={32} />
        <Skeleton variant="text" width="40%" height={24} />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        padding: 1,
        paddingBottom: 2.5,
        borderRadius: 0.5,
        border: "1px solid",
        borderColor: "divider",
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
        minHeight: "130px",
      }}
    >
      <Stack
        direction={"row"}
        justifyContent={"space-between"}
        alignItems={"flex-start"}
      >
        <Typography
          color={"text.primary"}
          typography={"s1"}
          fontWeight={"fontWeightRegular"}
        >
          {title}
        </Typography>
        <Box
          sx={{
            height: "31px",
            width: "30px",
            borderRadius: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            ...ICON_STYLES?.[id]?.containerStyle,
          }}
        >
          <SvgColor
            src={ICON_MAPPER?.[id]}
            sx={{
              ...ICON_STYLES?.[id]?.iconStyle,
            }}
          />
        </Box>
      </Stack>
      <Typography
        color={"text.primary"}
        typography={"m1"}
        fontWeight={"fontWeightSemiBold"}
      >
        {value}{" "}
        <Typography
          color={"text.primary"}
          typography={"s2"}
          fontWeight={"fontWeightRegular"}
          component={"span"}
        >
          {subtitle}
        </Typography>
      </Typography>
      <ShowComponent condition={percentageChange !== null}>
        <Typography>
          <Typography
            sx={{
              bgcolor: changeType === "positive" ? "green.o5" : "red.o5",
              padding: theme.spacing(0.25, 1),
              mr: 1,
              borderRadius: 0.5,
              color: changeType === "positive" ? "green.500" : "red.500",
            }}
            typography={"s3"}
            fontWeight={"fontWeightMedium"}
            component={"span"}
          >
            {percentageChange}
          </Typography>
          <Typography
            typography={"s3"}
            fontWeight={"fontWeightRegular"}
            component={"span"}
            color={"text.primary"}
          >
            {changeLabel}
          </Typography>
        </Typography>
      </ShowComponent>
    </Box>
  );
}

MetricCard.propTypes = {
  id: PropTypes.string,
  title: PropTypes.string,
  value: PropTypes.string,
  subtitle: PropTypes.string,
  percentageChange: PropTypes.string,
  changeLabel: PropTypes.string,
  changeType: PropTypes.string,
  isLoading: PropTypes.bool,
};

export default function Metrics({ metrics = [], isLoading = false }) {
  return (
    <Grid container spacing={1}>
      {isLoading
        ? Array.from({ length: 5 }).map((_, index) => (
            <Grid item key={index} xs={12} sm={6} md={6} lg={3} xl={3}>
              <MetricCard isLoading />
            </Grid>
          ))
        : metrics?.map((metric) => (
            <Grid item key={metric?.id} xs={12} sm={6} md={6} lg={3} xl={3}>
              <MetricCard {...metric} />
            </Grid>
          ))}
    </Grid>
  );
}

Metrics.propTypes = {
  metrics: PropTypes.array,
  isLoading: PropTypes.bool,
};
