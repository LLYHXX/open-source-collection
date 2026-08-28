import { useState, useEffect, useRef } from "react";
import _ from "lodash";

const INITIAL_REASONING = {
  sliders: [],
  dropdowns: [],
  showReasoningProcess: true,
};

const INITIAL_MODEL_PARAMETERS = {
  sliders: [],
  dropdowns: [],
  booleans: [],
  reasoning: INITIAL_REASONING,
};

/**
 * Resolve the value for a parameter item, preferring saved config on first load.
 * @param {Object} item - The parameter item from API
 * @param {string} id - The resolved id for the item
 * @param {boolean} useSavedConfig - Whether to use saved configuration
 * @param {Object} lookupObj - The object to look up saved values in (e.g. savedConfiguration, savedConfiguration?.booleans)
 * @param {*} fallback - Default value when nothing matches (null, false, item?.options?.[0])
 */
const resolveValue = (item, id, useSavedConfig, lookupObj, fallback) => {
  const fb = typeof fallback === "function" ? fallback(item) : fallback;
  if (useSavedConfig) {
    return (
      lookupObj?.[item.label] ??
      lookupObj?.[id] ??
      item.value ??
      item.default ??
      fb
    );
  }
  return item.value ?? item.default ?? fb;
};

/**
 * Filter out already-existing params and map new ones with resolved values.
 * @param {Array} existingParams - Already-present parameters
 * @param {Array} apiParams - New parameters from the API
 * @param {boolean} useSavedConfig - Whether to use saved configuration
 * @param {Object} lookupObj - The object to look up saved values in
 * @param {*} fallback - Default value when nothing matches
 */
const mergeNewParams = (
  existingParams,
  apiParams,
  useSavedConfig,
  lookupObj,
  fallback,
) => {
  if (!apiParams?.length) return existingParams;

  const existingIds = existingParams?.map((p) => p.id) || [];

  // Update existing params' values when applying saved config (e.g. version switch)
  const updatedExisting = useSavedConfig
    ? existingParams.map((param) => {
        const apiItem = apiParams.find(
          (item) => (item.id ?? _.camelCase(item.label)) === param.id,
        );
        if (!apiItem) return param;
        return {
          ...param,
          value: resolveValue(apiItem, param.id, true, lookupObj, fallback),
        };
      })
    : existingParams;

  // Add new params that don't exist yet
  const newItems = apiParams
    .filter((item) => {
      const id = item.id ?? _.camelCase(item.label);
      return !existingIds.includes(id);
    })
    .map((item) => {
      const id = item.id ?? _.camelCase(item.label);
      return {
        ...item,
        value: resolveValue(item, id, useSavedConfig, lookupObj, fallback),
        id,
      };
    });
  return [...updatedExisting, ...newItems];
};

/**
 * Custom hook for managing model parameters state
 * @param {Object} modelParams - Model parameters from API
 * @param {string} watchedModel - Selected model name
 * @param {Object} savedConfiguration - Previously saved configuration from node data
 * @returns {Object} Model parameters state and update functions
 */
