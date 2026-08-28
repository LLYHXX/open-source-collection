import { create } from "zustand";

export const useCallLogsSideDrawerStore = create((set) => ({
  callLogsSideDrawerData: null,
  setCallLogsSideDrawerData: (data) => set({ callLogsSideDrawerData: data }),
  resetCallLogsSideDrawer: () => {
    set({
      callLogsSideDrawerData: null,
    });
  },
}));
