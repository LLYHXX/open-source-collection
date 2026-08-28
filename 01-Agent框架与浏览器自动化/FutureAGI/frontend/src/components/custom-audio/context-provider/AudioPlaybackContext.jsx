import PropTypes from "prop-types";
import React, { createContext, useMemo, useState } from "react";

export const AudioPlaybackContext = createContext();

export const AudioPlaybackProvider = ({ children }) => {
  const [activePlayer, setActivePlayer] = useState(null);

  const value = useMemo(
    () => ({ activePlayer, setActivePlayer }),
    [activePlayer],
  );

  return (
    <AudioPlaybackContext.Provider value={value}>
      {children}
    </AudioPlaybackContext.Provider>
  );
};

AudioPlaybackProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
