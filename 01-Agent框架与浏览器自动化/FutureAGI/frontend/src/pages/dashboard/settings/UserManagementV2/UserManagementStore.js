import { create } from "zustand";

export const useUserManagementStore = create((set) => ({
  usersList: [],
  setUsersList: (newUsersList) => set({ usersList: newUsersList }),
}));
