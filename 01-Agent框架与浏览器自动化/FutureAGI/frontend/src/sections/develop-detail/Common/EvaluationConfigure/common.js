export const allowedColumnFilter = (evalConfig, allColumns) => {
  if (evalConfig?.evalTags?.includes("FUTURE_EVALS")) {
    if (evalConfig?.runPromptColumn) {
      if (evalConfig.templateName === "prompt_instruction_adherence") {
        if (window.location.pathname.includes("/dashboard/develop/")) {
          return allColumns?.filter((col) => col.originType === "run_prompt");
        } else {
          return allColumns;
        }
      }
      return allColumns?.filter((col) => col.originType === "run_prompt");
    }
    // if (!evalConfig?.evalTags?.includes("IMAGE")) {
    //   return allColumns?.filter((col) => col?.col?.dataType !== "image");
    // }
  }
  return allColumns;
};

export const keyWiseAllowedColumnFilter = (key, evalConfig, allColumns) => {
  // For prompt_instruction_adherence, "prompt" key should only show run_prompt columns
  if (
    evalConfig?.templateName === "prompt_instruction_adherence" &&
    key === "prompt"
  ) {
    return allColumns?.filter((col) => col.originType === "run_prompt");
  }

  // This is hardcoded in frontend for this specific case
  if (
    evalConfig?.templateName === "Eval Images" &&
    (key === "input_image_url" || key === "output_image_url")
  ) {
    return allColumns?.filter((col) => col?.col?.dataType === "image");
  }

  if (evalConfig?.evalTags?.includes("AUDIO")) {
    if (onlyAudioEvalTemplate.includes(evalConfig?.templateName)) {
      return allColumns?.filter((col) => col?.col?.dataType === "audio");
    }
    return allColumns;
  }
  return allColumns?.filter((col) => col?.col?.dataType !== "audio");
};

export const onlyAudioEvalTemplate = [
  "Audio Quality",
  "Eval Audio Description",
];
