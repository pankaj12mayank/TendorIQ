'use client';

import { useEffect, useState, type ComponentType } from 'react';

/**
 * Load a client-only module after mount. Avoids top-level next/dynamic chunks
 * that break when Clerk (or other optional deps) are not configured.
 */
export function useLazyClientModule<P extends object>(
  enabled: boolean,
  loader: () => Promise<{ default: ComponentType<P> } | ComponentType<P> | Record<string, ComponentType<P>>>,
  exportName?: string
) {
  const [Component, setComponent] = useState<ComponentType<P> | null>(null);

  useEffect(() => {
    if (!enabled) {
      setComponent(null);
      return;
    }

    let cancelled = false;
    void loader().then((mod) => {
      if (cancelled) return;
      const resolved =
        'default' in mod && mod.default
          ? mod.default
          : exportName
            ? (mod as Record<string, ComponentType<P>>)[exportName]
            : (mod as ComponentType<P>);
      if (resolved) {
        setComponent(() => resolved);
      }
    });

    return () => {
      cancelled = true;
    };
    // loader is intentionally omitted from deps — callers pass inline imports
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, exportName]);

  return Component;
}
