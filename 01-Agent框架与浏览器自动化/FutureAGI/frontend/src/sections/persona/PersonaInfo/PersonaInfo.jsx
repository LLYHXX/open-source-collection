import { Box, Divider, Typography } from "@mui/material";
import React from "react";
import PersonaBasicInfo from "./PersonaBasicInfo";
import PersonaBehaviouralInfo from "./PersonaBehaviouralInfo";
import PersonaConversationInfo from "./PersonaConversationInfo";
import { FormProvider, useForm } from "react-hook-form";
import {
  getPersonaDefaultValues,
  PersonCreateValidationSchema,
} from "../PersonaCreateEdit/common";
import { zodResolver } from "@hookform/resolvers/zod";
import PrintFormValues from "src/utils/PrintFormValues";
import PropTypes from "prop-types";
import { ShowComponent } from "src/components/show";
import { AGENT_TYPES } from "src/sections/agents/constants";
import PersonaChatSettingsInfo from "./PersonaChatInfo";

const PersonaInfo = ({
  onSuccess: _onSuccess,
  onCancel: _onCancel,
  editPersona,
  persona,
}) => {
  const _isEditMode = Boolean(editPersona);
  const form = useForm({
    defaultValues: getPersonaDefaultValues(editPersona),
    resolver: zodResolver(PersonCreateValidationSchema),
  });

  // const onSubmit = (data) => {
  //   if (isEditMode) {
  //     const updatePayload = {
  //       ...data,
  //       languages: data?.language,
  //     };
  //     delete updatePayload?.language;
  //   } else {
  //     // createPersona(data);
  //   }
  // };

  return (
    <FormProvider {...form}>
      <Box
        sx={{
          padding: 2,
          display: "flex",
          flexDirection: "column",
          gap: 2,
          height: "100%",
        }}
        component="form"
        // onSubmit={form.handleSubmit(onSubmit)}
      >
        <PrintFormValues control={form.control} />
        <Box>
          <Typography typography="m2" fontWeight="fontWeightSemiBold">
            Persona Info
          </Typography>
        </Box>
        <Divider flexItem orientation="horizontal" />
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <PersonaBasicInfo persona={persona} />
          <PersonaBehaviouralInfo persona={persona} />
          <ShowComponent
            condition={persona?.simulationType === AGENT_TYPES.VOICE}
          >
            <PersonaConversationInfo persona={persona} />
          </ShowComponent>
          <ShowComponent
            condition={persona?.simulationType === AGENT_TYPES.CHAT}
          >
            <PersonaChatSettingsInfo persona={persona} />
          </ShowComponent>
        </Box>
        {/* <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="outlined"
            color="primary"
            size="small"
            fullWidth
            onClick={onCancel}
          >
            Cancel
          </Button>
          <LoadingButton
            variant="contained"
            color="primary"
            size="small"
            fullWidth
            type="submit"
          >
            {isEditMode ? "Update" : "Add"}
          </LoadingButton>
        </Box> */}
      </Box>
    </FormProvider>
  );
};

PersonaInfo.propTypes = {
  onSuccess: PropTypes.func,
  onCancel: PropTypes.func,
  editPersona: PropTypes.object,
  persona: PropTypes.object,
};

export default PersonaInfo;
