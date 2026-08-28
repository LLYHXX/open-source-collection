import { useState, useCallback, useEffect } from "react";

export const DEFAULT_WIDTH = 450;
export const MIN_WIDTH = 450;
export const MAX_WIDTH = 800;

/**
 * Hook to manage NodeDrawer resize state
 * Provides width state, resize handlers, and computed offset for other components
 */
export default function useNodeDrawerResize(isOpen) {
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);

  // Handle mouse move for resizing
  // No need to guard `isResizing` — this listener is only attached when `isResizing` is true
  const handleMouseMove = useCallback((e) => {
    const newWidth = window.innerWidth - e.clientX;
    const clampedWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
    setWidth(clampedWidth);
  }, []);

  // Handle mouse up to stop resizing
  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Set up global event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  const handleResizeStart = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  // Computed offset for positioning other elements (like GlobalVariablePanel)
  const drawerOffset = isOpen ? width : 0;

  return {
    width,
    isResizing,
    handleResizeStart,
    drawerOffset,
  };
}
