import {
  Box,
  CircularProgress,
  IconButton,
  Typography,
  useTheme,
} from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import SvgColor from "src/components/svg-color";
import { ShowComponent } from "src/components/show";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useParams } from "react-router";

import { getColorMap } from "../common";

const PromptLabel = ({ name, id, version, viewOnly, showRemove, disabled }) => {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const colorMap = getColorMap(name, theme);
  const { id: promptId } = useParams();
  const { isPending: isDeletingLabel } = useMutation({
    mutationFn: (id) =>
      axios.delete(endpoints.develop.runPrompt.deletePromptLabel(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["prompt-labels"],
        type: "all",
      });
      queryClient.invalidateQueries({
        queryKey: ["prompt-versions", promptId],
      });
    },
  });

  const { mutate: assignLabels, isPending: isAssigningLabels } = useMutation({
    mutationFn: () =>
      axios.post(endpoints.develop.runPrompt.assignLabels(promptId, id), {
        version: version.template_version,
      }),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["prompt-versions", promptId],
      });
    },
  });

  const { mutate: removeLabel, isPending: isRemovingLabel } = useMutation({
    mutationFn: () =>
      axios.post(endpoints.develop.runPrompt.removeLabel(), {
        label_id: id,
        version_id: version?.id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["prompt-versions", promptId],
      });
    },
  });

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 0,
        "&:hover .copy-on-hover": {
          opacity: 1,
          visibility: "visible",
          width: "24px",
        },
      }}
    >
      <Box
        sx={{
          backgroundColor: colorMap.backgroundColor,
          color: colorMap.color,
          borderRadius: "100px",

          display: "flex",
          padding: "2px 12px 2px 12px",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 1,
          cursor: "pointer",
        }}
        onClick={() => {
          if (disabled) return;
          if (!viewOnly) {
            assignLabels();
          }
        }}
      >
        <Typography typography="s3" fontWeight={500}>
          {name}
        </Typography>
        <ShowComponent
          condition={isDeletingLabel || isAssigningLabels || isRemovingLabel}
        >
          <CircularProgress size={12} color="inherit" />
        </ShowComponent>
        {/* <ShowComponent
          condition={type === "custom" && !isDeletingLabel && !viewOnly}
        >
          <IconButton
            sx={{ padding: 0 }}
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              deleteLabel(id);
            }}
            disabled={disabled}
          >
            <SvgColor
              src="/assets/icons/ic_delete.svg"
              sx={{
                width: "12px",
                height: "12px",
                color: "text.primary",
                cursor: "pointer",
              }}
            />
          </IconButton>
        </ShowComponent>
        <ShowComponent condition={showCopy}>
          <IconButton
            sx={{ padding: 0 }}
            size="small"
            disableRipple
            onClick={(e) => {
              e.stopPropagation();
              copyToClipboard(name);
              enqueueSnackbar("Copied to clipboard", { variant: "success" });
            }}
          >
            <SvgColor
              src="/assets/icons/ic_copy.svg"
              sx={{
                width: "12px",
                height: "12px",
                color: "text.primary",
                cursor: "pointer",
              }}
            />
          </IconButton>
        </ShowComponent> */}
      </Box>
      <ShowComponent condition={showRemove}>
        <IconButton
          className="copy-on-hover"
          sx={{
            padding: 0,
            opacity: 0,
            visibility: "hidden",
            width: 0,
            marginLeft: 0,
            transition: "all 0.2s ease-in-out",
            overflow: "hidden",
          }}
          disabled={disabled}
          disableRipple
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            removeLabel();
          }}
        >
          <SvgColor
            src="/assets/icons/ic_close.svg"
            sx={{
              width: "12px",
              height: "12px",
              color: "text.primary",
              cursor: "pointer",
            }}
          />
        </IconButton>
      </ShowComponent>
    </Box>
  );
};

PromptLabel.propTypes = {
  name: PropTypes.string,
  id: PropTypes.string,
  version: PropTypes.object,
  viewOnly: PropTypes.bool,
  showRemove: PropTypes.bool,
  disabled: PropTypes.bool,
};

export default PromptLabel;
