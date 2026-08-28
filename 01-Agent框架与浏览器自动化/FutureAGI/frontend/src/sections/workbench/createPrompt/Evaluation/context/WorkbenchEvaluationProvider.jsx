import PropTypes from "prop-types";
import React, { useState } from "react";
import { WorkbenchEvaluationContext } from "./WorkbenchEvaluationContext";
import { usePromptWorkbenchContext } from "../../WorkbenchContext";
import { useUrlState } from "src/routes/hooks/use-url-state";

const WorkbenchEvaluationProvider = ({ children }) => {
  const [compareOpen, setCompareOpen] = useState(false);
  const [showPrompts, setShowPrompts] = useUrlState("showPrompts", false);
  const { selectedVersions } = usePromptWorkbenchContext();
  const [showVariables, setShowVariables] = useUrlState("showVar", true);
  const [isEvalsCompareOpen, setIsEvalsCompareOpen] = useState(false);
  const [isEvaluationDrawerOpen, setIsEvaluationDrawerOpen] = useState(false);
  const [versions, setVersions] = useUrlState("versions", [
    selectedVersions[0].version,
  ]);
  const [variables, setVariables] = useState({});

  return (
    <WorkbenchEvaluationContext.Provider
      value={{
        versions,
        variables,
        setVariables,
        setVersions,
        compareOpen,
        setCompareOpen,
        isEvaluationDrawerOpen,
        setIsEvaluationDrawerOpen,
        showVariables,
        setShowVariables,
        showPrompts,
        setShowPrompts,
        isEvalsCompareOpen,
        setIsEvalsCompareOpen,
      }}
    >
      {children}
    </WorkbenchEvaluationContext.Provider>
  );
};

export default WorkbenchEvaluationProvider;

WorkbenchEvaluationProvider.propTypes = {
  children: PropTypes.node,
};
