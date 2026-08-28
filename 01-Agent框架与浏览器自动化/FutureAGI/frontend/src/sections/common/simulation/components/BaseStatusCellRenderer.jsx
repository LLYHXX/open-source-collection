import { Button, Chip } from "@mui/material";
import React, { useCallback, useEffect } from "react";
import PropTypes from "prop-types";
import Iconify from "src/components/iconify";
import { enqueueSnackbar } from "src/components/snackbar";
import { useCancelExecution } from "../hooks/useCancelExecution";
import { statusStyles, STOPPABLE_STATUSES } from "../constants/statusStyles";

/**
 * Base status cell renderer component for AG Grid
 * Can be used for both simulation executions and test runs
 *
 * @param {Object} params - AG Grid cell params (value, data, api, column)
 * @param {Function} onRefresh - Callback to refresh the grid after cancellation
 * @param {boolean} showSnackbar - Whether to show snackbar notifications (default: true)
 */
const BaseStatusCellRenderer = ({ params, onRefresh, showSnackbar = true }) => {
  const { value, data } = params;
  const showStopButton = STOPPABLE_STATUSES.includes(value);

  useEffect(() => {
    params.api.autoSizeColumns([params.column.getColId()]);
  }, [showStopButton, params.api, params.column]);

  const { mutate: cancelExecution } = useCancelExecution();

  const handleStop = useCallback(
    (event) => {
      event.stopPropagation();
      cancelExecution(data?.id, {
        onSuccess: () => {
          if (showSnackbar) {
            enqueueSnackbar("Execution cancelled", { variant: "success" });
          }
          onRefresh?.();
        },
        onError: (error) => {
          if (showSnackbar) {
            enqueueSnackbar(
              error?.response?.data?.error ||
                error?.response?.data?.result ||
                "Failed to cancel execution",
              { variant: "error" },
            );
          }
        },
      });
    },
    [cancelExecution, data?.id, onRefresh, showSnackbar],
  );

  return (
    <>
      <Chip
        variant="soft"
        label={value}
        size="small"
        sx={{
          typography: "s3",
          fontWeight: "fontWeightRegular",
          pointerEvents: "none",
          ...statusStyles[value],
        }}
      />
      {showStopButton && (
        <Button
          variant="outlined"
          size="small"
          sx={{
            borderRadius: "4px",
            paddingX: 1.5,
            width: "70px",
            height: "26px",
            ml: 2,
          }}
          onClick={handleStop}
          startIcon={
            <Iconify
              icon="bi:stop-circle"
              color="text.primary"
              width="14px"
              height="14px"
              sx={{
                cursor: "pointer",
                marginRight: "-4px",
              }}
            />
          }
        >
          Stop
        </Button>
      )}
    </>
  );
};

BaseStatusCellRenderer.propTypes = {
  params: PropTypes.object.isRequired,
  onRefresh: PropTypes.func,
  showSnackbar: PropTypes.bool,
};

export default BaseStatusCellRenderer;
