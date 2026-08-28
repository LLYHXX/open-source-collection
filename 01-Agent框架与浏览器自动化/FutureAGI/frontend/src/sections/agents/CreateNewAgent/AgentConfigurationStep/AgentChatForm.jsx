import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import CustomModelDropdownControl from "src/components/custom-model-dropdown/CustomModelDropdownControl";
import { MODEL_TYPES } from "../../../develop-detail/RunPrompt/common";

export default function AgentChatForm({ control }) {
  return (
    <Box display="flex" flexDirection="column" gap={2}>
      <CustomModelDropdownControl
        control={control}
        fieldName="model"
        label="Model Used"
        fullWidth
        searchDropdown
        size="small"
        showIcon
        modelObjectKey={"modelDetails"}
        extraParams={{ model_type: MODEL_TYPES.LLM }}
        requireUserApiKey={false}
      />
    </Box>
  );
}

AgentChatForm.propTypes = {
  control: PropTypes.object.isRequired,
};
