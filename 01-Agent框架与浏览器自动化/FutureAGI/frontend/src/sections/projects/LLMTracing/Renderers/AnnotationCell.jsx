import PropTypes from "prop-types";
import React from "react";
import AnnotationValues from "src/components/traceDetailDrawer/CustomRenderer/AnnotationValues";

const AnnotationCell = ({ value, column }) => {
  return (
    <AnnotationValues
      value={value}
      annotationType={column?.annotationLabelType}
      maxChips={1}
      settings={column?.settings}
    />
  );
};

export default AnnotationCell;

AnnotationCell.propTypes = {
  value: PropTypes.any,
  column: PropTypes.object,
};
