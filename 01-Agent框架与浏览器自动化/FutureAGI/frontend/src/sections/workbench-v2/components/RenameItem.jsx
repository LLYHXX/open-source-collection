import { Divider, TextField } from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { enqueueSnackbar } from "notistack";
import PropTypes from "prop-types";
import React, { useState } from "react";
import ModalWrapper from "src/components/ModalWrapper/ModalWrapper";
import axios, { endpoints } from "../../../utils/axios";
import { useParams } from "react-router";
import { PROMPT_ITEM_TYPES } from "../common";
import _ from "lodash";
import { Events, PropertyName, trackEvent } from "../../../utils/Mixpanel";
export const RenameItem = ({
  open,
  onClose,
  name,
  type = PROMPT_ITEM_TYPES.FILE,
  id,
}) => {
  const [folderName, setFolderName] = useState(name);
  const queryClient = useQueryClient();
  const { folder } = useParams();

  const { mutate: updateFolder, isPending } = useMutation({
    mutationFn: async (name) => {
      if (type === PROMPT_ITEM_TYPES.FILE) {
        return axios.post(endpoints.develop.runPrompt.getNameChange(id), {
          name,
        });
      } else if (type === PROMPT_ITEM_TYPES.TEMPLATE) {
        return axios.patch(endpoints.develop.runPrompt.promptTemplateId(id), {
          name,
        });
      } else {
        return axios.patch(endpoints.develop.runPrompt.promptFolderId(id), {
          name,
        });
      }
    },
    onSuccess: () => {
      enqueueSnackbar(`${folderName} ${_.toLower(type)} has been updated`, {
        variant: "success",
      });
      onClose();
      setFolderName("");
      if (type === PROMPT_ITEM_TYPES.FILE) {
        queryClient.invalidateQueries({
          queryKey: ["folder-items", folder],
        });
      } else if (type === PROMPT_ITEM_TYPES.TEMPLATE) {
        queryClient.invalidateQueries({
          queryKey: ["prompt-templates"],
        });
      } else {
        if (folder === "all") {
          queryClient.invalidateQueries({
            queryKey: ["folder-items", folder],
          });
        }
        queryClient.invalidateQueries({
          queryKey: ["prompt-folders"],
        });
      }
    },
  });

  const handleSubmit = () => {
    trackEvent(Events.promptRenameSaveConfirmed, {
      [PropertyName.type]: type,
      [PropertyName.id]: id,
    });
    updateFolder(folderName);
  };

  return (
    <ModalWrapper
      open={open}
      onClose={onClose}
      title={`Rename ${_.toLower(type)}`}
      hideCancelBtn
      actionBtnSx={{
        width: "100%",
      }}
      dialogActionSx={{
        mt: 0,
      }}
      isValid={folderName.trim().length > 0}
      onSubmit={handleSubmit}
      isLoading={isPending}
    >
      <Divider
        sx={{
          borderColor: "divider",
        }}
      />
      <TextField
        autoFocus
        value={folderName}
        onChange={(e) => setFolderName(e.target.value)}
        size="small"
        label="Name"
        fullWidth
        onKeyDown={(e) => {
          if (e.key === "Enter" && folderName.trim().length > 0) {
            e.preventDefault(); // prevent form submit/reload
            handleSubmit();
          }
        }}
      />
    </ModalWrapper>
  );
};

RenameItem.propTypes = {
  id: PropTypes.string,
  onClose: PropTypes.func,
  open: PropTypes.bool,
  name: PropTypes.string,
  type: PropTypes.string,
};
