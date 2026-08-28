import React, { useRef, useState } from "react";
import { DevelopDetailContext } from "./DevelopDetailContext";
import PropTypes from "prop-types";

const DevelopDetailProvider = ({ children }) => {
  const [diffMode, setDiffMode] = useState(false);
  const actionSourceRef = useRef(null);
  const handleToggleDiffMode = () => {
    setDiffMode((prev) => !prev);
  };

  const setActionSource = (source) => {
    actionSourceRef.current = source;
  };

  const clearActionSource = () => {
    actionSourceRef.current = null;
  };

  const getActionSource = () => actionSourceRef.current;

  const value = {
    diffMode,
    handleToggleDiffMode,
    setActionSource,
    clearActionSource,
    getActionSource,
  };

  return (
    <DevelopDetailContext.Provider value={value}>
      {children}
    </DevelopDetailContext.Provider>
  );
};

DevelopDetailProvider.propTypes = {
  children: PropTypes.node,
};

export default DevelopDetailProvider;
