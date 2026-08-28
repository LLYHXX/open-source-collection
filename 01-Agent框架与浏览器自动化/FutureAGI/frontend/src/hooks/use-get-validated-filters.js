import { useMemo, useRef } from "react";
import { getComplexFilterValidation } from "src/components/ComplexFilter/common";
import { useDebounce } from "./use-debounce";
import { isEqual } from "lodash";

const DONT_FORMAT_FOR = [
  "Evaluation Metrics",
  "Attribute",
  "Annotation Metrics",
  "System Metrics",
];

export const useGetValidatedFilters = (filters, getCustomProperties) => {
  const previousValidatedFiltersRef = useRef([]);

  const validatedFilters = useMemo(() => {
    const newValidatedFilters = filters
      .map((filter) => {
        const result = getComplexFilterValidation(
          !DONT_FORMAT_FOR.includes(filter?._meta?.parentProperty),
          getCustomProperties,
        ).safeParse(filter);
        if (!result.success) {
          return false;
        }
        return result.data;
      })
      .filter(Boolean);

    // Only return new array if the contents are different
    if (
      JSON.stringify(previousValidatedFiltersRef.current) ===
      JSON.stringify(newValidatedFilters)
    ) {
      return previousValidatedFiltersRef.current;
    }

    previousValidatedFiltersRef.current = newValidatedFilters;
    return newValidatedFilters;
  }, [filters, getCustomProperties]);

  return useDebounce(validatedFilters, 500);
};

export const isValidFiltersChanged = (oldFilters, newFilters) => {
  const oldValidatedFilters = oldFilters
    .map((filter) => {
      const result = getComplexFilterValidation(
        !DONT_FORMAT_FOR.includes(filter?._meta?.parentProperty),
        () => {},
      ).safeParse(filter);
      if (!result.success) {
        return false;
      }
      return result.data;
    })
    .filter(Boolean);

  const newValidatedFilters = newFilters
    .map((filter) => {
      const result = getComplexFilterValidation(
        !DONT_FORMAT_FOR.includes(filter?._meta?.parentProperty),
        () => {},
      ).safeParse(filter);
      if (!result.success) {
        return false;
      }
      return result.data;
    })
    .filter(Boolean);

  return !isEqual(oldValidatedFilters, newValidatedFilters);
};
