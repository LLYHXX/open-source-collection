import React from "react";
import PropTypes from "prop-types";
import SaveDraftContext from "./saveDraftContext";
import useSaveDraft from "./hooks/useSaveDraft";

export default function SaveDraftProvider({ children, onCreateDraft }) {
  const { saveDraft, ensureDraft, promoteDraft } = useSaveDraft({
    onCreateDraft,
  });

  return (
    <SaveDraftContext.Provider value={{ saveDraft, ensureDraft, promoteDraft }}>
      {children}
    </SaveDraftContext.Provider>
  );
}

SaveDraftProvider.propTypes = {
  children: PropTypes.node.isRequired,
  onCreateDraft: PropTypes.func,
};
