import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import useNodeDrawerResize, {
  DEFAULT_WIDTH,
  MIN_WIDTH,
  MAX_WIDTH,
} from "../useNodeDrawerResize";

describe("useNodeDrawerResize", () => {
  beforeEach(() => {
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  });

  // ---- Initial state ----
  it("returns default width and constants", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    expect(result.current.width).toBe(450);
    expect(result.current.isResizing).toBe(false);
    expect(DEFAULT_WIDTH).toBe(450);
    expect(MIN_WIDTH).toBe(450);
    expect(MAX_WIDTH).toBe(800);
  });

  // ---- drawerOffset ----
  it("returns width as drawerOffset when open", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));
    expect(result.current.drawerOffset).toBe(450);
  });

  it("returns 0 as drawerOffset when closed", () => {
    const { result } = renderHook(() => useNodeDrawerResize(false));
    expect(result.current.drawerOffset).toBe(0);
  });

  // ---- Resize start ----
  it("sets isResizing to true on handleResizeStart", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    expect(result.current.isResizing).toBe(true);
  });

  it("sets cursor to col-resize when resizing", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    expect(document.body.style.cursor).toBe("col-resize");
    expect(document.body.style.userSelect).toBe("none");
  });

  // ---- Mouse move clamping ----
  it("clamps width to MIN_WIDTH when mouse moves far right", () => {
    // Simulate window.innerWidth = 1024
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });

    const { result } = renderHook(() => useNodeDrawerResize(true));

    // Start resizing
    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    // Mouse at far right (clientX = 900) → newWidth = 1024 - 900 = 124 → clamped to 450
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 900 }));
    });

    expect(result.current.width).toBe(450);
  });

  it("clamps width to MAX_WIDTH when mouse moves far left", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });

    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    // Mouse at far left (clientX = 0) → newWidth = 1024 → clamped to 800
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 0 }));
    });

    expect(result.current.width).toBe(800);
  });

  it("sets width within bounds on valid mouse position", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });

    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    // Mouse at clientX = 424 → newWidth = 1024 - 424 = 600
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 424 }));
    });

    expect(result.current.width).toBe(600);
  });

  // ---- Mouse move ignored when not resizing ----
  it("ignores mouse move when not resizing", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });

    const { result } = renderHook(() => useNodeDrawerResize(true));

    // Don't start resizing — just fire a move event
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 424 }));
    });

    // Width should remain at default
    expect(result.current.width).toBe(450);
  });

  // ---- Mouse up stops resizing ----
  it("stops resizing on mouseup", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });
    expect(result.current.isResizing).toBe(true);

    act(() => {
      document.dispatchEvent(new MouseEvent("mouseup"));
    });
    expect(result.current.isResizing).toBe(false);
  });

  it("resets cursor styles on mouseup", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mouseup"));
    });

    expect(document.body.style.cursor).toBe("");
    expect(document.body.style.userSelect).toBe("");
  });

  // ---- Cleanup on unmount ----
  it("cleans up event listeners and styles on unmount", () => {
    const { result, unmount } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    unmount();

    expect(document.body.style.cursor).toBe("");
    expect(document.body.style.userSelect).toBe("");
  });
});

describe("useNodeDrawerResize – edge cases", () => {
  beforeEach(() => {
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });
  });

  // ---- Exact boundary values ----
  it("sets width to exactly MIN_WIDTH (450) when computed width equals 450", () => {
    // clientX = 1024 - 450 = 574
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 574 }));
    });

    expect(result.current.width).toBe(450);
  });

  it("sets width to 451 (one above MIN_WIDTH) without clamping", () => {
    // clientX = 1024 - 451 = 573
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 573 }));
    });

    expect(result.current.width).toBe(451);
  });

  it("sets width to 799 (one below MAX_WIDTH) without clamping", () => {
    // clientX = 1024 - 799 = 225
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 225 }));
    });

    expect(result.current.width).toBe(799);
  });

  it("sets width to exactly MAX_WIDTH (800) when computed width equals 800", () => {
    // clientX = 1024 - 800 = 224
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 224 }));
    });

    expect(result.current.width).toBe(800);
  });

  it("clamps to MAX_WIDTH when computed width is 801 (one above MAX)", () => {
    // clientX = 1024 - 801 = 223
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 223 }));
    });

    expect(result.current.width).toBe(800);
  });

  it("clamps to MIN_WIDTH when computed width is 449 (one below MIN)", () => {
    // clientX = 1024 - 449 = 575
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 575 }));
    });

    expect(result.current.width).toBe(450);
  });

  // ---- Window innerWidth changes mid-drag ----
  it("respects window.innerWidth change mid-drag", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    // First move with innerWidth = 1024, clientX = 424 → width = 600
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 424 }));
    });
    expect(result.current.width).toBe(600);

    // Simulate window resize to a smaller viewport mid-drag
    window.innerWidth = 800;

    // Same clientX = 424 → newWidth = 800 - 424 = 376 → clamped to 450
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 424 }));
    });
    expect(result.current.width).toBe(450);
  });

  it("uses updated window.innerWidth for MAX clamping mid-drag", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    // Expand viewport mid-drag
    window.innerWidth = 2000;

    // clientX = 1100 → newWidth = 2000 - 1100 = 900 → clamped to 800
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 1100 }));
    });
    expect(result.current.width).toBe(800);
  });

  // ---- handleResizeStart with event missing preventDefault ----
  it("throws when handleResizeStart receives an event without preventDefault", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    expect(() => {
      act(() => {
        result.current.handleResizeStart({});
      });
    }).toThrow();
  });

  it("does not set isResizing when handleResizeStart throws due to missing preventDefault", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    try {
      act(() => {
        result.current.handleResizeStart({});
      });
    } catch {
      // expected
    }

    expect(result.current.isResizing).toBe(false);
  });

  // ---- drawerOffset reflects resized width ----
  it("drawerOffset reflects the resized width when open", () => {
    const { result } = renderHook(() => useNodeDrawerResize(true));

    act(() => {
      result.current.handleResizeStart({ preventDefault: () => {} });
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 424 }));
    });

    expect(result.current.drawerOffset).toBe(600);
  });

  it("drawerOffset remains 0 when closed regardless of width", () => {
    const { result } = renderHook(() => useNodeDrawerResize(false));

    expect(result.current.drawerOffset).toBe(0);
    expect(result.current.width).toBe(450);
  });
});
