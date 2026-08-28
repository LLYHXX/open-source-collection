import { useContext } from "react";
import { AudioPlaybackContext } from "./AudioPlaybackContext";

export const useAudioPlayback = () => useContext(AudioPlaybackContext);
