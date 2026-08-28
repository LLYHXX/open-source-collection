import { createContext, useContext } from "react";
import logger from "src/utils/logger";

const SaveDraftContext = createContext(null);

const noop = () => {};

// Fallback used when components render outside SaveDraftProvider (e.g. changelog,
// preview pages). ensureDraft returns false to block mutations — any code that
// calls ensureDraft without a provider will not proceed with the write path.
const fallback = {
  saveDraft: noop,
  ensureDraft: async () => {
    logger.warn(
      "[SaveDraftContext] ensureDraft called outside SaveDraftProvider — mutation blocked",
    );
    return false;
  },
  promoteDraft: noop,
};

export const useSaveDraftContext = () => {
  const ctx = useContext(SaveDraftContext);
  return ctx ?? fallback;
};

export default SaveDraftContext;
