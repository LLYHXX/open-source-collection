import { Button, Divider, Stack, Typography, useTheme } from "@mui/material";
import React from "react";
import SvgColor from "src/components/svg-color";
import { useAlertStore } from "../../store/useAlertStore";

export default function RowActions() {
  const theme = useTheme();
  // hasUnMutedAlerts is for selected rows
  // currentPageHasMutedAlerts is for whole page selection "select all"
  const {
    selectedRows,
    hasUnMutedAlerts,
    currentPageHasMutedAlerts,
    handleOpenActionModal,
    selectedAll,
    excludingIds,
    totalRows,
    handleCancelSelection,
  } = useAlertStore();

  const message = selectedAll
    ? `${totalRows - excludingIds?.length} Selected`
    : `${selectedRows.length} Selected`;
  return (
    <Stack
      direction={"row"}
      gap={2}
      alignItems={"center"}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 0.5,
        padding: theme.spacing(0, 2),
        height: "38px",
      }}
    >
      <Typography
        variant="s1"
        fontWeight={"fontWeightMedium"}
        color={"primary.main"}
      >
        {message}
      </Typography>
      <Divider
        orientation="vertical"
        sx={{
          borderColor: "divider",
          height: "80%",
        }}
      />
      {/* {selectedRows?.length === 1 && (
        <Button
          variant="text"
          size="small"
          sx={{
            mr: 1,
            typography: "s1",
            color: "text.primary",
            fontWeight: "fontWeightRegular",
          }}
          startIcon={<SvgColor src="/assets/icons/ic_edit.svg" />}
          onClick={() => {

          }}
        >
          Edit
        </Button>
      )} */}
      <Button
        variant="text"
        size="small"
        sx={{
          mr: 1,
          typography: "s1",
          color: "text.primary",
          fontWeight: "fontWeightRegular",
        }}
        startIcon={<SvgColor src="/assets/icons/ic_delete.svg" />}
        onClick={() => handleOpenActionModal("delete")}
      >
        Delete
      </Button>
      <Button
        variant="text"
        size="small"
        sx={{
          mr: 1,
          typography: "s1",
          color: "text.primary",
          fontWeight: "fontWeightRegular",
        }}
        startIcon={<SvgColor src="/assets/icons/ic_mute.svg" />}
        onClick={() =>
          handleOpenActionModal(
            selectedAll
              ? currentPageHasMutedAlerts()
                ? "unmute"
                : "mute"
              : hasUnMutedAlerts()
                ? "mute"
                : "unmute",
          )
        }
      >
        {selectedAll
          ? currentPageHasMutedAlerts()
            ? "Unmute"
            : "Mute"
          : hasUnMutedAlerts()
            ? "Mute"
            : "Unmute"}
      </Button>
      <Divider
        orientation="vertical"
        sx={{
          borderColor: "divider",
          height: "80%",
        }}
      />
      <Button onClick={handleCancelSelection} size="small" variant="text">
        Cancel
      </Button>
    </Stack>
  );
}
