import { useCallback, useRef } from "react";

/**
 * Custom hook to debounce filter updates and prevent race conditions
 * @param {Function} updateFunction - The function to call for updates
 * @param {number} delay - Debounce delay in milliseconds (default: 300)
 * @returns {Function} - Debounced update function
 */
export const useDebouncedFilterUpdate = (updateFunction, delay = 300) => {
  const timeoutRef = useRef(null);

  const debouncedUpdate = useCallback(
    (...args) => {
      // Clear previous timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        updateFunction(...args);
        timeoutRef.current = null;
      }, delay);
    },
    [updateFunction, delay],
  );

  // Cleanup function to clear timeout on unmount
  // const clearPendingUpdate = useCallback(() => {
  //   if (timeoutRef.current) {
  //     clearTimeout(timeoutRef.current);
  //     timeoutRef.current = null;
  //   }
  // }, []);

  return debouncedUpdate;
};

export default useDebouncedFilterUpdate;
