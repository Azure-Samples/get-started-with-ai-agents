import { useMediaQuery } from "../../core/theme/useThemeProvider";

/**
 * Hook to detect if the user has requested reduced motion
 * via their operating system preferences.
 *
 * @returns A boolean indicating whether reduced motion is enabled
 *
 * @example
 * ```tsx
 * const isMotionReduced = useIsMotionReduced();
 *
 * return (
 *   <div>
 *     {isMotionReduced
 *       ? <StaticComponent />
 *       : <AnimatedComponent />}
 *   </div>
 * );
 * ```
 */
export function useIsMotionReduced(): boolean {
  // Media query to detect if motion is NOT reduced
  // If this query matches, the user has not requested reduced motion
  // We invert the logic - if "no-preference" matches, motion is NOT reduced.
  // This is for backward compatibility with older browsers that may not support the media query
  // and to ensure we default to reduced motion when SSR is involved.
  const mediaQuery = '(prefers-reduced-motion: no-preference)';

  return !useMediaQuery(mediaQuery);
}
