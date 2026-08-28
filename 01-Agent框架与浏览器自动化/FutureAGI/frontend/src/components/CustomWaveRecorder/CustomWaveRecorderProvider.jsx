import React, { useState } from "react";
import PropTypes from "prop-types";
import CustomWaveRecorderContext from "./CustomWaveRecorderContext";
const CustomWaveRecorderProvider = ({ defaultRecording, children }) => {
  const [isRecording, setIsRecording] = useState(defaultRecording ?? false);
  const [recordedAudio, setRecordedAudio] = useState(null);

  return (
    <CustomWaveRecorderContext.Provider
      value={{
        isRecording,
        setIsRecording,
        recordedAudio,
        setRecordedAudio,
      }}
    >
      {children}
    </CustomWaveRecorderContext.Provider>
  );
};

CustomWaveRecorderProvider.propTypes = {
  defaultRecording: PropTypes.bool,
  children: PropTypes.any,
};

export default CustomWaveRecorderProvider;
