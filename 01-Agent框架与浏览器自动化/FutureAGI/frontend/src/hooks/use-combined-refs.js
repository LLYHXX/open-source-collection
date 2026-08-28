import { useCallback } from "react";

function setRef(ref, value) {
  if (typeof ref === "function") {
    const cleanup = ref(value);
    if (typeof cleanup === "function") {
      return cleanup;
    }
    return () => ref(null); // fallback cleanup for functions without cleanup
  } else if (ref) {
    ref.current = value;
    return () => {
      ref.current = null;
    }; // cleanup for ref objects
  }
  return undefined;
}

export function useCombinedRefs(...refs) {
  return useCallback(
    (value) => {
      const cleanups = refs.map((ref) => setRef(ref, value)).filter(Boolean);
      return () => {
        cleanups.forEach((cleanup) => {
          if (typeof cleanup === "function") {
            cleanup();
          }
        });
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...refs],
  );
}
