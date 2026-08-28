import PropTypes from "prop-types";
import React from "react";

export const ShowComponent = ({ condition, children }) => {
  return condition ? children : <></>;
};

ShowComponent.propTypes = {
  condition: PropTypes.bool,
  children: PropTypes.node,
};
