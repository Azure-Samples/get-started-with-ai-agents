import {
  BrandVariants,
  createDarkTheme,
  createLightTheme,
  Theme,
} from "@fluentui/react-components";

// Define our brand colors for the theme
const brandColors: BrandVariants = {
  10: "#010306",
  20: "#071926",
  30: "#002A41",
  40: "#003653",
  50: "#004365",
  60: "#005078",
  70: "#005E8B",
  80: "#007BB4",
  90: "#007BB4",
  100: "#008AC9",
  110: "#0099DE",
  120: "#00A8F4",
  130: "#3FB6FF",
  140: "#73C3FF",
  150: "#98D0FF",
  160: "#B8DEFF",
};

export const lightTheme: Theme = {
  ...createLightTheme(brandColors),
};

export const darkTheme: Theme = {
  ...createDarkTheme(brandColors),
  colorBrandForeground1: brandColors[110],
  colorBrandForeground2: brandColors[120],
  colorBrandForegroundLink: brandColors[140],
};
