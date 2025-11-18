import { ReactNode } from "react";

interface AIFoundryLogoProps {
  width?: number | string;
  height?: number | string;
  className?: string;
}

export function AIFoundryLogo({ 
  width = 24, 
  height = 24, 
  className 
}: AIFoundryLogoProps): ReactNode {
  return (
    <svg
      fill="currentColor"
      height={height}
      role="presentation"
      viewBox="0 0 20 20"
      width={width}
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path d="M18.3515 6.60197C18.3515 6.34706 18.1451 6.15283 17.9024 6.15283H15.778C14.2849 6.15283 13.071 7.36673 13.071 8.85983V13.3513H15.6445C17.1376 13.3513 18.3515 12.1374 18.3515 10.6443V6.60197Z" />
      <path
        clipRule="evenodd"
        d="M12.3185 1.00586L12.2457 15.3906C12.2457 17.3814 10.6312 18.9959 8.64039 18.9959H2.09747C1.78186 18.9959 1.5755 18.6924 1.67261 18.401L6.91666 3.42152C7.42649 1.97698 8.78606 1.00586 10.3156 1.00586H12.3185Z"
        fillRule="evenodd"
      />
    </svg>
  );
}
