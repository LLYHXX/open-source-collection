import { Box, Chip, useTheme, alpha } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Iconify from "src/components/iconify";
import { ShowComponent } from "src/components/show";
import { OutputTypes } from "src/sections/common/DevelopCellRenderer/CellRenderers/cellRendererHelper";

const getColorByValues = (data, type, theme) => {
  const isDark = theme.palette.mode === "dark";
  const opacityBg = isDark ? 0.16 : 0.1;

  let colors = {
    backgroundColor: "",
    color: "",
  };

  if (type == "bool") {
    const isPass = data?.avgBoolPassScore;
    colors = {
      ...colors,
      color: isPass
        ? isDark
          ? theme.palette.green[400]
          : theme.palette.green[500]
        : isDark
          ? theme.palette.red[400]
          : theme.palette.red[500],
      backgroundColor: alpha(
        isPass ? theme.palette.green[500] : theme.palette.red[500],
        opacityBg,
      ),
    };
  } else if (type == "float") {
    if (
      (data.avgFloatScore >= 0 && data.avgFloatScore <= 49) ||
      !data.avgFloatScore
    ) {
      colors = {
        ...colors,
        color: isDark ? theme.palette.red[400] : theme.palette.red[500],
        backgroundColor: alpha(theme.palette.red[500], opacityBg),
      };
    } else if (data.avgFloatScore >= 50 && data.avgFloatScore <= 79) {
      colors = {
        ...colors,
        color: isDark ? theme.palette.orange[400] : theme.palette.orange[500],
        backgroundColor: alpha(theme.palette.orange[500], opacityBg),
      };
    } else if (data.avgFloatScore >= 80) {
      colors = {
        ...colors,
        color: isDark ? theme.palette.green[400] : theme.palette.green[500],
        backgroundColor: alpha(theme.palette.green[500], opacityBg),
      };
    }
  } else if (type === OutputTypes.NUMERIC) {
    colors = {
      color: "",
      backgroundColor: "",
    };
  } else {
    colors = {
      ...colors,
      color: theme.palette.primary.main,
      backgroundColor: theme.palette.action.hover,
    };
  }

  return colors;
};

const getChipLabel = (data, type) => {
  if (type === "bool") {
    if (data?.avgBoolPassScore) {
      return `Average Pass: ${data.avgBoolPassScore}%`;
    } else if (data?.avgBoolFailScore) {
      return `Average Fail: ${data.avgBoolFailScore}%`;
    } else {
      return "Average Pass: NA";
    }
  } else if (type === "float") {
    const score = parseFloat(data?.avgFloatScore);
    if (typeof score === "number" && !isNaN(score)) {
      return `Average Score: ${score === 0 ? "0" : Number(score.toFixed(2))}%`;
    } else {
      return "Average Score: NA";
    }
  } else if (type === OutputTypes.NUMERIC) {
    const numValue = Number(data?.avgFloatScore);
    const safeValue = isNaN(numValue)
      ? "-"
      : Number.isInteger(numValue)
        ? String(numValue)
        : numValue.toFixed(4);
    return `Average Score: ${safeValue}`;
  } else {
    return null;
  }
};

function evaluateResult(data, evalId) {
  const evalType = data?.evalType;
  const totalErrors = data?.totalErrorsCount || 0;

  const result = {
    ...data,
    evaluationId: evalId,
    errorType: "SUCCESS",
    errorTitle: "Evaluation Success",
  };

  if (evalType === "bool") {
    const hasPassScore = data.avgBoolPassScore !== null;
    const hasFailScore = data.avgBoolFailScore !== null;

    if ((hasPassScore || hasFailScore) && totalErrors > 0) {
      result.errorType = "PARTIAL";
      result.errorTitle = "Evaluation Failed Partially";
      result.showIcon = true;
    }
    if (!(hasPassScore || hasFailScore) && totalErrors === 0) {
      result.errorType = "ERROR";
      result.errorTitle = "Evaluation Failed";
      result.showIcon = true;
    }
    if (!(hasPassScore || hasFailScore) && totalErrors > 0) {
      result.errorType = "ERROR";
      result.errorTitle = "Evaluation Failed";
      result.showIcon = true;
    }
  } else if (evalType === "float") {
    const hasScore = data.avgFloatScore !== null;

    if (hasScore && totalErrors > 0) {
      result.errorType = "PARTIAL";
      result.errorTitle = "Evaluation Failed Partially";
      result.showIcon = true;
    }

    if (!hasScore && totalErrors === 0) {
      result.errorType = "ERROR";
      result.errorTitle = "Evaluation Failed";
      result.showIcon = true;
    }

    if (!hasScore && totalErrors > 0) {
      result.errorType = "ERROR";
      result.errorTitle = "Evaluation Failed";
      result.showIcon = true;
    }
  }

  return result;
}

