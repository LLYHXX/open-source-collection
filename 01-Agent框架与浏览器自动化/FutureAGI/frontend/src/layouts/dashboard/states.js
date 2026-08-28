import { create } from "zustand";

export const useCreateWorkspaceModal = create((set) => ({
  open: false,
  setOpen: (value) => set({ open: value }),
}));

export const useCreateOrganizationModal = create((set) => ({
  open: false,
  setOpen: (value) => set({ open: value }),
}));

export const useSettingsOpen = create((set) => ({
  settingOpen: false,
  setSettingOpen: (value) => set({ settingOpen: value }),
}));

export const useGatewayOpen = create((set) => ({
  gatewayOpen: false,
  setGatewayOpen: (value) => set({ gatewayOpen: value }),
}));
