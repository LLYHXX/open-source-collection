import { useEffect, useRef } from "react";

export const useScrollEnd = (callBack, arr = []) => {
  const ref = useRef(null);
  useEffect(() => {
    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = ref.current;
      if (scrollTop + clientHeight >= scrollHeight - 5) {
        callBack?.();
      }
    };

    const container = ref.current;
    if (container) {
      container.addEventListener("scroll", handleScroll);
    }

    return () => {
      if (container) {
        container.removeEventListener("scroll", handleScroll);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, arr);

  return ref;
};
