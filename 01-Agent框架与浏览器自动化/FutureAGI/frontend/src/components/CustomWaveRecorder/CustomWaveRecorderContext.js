import { createContext } from "react";

const CustomWaveRecorderContext = createContext({
  isRecording: false,
  setIsRecording: () => {},
  recordedAudio: null,
  setRecordedAudio: () => {},
});

export default CustomWaveRecorderContext;
