import { useEffect, useRef, useState } from "react";

export function useInView({
  threshold = 0.1,
  root = null,
  rootMargin = "0px",
  triggerOnce = false,
} = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          if (triggerOnce) observer.disconnect();
        } else if (!triggerOnce) {
          setInView(false);
        }
      },
      { threshold, root, rootMargin },
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [threshold, root, rootMargin, triggerOnce]);

  return [ref, inView];
}
