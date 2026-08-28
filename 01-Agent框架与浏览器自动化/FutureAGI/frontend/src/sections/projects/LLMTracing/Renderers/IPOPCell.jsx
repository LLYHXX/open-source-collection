import PropTypes from "prop-types";
import React, { memo, useMemo } from "react";
import _ from "lodash";
import { RenderJSONString } from "../../../../components/custom-json-viewer/CustomJsonViewer";
import { safeParse } from "../../../../utils/utils";

// Custom comparison function - compare normalized string values
// Since valueGetter normalizes objects to JSON strings, we can do simple string comparison
const arePropsEqual = (prevProps, nextProps) => {
  // Handle null/undefined cases
  if (prevProps.value === nextProps.value) return true;
  if (prevProps.value == null || nextProps.value == null) return false;

  // For strings (normalized from objects), direct comparison
  if (
    typeof prevProps.value === "string" &&
    typeof nextProps.value === "string"
  ) {
    return prevProps.value === nextProps.value;
  }

  // Fallback to deep equality for other types
  return _.isEqual(prevProps.value, nextProps.value);
};

const IPOPCell = memo(({ value }) => {
  // valueGetter normalizes objects to JSON strings, so we need to parse them back
  // This ensures stable comparison in AG Grid (strings are compared instead of object references)
  const parsedValue = useMemo(() => {
    if (value === null || value === undefined || value === "") {
      return null;
    }
    // If value is a string, try to parse it (it might be a JSON string from valueGetter)
    if (typeof value === "string") {
      const parsed = safeParse(value);
      // If parsing succeeded and result is an object, use it; otherwise use original string
      return typeof parsed === "object" && parsed !== null ? parsed : value;
    }
    // If value is already an object (fallback case), use it directly
    return value;
  }, [value]);

  // Memoize value type check
  const isObject = useMemo(
    () => typeof parsedValue === "object" && parsedValue !== null,
    [parsedValue],
  );

  // Memoize cell content to prevent recreation
  const cellContent = useMemo(() => {
    if (isObject) {
      return <RenderJSONString val={parsedValue} />;
    }
    return parsedValue;
  }, [isObject, parsedValue]);

  // Early return for null/undefined
  if (parsedValue === null || parsedValue === undefined) {
    return <div className="ipop-cell">-</div>;
  }

  return <div className="ipop-cell">{cellContent}</div>;
}, arePropsEqual);

IPOPCell.displayName = "IPOPCell";

IPOPCell.propTypes = {
  value: PropTypes.any,
};

export default IPOPCell;