export function useModelParameters(
  modelParams,
  watchedModel,
  savedConfiguration,
) {
  const [modelParameters, setModelParameters] = useState(
    INITIAL_MODEL_PARAMETERS,
  );
  const modelParametersModelRef = useRef(null);
  const savedConfigAppliedRef = useRef(false);
  const prevSavedConfigRef = useRef(savedConfiguration);

  // Reset applied flag when savedConfiguration changes (e.g. version switch)
  useEffect(() => {
    if (!_.isEqual(prevSavedConfigRef.current, savedConfiguration)) {
      savedConfigAppliedRef.current = false;
      prevSavedConfigRef.current = savedConfiguration;
    }
  }, [savedConfiguration]);

  // Update model parameters when model changes
  useEffect(() => {
    if (!watchedModel) {
      setModelParameters(INITIAL_MODEL_PARAMETERS);
      modelParametersModelRef.current = null;
      savedConfigAppliedRef.current = false;
      return;
    }

    const modelChanged = modelParametersModelRef.current !== watchedModel;

    // Reset the applied flag when model changes so saved config won't carry over
    if (modelChanged) {
      savedConfigAppliedRef.current = false;
    }

    if (!modelParams) {
      if (modelChanged) {
        modelParametersModelRef.current = null;
        setModelParameters(INITIAL_MODEL_PARAMETERS);
      }
      return;
    }

    // Only use saved configuration on first load for this model, not after user edits
    const useSavedConfig = savedConfiguration && !savedConfigAppliedRef.current;

    setModelParameters((prev) => {
      const baseParams = modelChanged
        ? INITIAL_MODEL_PARAMETERS
        : {
            sliders: prev?.sliders || [],
            dropdowns: prev?.dropdowns || [],
            booleans: prev?.booleans || [],
            reasoning: prev?.reasoning || INITIAL_REASONING,
          };

      const result = {
        sliders: [...baseParams.sliders],
        dropdowns: [...baseParams.dropdowns],
        booleans: [...baseParams.booleans],
        reasoning: { ...baseParams.reasoning },
      };

      result.sliders = mergeNewParams(
        result.sliders,
        modelParams?.sliders,
        useSavedConfig,
        savedConfiguration,
        null,
      );

      result.booleans = mergeNewParams(
        result.booleans,
        modelParams?.booleans,
        useSavedConfig,
        savedConfiguration?.booleans,
        false,
      );

      result.dropdowns = mergeNewParams(
        result.dropdowns,
        modelParams?.dropdowns,
        useSavedConfig,
        savedConfiguration?.dropdowns,
        (item) => item?.options?.[0],
      );

      // Handle reasoning parameters — only present for some models
      if (modelParams?.reasoning) {
        result.reasoning = {
          sliders: mergeNewParams(
            [],
            modelParams.reasoning.sliders || [],
            useSavedConfig,
            savedConfiguration,
            null,
          ),
          dropdowns: mergeNewParams(
            [],
            modelParams.reasoning.dropdowns || [],
            useSavedConfig,
            savedConfiguration,
            (item) => item?.options?.[0],
          ),
          showReasoningProcess: useSavedConfig
            ? savedConfiguration?.showReasoningProcess ?? true
            : result.reasoning?.showReasoningProcess ?? true,
        };
      } else {
        // Model doesn't support reasoning — clear it entirely
        result.reasoning = null;
      }

      return result;
    });

    if (useSavedConfig) {
      savedConfigAppliedRef.current = true;
    }

    modelParametersModelRef.current = watchedModel;
  }, [modelParams, watchedModel, savedConfiguration]);

  const updateSliderParameter = (index, value) => {
    setModelParameters((prev) => ({
      ...prev,
      sliders: prev.sliders?.map((item, i) =>
        i === index ? { ...item, value } : item,
      ),
    }));
  };

  const updateBooleanParameter = (index, value) => {
    setModelParameters((prev) => ({
      ...prev,
      booleans: prev.booleans?.map((item, i) =>
        i === index ? { ...item, value } : item,
      ),
    }));
  };

  const updateDropdownParameter = (index, value) => {
    setModelParameters((prev) => ({
      ...prev,
      dropdowns: prev.dropdowns?.map((item, i) =>
        i === index ? { ...item, value } : item,
      ),
    }));
  };

  const updateReasoningSliderParameter = (index, value) => {
    setModelParameters((prev) => ({
      ...prev,
      reasoning: {
        ...prev.reasoning,
        sliders: prev.reasoning?.sliders?.map((item, i) =>
          i === index ? { ...item, value } : item,
        ),
      },
    }));
  };

  const updateReasoningDropdownParameter = (index, value) => {
    setModelParameters((prev) => ({
      ...prev,
      reasoning: {
        ...prev.reasoning,
        dropdowns: prev.reasoning?.dropdowns?.map((item, i) =>
          i === index ? { ...item, value } : item,
        ),
      },
    }));
  };

  const updateShowReasoningProcess = (value) => {
    setModelParameters((prev) => ({
      ...prev,
      reasoning: {
        ...prev.reasoning,
        showReasoningProcess: value,
      },
    }));
  };

  return {
    modelParameters,
    updateSliderParameter,
    updateBooleanParameter,
    updateDropdownParameter,
    updateReasoningSliderParameter,
    updateReasoningDropdownParameter,
    updateShowReasoningProcess,
  };
}
