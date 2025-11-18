import { useCallback } from 'react';

/**
 * Hook for formatting Date objects into readable date strings
 * @returns A function that formats Date objects
 */
export const useFormatTimestamp = (): ((date: Date | undefined) => string) => {
  return useCallback(
    (date: Date | undefined): string => {
      if (date === undefined) {
        return '';
      }

      // Simple date formatting with time
      return new Intl.DateTimeFormat('en', {
        dateStyle: 'short',
        timeStyle: 'short'
      }).format(date);
    },
    [],
  );
};