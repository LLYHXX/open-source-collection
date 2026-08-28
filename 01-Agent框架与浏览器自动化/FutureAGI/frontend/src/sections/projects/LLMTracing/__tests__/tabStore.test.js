import { describe, it, expect, beforeEach } from "vitest";
import { useTabStore, resetTabStore } from "../tabStore";

describe("tabStore", () => {
  beforeEach(() => {
    resetTabStore();
  });

  it("initializes with default state", () => {
    const state = useTabStore.getState();
    expect(state.dirtyConfig).toBeNull();
    expect(state.isDirty).toBe(false);
    expect(state.contextMenuAnchor).toBeNull();
    expect(state.createModalOpen).toBe(false);
    expect(state.editModalView).toBeNull();
    expect(state.editingTabId).toBeNull();
  });

  it("setDirtyConfig updates dirty state", () => {
    useTabStore.getState().setDirtyConfig({ filters: [] });
    expect(useTabStore.getState().dirtyConfig).toEqual({ filters: [] });
    expect(useTabStore.getState().isDirty).toBe(true);
  });

  it("clearDirty resets dirty state", () => {
    useTabStore.getState().setDirtyConfig({ filters: [] });
    useTabStore.getState().clearDirty();
    expect(useTabStore.getState().dirtyConfig).toBeNull();
    expect(useTabStore.getState().isDirty).toBe(false);
  });

  it("openContextMenu sets anchor position and viewId", () => {
    useTabStore.getState().openContextMenu(100, 200, "view-123");
    const anchor = useTabStore.getState().contextMenuAnchor;
    expect(anchor).toEqual({ x: 100, y: 200, viewId: "view-123" });
  });

  it("closeContextMenu clears anchor", () => {
    useTabStore.getState().openContextMenu(100, 200, "view-123");
    useTabStore.getState().closeContextMenu();
    expect(useTabStore.getState().contextMenuAnchor).toBeNull();
  });

  it("openCreateModal sets modal open", () => {
    useTabStore.getState().openCreateModal();
    expect(useTabStore.getState().createModalOpen).toBe(true);
    expect(useTabStore.getState().editModalView).toBeNull();
  });

  it("openEditModal sets modal open with view", () => {
    const view = { id: "123", name: "Test" };
    useTabStore.getState().openEditModal(view);
    expect(useTabStore.getState().createModalOpen).toBe(true);
    expect(useTabStore.getState().editModalView).toEqual(view);
  });

  it("closeCreateModal resets modal state", () => {
    useTabStore.getState().openCreateModal();
    useTabStore.getState().closeCreateModal();
    expect(useTabStore.getState().createModalOpen).toBe(false);
    expect(useTabStore.getState().editModalView).toBeNull();
  });

  it("startRenaming sets editing tab id", () => {
    useTabStore.getState().startRenaming("view-456");
    expect(useTabStore.getState().editingTabId).toBe("view-456");
  });

  it("stopRenaming clears editing tab id", () => {
    useTabStore.getState().startRenaming("view-456");
    useTabStore.getState().stopRenaming();
    expect(useTabStore.getState().editingTabId).toBeNull();
  });

  it("resetTabStore resets everything", () => {
    useTabStore.getState().setDirtyConfig({ filters: [] });
    useTabStore.getState().openContextMenu(1, 2, "v");
    useTabStore.getState().openCreateModal();
    useTabStore.getState().startRenaming("r");

    resetTabStore();

    const state = useTabStore.getState();
    expect(state.dirtyConfig).toBeNull();
    expect(state.isDirty).toBe(false);
    expect(state.contextMenuAnchor).toBeNull();
    expect(state.createModalOpen).toBe(false);
    expect(state.editingTabId).toBeNull();
  });
});
