import React from "react";
import ModalWrapper from "../../../components/ModalWrapper/ModalWrapper";
import PropTypes from "prop-types";
import { Typography } from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";

export default function DeleteGroupModal({ open, onClose, id }) {
  const queryClient = useQueryClient();
  const { mutate: deleteGroup, isPending } = useMutation({
    mutationFn: async () => {
      return axios.delete(`${endpoints.develop.eval.groupEvals}${id}/`);
    },
    onSuccess: () => {
      enqueueSnackbar("Group has been deleted", {
        variant: "success",
      });
      queryClient.invalidateQueries({
        queryKey: ["eval-groups"],
      });
      onClose();
    },
  });

  const handleDelete = () => {
    deleteGroup();
  };
  return (
    <ModalWrapper
      actionBtnTitle="Delete Group"
      open={open}
      onClose={onClose}
      title={"Delete Group"}
      onSubmit={handleDelete}
      actionBtnProps={{
        color: "error",
      }}
      isValid={true}
      isLoading={isPending}
      cancelBtnSx={{
        "& .MuiTypography-root": {
          color: isPending ? "unset" : "text.primary",
        },
      }}
    >
      <Typography
        typography={"s1"}
        fontWeight={"fontWeightRegular"}
        color={"text.primary"}
      >
        Are you sure you&apos;d like to delete this group? This action is
        irreversible <br />
        <Typography
          typography={"s1"}
          fontWeight={"fontWeightMedium"}
          color={"text.primary"}
          component={"span"}
        >
          Note:{" "}
        </Typography>
        Once the group is deleted, the evaluation applied on the platform will
        still be visible
      </Typography>
    </ModalWrapper>
  );
}

DeleteGroupModal.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  id: PropTypes.string,
};
