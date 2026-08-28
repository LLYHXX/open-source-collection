import { Box, Chip, Typography } from "@mui/material";
import _ from "lodash";
import React from "react";
import QuickFilter from "src/components/ComplexFilter/QuickFilterComponents/QuickFilter";
import { format } from "date-fns";
import { interpolateColorBasedOnScore } from "src/utils/utils";
import AnnotationValues from "../../../traceDetailDrawer/CustomRenderer/AnnotationValues";
import GridIcon from "src/components/gridIcon/GridIcon";
import StatusChip from "src/components/custom-status-chip/CustomStatusChip";
import CustomJsonViewer, {
  RenderJSONString,
} from "src/components/custom-json-viewer/CustomJsonViewer";
import CustomTooltip from "src/components/tooltip";
import { OutputTypes } from "src/sections/common/DevelopCellRenderer/CellRenderers/cellRendererHelper";
import NumericCell from "src/sections/common/DevelopCellRenderer/EvaluateCellRenderer/NumericCell";

const IgnoredQuickFilters = ["input", "output", "start_time"];

const CustomTraceRenderer = (params) => {
  const column = params.colDef.col;
  const outputType = column?.outputType;
  const shouldReverse = column?.reverseOutput;
  const applyQuickFilters = params.applyQuickFilters;

  const value = shouldReverse
    ? `${100 - parseFloat(params.value)}`
    : `${params.value}`;

  const backgroundColor =
    column?.groupBy === "Evaluation Metrics" &&
    outputType !== OutputTypes.NUMERIC
      ? interpolateColorBasedOnScore(parseFloat(value), 100, shouldReverse)
      : "";

  const isEval = column?.groupBy === "Evaluation Metrics";
  const isAnnotation = column?.groupBy === "Annotation Metrics";

  const renderJson = (val, justString) => {
    if (justString) {
      return <RenderJSONString val={val} />;
    }
    return <CustomJsonViewer object={val} />;
  };

  const renderValue = (fromCell) => {
    if (isEval) {
      return renderEval(params.value);
    }

    if (isAnnotation) {
      return (
        <AnnotationValues
          value={params.value}
          annotationType={column?.annotationLabelType}
          maxChips={1}
          settings={column?.settings}
        />
      );
    }

    if (typeof params.value === "object") {
      return renderJson(params.value, fromCell);
    } else if (typeof params.value === "boolean") {
      return `${params.value}`;
    }

    return params.value;
  };

  const renderEval = (val) => {
    if (outputType === OutputTypes.NUMERIC) {
      return <NumericCell value={Number(value)} sx={{ padding: "0" }} />;
    }
    if (Array.isArray(val)) {
      return (
        <Box sx={{ display: "flex", gap: 1 }}>
          {val.map((each) => (
            <Chip
              size="small"
              key={each}
              label={each}
              variant="outlined"
              color="primary"
            />
          ))}
        </Box>
      );
    }
    // Scores on 0-1 scale → multiply by 100 for display; already 0-100 → use as-is
    const pctValue =
      parseFloat(value) <= 1 ? parseFloat(value) * 100 : parseFloat(value);
    return `${pctValue.toFixed(pctValue % 1 === 0 ? 0 : 2)}%`;
  };

  if (
    params.value === null ||
    params.value === undefined ||
    (Array.isArray(params.value) && !params?.value?.length)
  )
    return (
      <Box
        sx={{
          paddingX: 1,
          height: "100%",
          alignItems: "center",
          display: "flex",
        }}
      >
        -
      </Box>
    );

  if (column.id === "status" && params.value) {
    return (
      <Box paddingLeft={1}>
        <StatusChip label={`Status: ${params.value}`} status={params.value} />
      </Box>
    );
  }

  if (column.id === "trace_name" || column.id === "span_name") {
    const nodeType = params.data?.node_type;
    return (
      <QuickFilter
        show={!IgnoredQuickFilters.includes(column.id)}
        onClick={(e) =>
          applyQuickFilters({
            col: column,
            value: params.value,
            filterAnchor: {
              top: e.clientY,
              left: e.clientX,
            },
          })
        }
      >
        <Box
          sx={{
            paddingX: 1.8,
            height: "100%",
            alignItems: "center",
            display: "flex",
            gap: 1.4,
          }}
        >
          <GridIcon
            src={`/icons/tracedetails/${nodeType}_icon.svg`}
            sx={{
              width: 24,
              height: 24,
              mb: 0.3,
            }}
          />
          <Typography color="text.primary" variant="s1">
            {_.capitalize(params.value)}
          </Typography>
        </Box>
      </QuickFilter>
    );
  }

  return (
    <CustomTooltip
      show={column?.id === "input" || column?.id === "output"}
      title={
        <Box sx={{ maxHeight: 240, minWidth: "200px", overflowY: "auto" }}>
          {renderValue()}
        </Box>
      }
    >
      <Box sx={{ width: "100%", height: "100%" }}>
        <QuickFilter
          show={!IgnoredQuickFilters.includes(column.id)}
          onClick={(e) =>
            applyQuickFilters({
              col: column,
              value: params.value,
              filterAnchor: {
                top: e.clientY,
                left: e.clientX,
              },
            })
          }
        >
          <Box
            sx={{
              paddingX: 1,
              backgroundColor,
              height: "100%",
              alignItems: "center",
              display: "flex",
            }}
          >
            <Typography
              typography="s3"
              fontWeight={column?.id === "trace_id" ? "fontWeightMedium" : 400}
              color={column?.id === "trace_id" ? "text.primary" : "inherit"}
              sx={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                cursor: column?.id === "trace_id" ? "pointer" : "default",
              }}
            >
              {column?.id === "start_time" && params.value
                ? format(new Date(params.value), "dd/MM/yyyy - HH:mm")
                : renderValue(true)}
            </Typography>
          </Box>
        </QuickFilter>
      </Box>
    </CustomTooltip>
  );
};

export default CustomTraceRenderer;
