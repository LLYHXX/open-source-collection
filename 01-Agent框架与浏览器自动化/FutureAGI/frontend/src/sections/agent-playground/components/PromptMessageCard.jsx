import React, { useState, useCallback } from "react";
import PropTypes from "prop-types";
import { PromptRoles } from "src/utils/constants";
import PromptCard from "src/components/PromptCards/PromptCard";

export default function PromptMessageCard({
  id: _id,
  role,
  content,
  index,
  onRoleChange,
  onContentChange,
  onRemove,
  existingRoles,
  disabled,
}) {
  const [expandPrompt, setExpandPrompt] = useState(false);

  // Handle prompt content change from Quill editor
  const handlePromptChange = useCallback(
    (newContent) => {
      onContentChange(newContent);
    },
    [onContentChange],
  );

  // Handle role change
  const handleRoleChange = useCallback(
    (newRole) => {
      onRoleChange(newRole);
    },
    [onRoleChange],
  );

  // View options for PromptCard
  const viewOptions = {
    allowRoleChange: true,
    allowRemove: true,
    allowImprovePrompt: true,
    allowGeneratePrompt: true,
    allowAttachment: true,
    allowSync: false,
    allowAllRoleChange: true,
    sortable: false,
  };

  return (
    <PromptCard
      prompt={content || []}
      role={role}
      onPromptChange={handlePromptChange}
      onRoleChange={handleRoleChange}
      viewOptions={viewOptions}
      index={index}
      onRemove={onRemove}
      showEditEmbed={false}
      mentionEnabled={false}
      disabled={disabled}
      expandable={false}
      expandPrompt={expandPrompt}
      setExpandPrompt={setExpandPrompt}
      existingRoles={existingRoles}
    />
  );
}

PromptMessageCard.propTypes = {
  id: PropTypes.string.isRequired,
  role: PropTypes.oneOf(Object.values(PromptRoles)).isRequired,
  content: PropTypes.array,
  index: PropTypes.number.isRequired,
  onRoleChange: PropTypes.func.isRequired,
  onContentChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  existingRoles: PropTypes.array,
  disabled: PropTypes.bool,
};
