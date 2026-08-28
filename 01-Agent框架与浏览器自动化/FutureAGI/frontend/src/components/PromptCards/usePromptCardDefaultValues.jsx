import { isContentNotEmpty } from "src/sections/workbench/createPrompt/Playground/common";
import { PromptRoles } from "src/utils/constants";

const getRoleChangePermission = (role, index) => {
  if (role === PromptRoles.SYSTEM) return false;
  if (index === 1 && role === PromptRoles.USER) return false;
  return true;
};

const getRemovePermission = (role, index) => {
  if (role === PromptRoles.SYSTEM) return false;
  if (index === 1 && role === PromptRoles.USER) return false;
  return true;
};

export const usePromptCardDefaultValues = ({
  role,
  index,
  viewOptions,
  prompt,
}) => {
  const hasContent = isContentNotEmpty(prompt);

  const allowRoleChange =
    viewOptions?.allowRoleChange !== undefined
      ? viewOptions?.allowRoleChange
      : getRoleChangePermission(role, index);

  const allowRemove =
    viewOptions?.allowRemove !== undefined
      ? viewOptions?.allowRemove
      : getRemovePermission(role, index);

  const allowImprovePrompt =
    viewOptions?.allowImprovePrompt !== undefined
      ? viewOptions?.allowImprovePrompt
      : role === PromptRoles.USER && Boolean(hasContent);

  const allowGeneratePrompt =
    viewOptions?.allowGeneratePrompt !== undefined
      ? viewOptions?.allowGeneratePrompt
      : role === PromptRoles.USER && Boolean(!hasContent);

  const allowAttachment =
    viewOptions?.allowAttachment !== undefined
      ? viewOptions?.allowAttachment
      : role === PromptRoles.USER;

  const allowSync =
    viewOptions?.allowSync !== undefined
      ? viewOptions?.allowSync
      : role === PromptRoles.SYSTEM;

  return {
    allowRoleChange,
    allowRemove,
    allowImprovePrompt,
    allowGeneratePrompt,
    allowAttachment,
    allowSync,
  };
};
