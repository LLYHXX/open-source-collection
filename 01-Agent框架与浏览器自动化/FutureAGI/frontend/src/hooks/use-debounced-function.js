import { useCallback, useRef, useEffect } from "react";

export const useDebouncedFunction = (
  mutationFn,
  delay = 1000,
  keySelector = (args) => args[0], // Default to using first argument as key
) => {
  const timeoutMapRef = useRef(new Map());

  const debouncedFn = useCallback(
    (...variables) => {
      const key = keySelector(variables);
      const timeoutId = timeoutMapRef.current.get(key);

      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutMapRef.current.set(
        key,
        setTimeout(() => {
          mutationFn(...variables);
          timeoutMapRef.current.delete(key);
        }, delay),
      );
    },
    [mutationFn, delay, keySelector],
  );

  useEffect(() => {
    const timeoutMap = timeoutMapRef.current;
    return () => {
      // Clear all timeouts on unmount
      timeoutMap.forEach((timeoutId) => {
        clearTimeout(timeoutId);
      });
      timeoutMap.clear();
    };
  }, []);

  return debouncedFn;
};
