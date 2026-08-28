import { useMemo } from "react";
import {
  extractVariableFromAllCols,
  getDropdownOptionsFromCols,
} from "src/sections/develop-detail/RunPrompt/common";

/**
 * Custom hook to get variable options for prompt editors.
 * Consolidates the common pattern of extracting variables and dropdown options
 * from columns, JSON schemas, and derived variables.
 *
 * @param {Array} allColumns - All columns in the dataset
 * @param {Object} jsonSchemas - JSON schemas keyed by column ID (from useGetJsonColumnSchema)
 * @param {Object} derivedVariables - Derived variables from prompt outputs (from useDerivedVariables)
 * @returns {Object} Object containing existingCols and mentionValues
 */
export const useVariableOptions = (
  allColumns = [],
  jsonSchemas = {},
  derivedVariables = {},
) => {
  const existingCols = useMemo(() => {
    return extractVariableFromAllCols(
      allColumns,
      jsonSchemas,
      derivedVariables,
    );
  }, [allColumns, jsonSchemas, derivedVariables]);

  const mentionValues = useMemo(() => {
    return getDropdownOptionsFromCols(
      allColumns,
      jsonSchemas,
      derivedVariables,
    );
  }, [allColumns, jsonSchemas, derivedVariables]);

  return { existingCols, mentionValues };
};

export default useVariableOptions;
