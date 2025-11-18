import { PropsWithChildren } from "react";
import { FluentProvider } from "@fluentui/react-components";
import { ThemeContext } from "./ThemeContext";
import { useThemeProvider } from "./useThemeProvider";

export function ThemeProvider({ children }: PropsWithChildren): JSX.Element {
  const themeContext = useThemeProvider();

  return (
    <ThemeContext.Provider value={themeContext}>
      <FluentProvider theme={themeContext.themeStyles}>
        {children}
      </FluentProvider>
    </ThemeContext.Provider>
  );
}
