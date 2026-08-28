import { useMemo } from "react";

// Define field groups for each step
const stepFields = {
  0: [
    "agentDefinition",
    "scenarioName",
    "numOfScenarios",
    "addPersonaAutomatically",
    "personas",
    "hasAgentPrompt",
    "agentDefExists",
    "agentType",
    "replaySessionId",
  ],
  2: ["model", "config", "errorLocalizer", "kbId", "projectEvals"],
};

/**
 * Custom hook to check if specific step fields are dirty
 * @param {Object} dirtyFields - The dirtyFields object from react-hook-form formState
 * @returns {Function} isStepDirty - Function that takes a step number and returns boolean
 */
export function useStepDirty(dirtyFields) {
  // Helper function to check if a step is dirty
  const isStepDirty = useMemo(() => {
    return (stepNumber) => {
      const fields = stepFields[stepNumber];
      if (!fields) return false;

      return fields.some((field) => {
        // Handle nested fields like agentDefinition.name
        if (field.includes(".")) {
          const [parent, child] = field.split(".");
          return dirtyFields[parent]?.[child] === true;
        }
        // Handle nested objects like agentDefinition
        if (dirtyFields[field] && typeof dirtyFields[field] === "object") {
          // If it's an object, check if any nested field is dirty
          return Object.values(dirtyFields[field]).some(
            (value) => value === true,
          );
        }
        return dirtyFields[field] === true;
      });
    };
  }, [dirtyFields]);

  return isStepDirty;
}
