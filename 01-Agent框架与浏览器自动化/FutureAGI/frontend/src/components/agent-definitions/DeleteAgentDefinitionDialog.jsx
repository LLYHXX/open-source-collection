import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogActions,
  Typography,
  Button,
  IconButton,
  Box,
} from "@mui/material";
import PropTypes from "prop-types";
import axios, { endpoints } from "src/utils/axios";
import { Events, PropertyName, trackEvent } from "src/utils/Mixpanel";
import { enqueueSnackbar } from "notistack";
import Iconify from "../iconify";
import { LoadingButton } from "@mui/lab";

const DeleteAgentDefinitionDialog = ({
  open,
  onClose,
  agents,
  onDeleteSuccess,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!agents?.length) return;

    setIsDeleting(true);

    trackEvent(Events.deleteAgentDefClicked, {
      [PropertyName.ids]: agents.map((a) => a.id),
    });

    try {
      await axios.delete(endpoints.agentDefinitions.delete, {
        data: {
          agent_ids: agents.map((a) => a.id),
        },
      });

      enqueueSnackbar("Selected agents deleted successfully!", {
        variant: "success",
      });

      onDeleteSuccess?.();
      onClose();
    } catch (err) {
      enqueueSnackbar(
        err.response?.data?.error ||
          "Failed to delete selected agents. Please try again.",
        { variant: "error" },
      );
    } finally {
      setIsDeleting(false);
    }
  };

  // Build dynamic confirmation message
  const getDeleteMessage = () => {
    if (!agents?.length) return "";

    if (agents.length === 1) {
      return `Are you sure you want to delete ${agents[0].agentName} agent definition?`;
    }

    const firstTwo = agents.slice(0, 2).map((a) => a.agentName);
    if (agents.length === 2) {
      return `Are you sure you want to delete ${firstTwo.join(
        " and ",
      )} agent definitions?`;
    }

    const remainingCount = agents.length - 2;
    return `Are you sure you want to delete ${firstTwo.join(
      ", ",
    )} and ${remainingCount} more agent definitions?`;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <Box sx={{ padding: 2 }}>
        <DialogTitle sx={{ padding: 0, margin: 0 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Typography
              fontWeight="fontWeightBold"
              color="text.primary"
              typography="m3"
            >
              Delete Agent definition
              {agents?.length > 1 && "s"}
            </Typography>

            <IconButton onClick={onClose} sx={{ padding: 1 }}>
              <Iconify icon="mdi:close" color="text.primary" />
            </IconButton>
          </Box>

          <Typography
            typography="s1"
            color="text.primary"
            fontWeight={"fontWeightRegular"}
          >
            {getDeleteMessage()}
          </Typography>
        </DialogTitle>

        <Box>
          <DialogActions sx={{ padding: 0, marginTop: "32px" }}>
            <Button
              onClick={() => {
                trackEvent(Events.deleteAgentDefCancelled);
                onClose();
              }}
              size="small"
              variant="outlined"
            >
              <Typography typography="s2" fontWeight="fontWeightSemiBold">
                Cancel
              </Typography>
            </Button>

            <LoadingButton
              variant="contained"
              loading={isDeleting}
              size="small"
              onClick={handleDelete}
              sx={{
                backgroundColor: "red.500",
                color: "common.white",
                "&:hover": { backgroundColor: "red.600" },
              }}
            >
              <Typography typography="s2" fontWeight="fontWeightSemiBold">
                Delete
              </Typography>
            </LoadingButton>
          </DialogActions>
        </Box>
      </Box>
    </Dialog>
  );
};

DeleteAgentDefinitionDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  agents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      agentName: PropTypes.string,
    }),
  ),
  onDeleteSuccess: PropTypes.func,
};

export default DeleteAgentDefinitionDialog;
