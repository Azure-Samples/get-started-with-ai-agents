import { useCallback, useEffect, useState } from "react";
import { IThemeContextValue, Theme } from "./ThemeContext";
import { darkTheme, lightTheme } from "./themes";

const LOCAL_STORAGE_THEME_KEY = "get-started-with-agents-app-theme-preference";

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== "undefined") {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia(query);
      const updateMatches = () => {
        setMatches(mediaQuery.matches);
      };

      mediaQuery.addEventListener("change", updateMatches);

      updateMatches();
      return () => {
        mediaQuery.removeEventListener("change", updateMatches);
      };
    }
    return () => {
      // Cleanup if needed
    };
  }, [query]);

  return matches;
}

export const useThemeProvider = (): IThemeContextValue => {
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");

  const [savedTheme, setSavedTheme] = useState<Theme>(() => {
    if (typeof localStorage !== "undefined") {
      const storedTheme = localStorage.getItem(
        LOCAL_STORAGE_THEME_KEY
      ) as Theme;
      if (storedTheme && ["Light", "Dark", "System"].includes(storedTheme)) {
        return storedTheme;
      }
    }
    return "System";
  });

  const isDarkMode =
    savedTheme === "System" ? prefersDark : savedTheme === "Dark";

  const currentTheme = isDarkMode ? "Dark" : "Light";

  const themeStyles = isDarkMode ? darkTheme : lightTheme;

  const setTheme = useCallback((newTheme: Theme) => {
    setSavedTheme(newTheme);
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(LOCAL_STORAGE_THEME_KEY, newTheme);
    }
  }, []);

  useEffect(() => {
    // Update document color scheme for browser UI
    if (typeof document !== "undefined") {
      document.documentElement.style.colorScheme = isDarkMode
        ? "dark"
        : "light";
    }
  }, [isDarkMode]);

  return {
    theme: savedTheme,
    savedTheme,
    currentTheme,
    themeStyles,
    setTheme,
    isDarkMode,
  };
};
