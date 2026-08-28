import { useMemo } from "react";
import { useTheme } from "@mui/material";
import {
  getAgTheme,
  getAgThemeWithoutGrid,
  getAgThemePrompt,
} from "src/theme/ag-theme";

export function useAgTheme() {
  const { palette } = useTheme();
  return useMemo(() => getAgTheme(palette.mode), [palette.mode]);
}

export function useAgThemeWithoutGrid() {
  const { palette } = useTheme();
  return useMemo(() => getAgThemeWithoutGrid(palette.mode), [palette.mode]);
}

export function useAgThemePrompt() {
  const { palette } = useTheme();
  return useMemo(() => getAgThemePrompt(palette.mode), [palette.mode]);
}

/**
 * Returns a memoized AG Grid theme with param overrides applied.
 * `params` MUST be a stable reference (module-level constant or from AG_THEME_OVERRIDES).
 */
export function useAgThemeWith(params) {
  const base = useAgTheme();
  return useMemo(() => base.withParams(params), [base, params]);
}

/**
 * Returns a memoized AG Grid "prompt" theme with param overrides applied.
 * `params` MUST be a stable reference (module-level constant or from AG_THEME_OVERRIDES).
 */
export function useAgThemePromptWith(params) {
  const base = useAgThemePrompt();
  return useMemo(() => base.withParams(params), [base, params]);
}

/**
 * Returns a memoized AG Grid "without grid" theme with param overrides applied.
 * `params` MUST be a stable reference (module-level constant or from AG_THEME_OVERRIDES).
 */
export function useAgThemeWithoutGridWith(params) {
  const base = useAgThemeWithoutGrid();
  return useMemo(() => base.withParams(params), [base, params]);
}
