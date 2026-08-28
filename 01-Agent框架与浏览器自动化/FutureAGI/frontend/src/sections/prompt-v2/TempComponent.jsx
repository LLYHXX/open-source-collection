import { Box, Button } from "@mui/material";
import React, { useState } from "react";
import { PromptRoles } from "src/utils/constants";
import { getRandomId } from "src/utils/utils";
import PromptCard from "src/components/PromptCards/PromptCard";
import { logger } from "@sentry/react";

const dummy1 = [
  {
    id: "a",
    role: "system",
    content: [
      {
        type: "text",
        text: "",
      },
    ],
  },
  {
    id: "b",
    role: "user",
    content: [
      {
        type: "text",
        text: "{{test}} \n",
      },
      {
        type: "image_url",
        imageUrl: {
          url: "https://picsum.photos/id/237/200/300",
          img_name: "pexels-maria-ravanelli-20372669.jpg",
          img_size: 1123089,
        },
      },
      {
        type: "text",
        text: "\n\n{{dsadas}}\n",
      },
    ],
  },
];

const TempComponent = () => {
  const [prompts, setPrompts] = useState(dummy1);

  const onRoleChange = (role, index) => {
    const newPrompts = [...prompts];
    newPrompts[index].role = role;
    setPrompts(newPrompts);
  };

  const onPromptRemove = (index) => {
    const newPrompts = [...prompts];
    newPrompts.splice(index, 1);
    setPrompts(newPrompts);
  };

  const onPromptChange = (content, index) => {
    const newPrompts = [...prompts];
    newPrompts[index].content = content;
    setPrompts(newPrompts);
  };

  const onAddPrompt = () => {
    const newPrompts = [...prompts];
    newPrompts.push({
      id: getRandomId(),
      role: PromptRoles.USER,
      content: [
        {
          type: "text",
          text: "",
        },
      ],
    });
    setPrompts(newPrompts);
  };

  const openVariableEditor = () => {
    logger.debug("openVariableEditor");
  };

  const tempCols = {
    act: ["1"],
    prompt: ["1"],
    "JSON-col": ["1"],
  };

  return (
    <Box
      sx={{ padding: 2, backgroundColor: "background.paper", height: "100%" }}
    >
      <Box
        sx={{ width: "50%", display: "flex", flexDirection: "column", gap: 2 }}
      >
        {prompts.map(({ id, role, content }, _idx) => (
          <PromptCard
            key={id}
            role={role}
            index={_idx}
            prompt={content}
            onRemove={() => onPromptRemove(_idx)}
            onRoleChange={(role) => onRoleChange(role, _idx)}
            onPromptChange={(content) => onPromptChange(content, _idx)}
            appliedVariableData={tempCols}
            openVariableEditor={openVariableEditor}
            viewOptions={{
              allowGeneratePrompt: false,
              allowImprovePrompt: false,
            }}
          />
        ))}
        <Button variant="outlined" size="small" onClick={onAddPrompt}>
          Add Prompt
        </Button>
      </Box>
    </Box>
  );
};

export default TempComponent;
