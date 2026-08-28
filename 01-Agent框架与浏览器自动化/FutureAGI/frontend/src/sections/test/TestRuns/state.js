import { create } from "zustand";
import { useShallow } from "zustand/react/shallow";

const useTestRunSdkStore = create((set) => ({
  sdkCodeOpen: false,
  setSdkCodeOpen: (sdkCodeOpen) => set({ sdkCodeOpen }),
}));

export const useTestRunSdkStoreShallow = (fun) => {
  return useTestRunSdkStore(useShallow(fun));
};
