import React from "react";
import PropTypes from "prop-types";
import { DrawerContext } from "./replayDrawerContent";

// Provider component
export const DrawerProvider = ({ children, value }) => {
  return (
    <DrawerContext.Provider value={value}>{children}</DrawerContext.Provider>
  );
};

DrawerProvider.propTypes = {
  children: PropTypes.node.isRequired,
  value: PropTypes.object.isRequired,
};
