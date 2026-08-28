import { useMemo, useEffect } from "react";
import { useSearchParams as _useSearchParams } from "react-router-dom";

// ----------------------------------------------------------------------

export function useSearchParams(defaultValues) {
  const [searchParams, setSearchParams] = _useSearchParams();

  const searchParamObject = useMemo(() => {
    const obj = {};
    for (const [key, value] of searchParams.entries()) {
      // Check if the key already exists to handle arrays
      if (obj[key]) {
        // If it exists, convert to array if not already
        obj[key] = Array.isArray(obj[key])
          ? [...obj[key], value]
          : [obj[key], value];
      } else {
        // Check defaultValues to determine if this should be an array
        obj[key] =
          defaultValues?.[key] && Array.isArray(defaultValues[key])
            ? [value]
            : value;
      }
    }
    return obj;
  }, [searchParams, defaultValues]);

  const setValue = (v) => {
    const obj = { ...searchParamObject, ...v };
    // Convert the object to URLSearchParams format
    const params = new URLSearchParams();

    Object.entries(obj).forEach(([key, value]) => {
      if (value !== null) {
        if (Array.isArray(value)) {
          // Handle arrays by adding multiple entries with the same key
          value.forEach((item) => params.append(key, item));
        } else {
          params.append(key, value);
        }
      }
    });

    setSearchParams(params, { replace: true });
  };

  // Initialize with default values if URL params are empty
  useEffect(() => {
    if (defaultValues && searchParams.entries().next().done) {
      setValue(defaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return [searchParamObject, setValue];
}
