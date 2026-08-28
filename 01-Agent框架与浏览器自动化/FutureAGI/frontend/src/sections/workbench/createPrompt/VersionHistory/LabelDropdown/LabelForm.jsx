import { LoadingButton } from "@mui/lab";
import { Box } from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import PropTypes from "prop-types";
import React from "react";
import { useForm } from "react-hook-form";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";
import axios, { endpoints } from "src/utils/axios";

const LabelForm = ({ onClose }) => {
  const { control, handleSubmit } = useForm({
    defaultValues: {
      name: "",
    },
  });

  const queryClient = useQueryClient();

  const { mutate: createLabel, isPending } = useMutation({
    mutationFn: (data) =>
      axios.post(endpoints.develop.runPrompt.createPromptLabel, {
        ...data,
        type: "custom",
      }),
    onSuccess: () => {
      onClose();
      queryClient.invalidateQueries({
        queryKey: ["prompt-labels"],
        type: "all",
      });
    },
  });

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <FormTextFieldV2
        placeholder="Label Name"
        control={control}
        fieldName="name"
        size="small"
        inputProps={{
          sx: {
            paddingY: 0.5,
            paddingX: 1.5,
          },
        }}
        autoFocus
      />
      <LoadingButton
        loading={isPending}
        variant="contained"
        color="primary"
        size="small"
        onClick={handleSubmit(createLabel)}
      >
        Save
      </LoadingButton>
    </Box>
  );
};

LabelForm.propTypes = {
  onClose: PropTypes.func,
};

export default LabelForm;
