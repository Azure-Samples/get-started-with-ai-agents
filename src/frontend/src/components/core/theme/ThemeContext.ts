import { createContext, useContext } from "react";
import { Theme as FluentTheme } from "@fluentui/react-components";
import { lightTheme } from "./themes";

export type Theme = "Light" | "Dark" | "System";

export interface IThemeContextValue {
  theme: Theme;
  savedTheme: Theme;
  currentTheme: "Light" | "Dark";
  themeStyles: FluentTheme;
  setTheme: (theme: Theme) => void;
  isDarkMode: boolean;
}

export const ThemeContext = createContext<IThemeContextValue>({
  theme: "Light",
  savedTheme: "Light",
  currentTheme: "Light",
  themeStyles: lightTheme,
  setTheme(theme: Theme) {
    console.log(`Theme set to ${theme}`);
  },
  isDarkMode: false,
});

export function useThemeContext(): IThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useThemeContext must be used within a ThemeProvider");
  }
  return context;
}
