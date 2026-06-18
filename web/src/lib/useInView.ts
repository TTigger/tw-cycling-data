import { useEffect, useRef, useState } from "react";

/** Returns a ref + whether it has scrolled near the viewport yet (latches true
 * once seen). Used to defer loading heavy, below-the-fold data until needed.
 * Falls back to true when IntersectionObserver is unavailable. */
export function useInView<T extends Element>(rootMargin = "300px"): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (inView) return;
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") { setInView(true); return; }
    const obs = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { setInView(true); obs.disconnect(); }
    }, { rootMargin });
    obs.observe(el);
    return () => obs.disconnect();
  }, [inView, rootMargin]);
  return [ref, inView];
}