const CustomChipRenderer = ({ data, evalId, type, handleErrorClick }) => {
  const theme = useTheme();
  const chipColor = getColorByValues(data, type, theme);
  const errorData = evaluateResult(data, evalId);
  return (
    <>
      <ShowComponent condition={type == "bool"}>
        <Box
          onClick={() => handleErrorClick(errorData)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: (theme) => theme.spacing(1.5),
          }}
        >
          <Chip
            label={getChipLabel(data, type)}
            variant="soft"
            sx={{
              color: chipColor?.color,
              background: chipColor?.backgroundColor,
              transition: "none",
              paddingX: (theme) => theme.spacing(0.5),
              typography: "s2",
              cursor: errorData?.showIcon ? "pointer" : "default",
              fontWeight: "fontWeightRegular",
              "&:hover": {
                background: chipColor?.backgroundColor,
                color: chipColor?.color,
              },
            }}
          />
          {errorData?.showIcon && (
            <Iconify
              icon="fluent:warning-24-regular"
              cursor={errorData?.showIcon ? "pointer" : "default"}
              color={
                errorData?.errorType == "PARTIAL" ? "orange.400" : "red.500"
              }
            />
          )}
        </Box>
      </ShowComponent>
      <ShowComponent condition={type == "float"}>
        <Box
          onClick={() => handleErrorClick(errorData)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: (theme) => theme.spacing(1.5),
          }}
        >
          <Chip
            label={getChipLabel(data, type)}
            variant="soft"
            sx={{
              color: chipColor?.color,
              background: chipColor?.backgroundColor,
              transition: "none",
              fontWeight: "fontWeightRegular",
              typography: "s2",
              paddingX: (theme) => theme.spacing(0.5),
              cursor: errorData?.showIcon ? "pointer" : "default",
              "&:hover": {
                background: chipColor?.backgroundColor,
                color: chipColor?.color,
              },
            }}
          />
          {errorData?.showIcon && (
            <Iconify
              icon="fluent:warning-24-regular"
              cursor={errorData?.showIcon ? "pointer" : "default"}
              color={
                errorData?.errorType == "PARTIAL" ? "orange.400" : "red.500"
              }
            />
          )}
        </Box>
      </ShowComponent>
      <ShowComponent condition={type == "str_list"}>
        {data?.strListScore &&
          Object?.entries(data?.strListScore).map((item, index) => (
            <Chip
              key={index}
              label={`${item[0]}: ${item[1]?.score}%`}
              variant="soft"
              sx={{
                color: chipColor?.color,
                background: chipColor?.backgroundColor,
                transition: "none",
                fontWeight: "fontWeightRegular",
                typography: "s2",
                paddingX: (theme) => theme.spacing(0.5),
                cursor: "default",
                "&:hover": {
                  background: chipColor?.backgroundColor,
                  color: chipColor?.color,
                },
              }}
            />
          ))}
      </ShowComponent>
    </>
  );
};

CustomChipRenderer.propTypes = {
  evalId: PropTypes.string,
  data: PropTypes.object,
  type: PropTypes.string,
  handleErrorClick: PropTypes.func,
};

export default CustomChipRenderer;
