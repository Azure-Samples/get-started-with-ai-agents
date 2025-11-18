/* eslint-disable react/jsx-props-no-spreading -- This is a wrapper component */
import type {
  MenuButtonProps as FluentMenuButtonProps,
  MenuItemProps,
  MenuListProps,
  MenuPopoverProps,
  MenuProps,
  MenuTriggerProps,
} from "@fluentui/react-components";
import type { Key, MouseEvent, MouseEventHandler, ReactNode } from "react";

import {
  MenuButton as FluentMenuButton,
  Menu,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
} from "@fluentui/react-components";
import clsx from "clsx";
import { forwardRef, useCallback } from "react";

import styles from "./MenuButton.module.css";

export interface IMenuItemConfig extends MenuItemProps {
  key: Key;
}

export interface IMenuButtonProps {
  menuButtonText: string;
  menuItems: IMenuItemConfig[];
  menuProps?: MenuProps;
  menuButtonProps?: FluentMenuButtonProps;
  menuTriggerProps?: MenuTriggerProps;
  menuListProps?: MenuListProps;
  menuPopoverProps?: MenuPopoverProps;
}

export const MenuButton = forwardRef<HTMLButtonElement, IMenuButtonProps>(
  (
    {
      menuButtonText,
      menuItems,
      menuProps,
      menuButtonProps,
      menuTriggerProps,
      menuListProps,
      menuPopoverProps,
    },
    ref
  ): ReactNode => {
    const handleMenuButtonClick = useCallback(
      (event: MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => {
        if (menuButtonProps?.onClick) {
          if (event.currentTarget instanceof HTMLButtonElement) {
            (menuButtonProps.onClick as MouseEventHandler<HTMLButtonElement>)(
              event as MouseEvent<HTMLButtonElement>
            );
          } else if (event.currentTarget instanceof HTMLAnchorElement) {
            (menuButtonProps.onClick as MouseEventHandler<HTMLAnchorElement>)(
              event as MouseEvent<HTMLAnchorElement>
            );
          }
        }
      },
      [menuButtonProps]
    );

    const handleMenuItemClick = useCallback(
      (
        event: MouseEvent<HTMLDivElement>,
        onClick: MouseEventHandler<HTMLDivElement> | undefined
      ) => {
        onClick?.(event);
      },
      []
    );

    const {
      shape = "circular",
      appearance = "secondary",
      className,
      ...restMenuButtonProps
    } = menuButtonProps ?? {};

    return (
      <Menu {...menuProps}>
        <MenuTrigger {...menuTriggerProps}>
          <FluentMenuButton
            {...restMenuButtonProps}
            ref={ref}
            appearance={appearance}
            className={clsx(
              appearance === "secondary" && styles.secondary,
              className
            )}
            onClick={handleMenuButtonClick}
            shape={shape}
          >
            {menuButtonText}
          </FluentMenuButton>
        </MenuTrigger>
        <MenuPopover {...menuPopoverProps}>
          <MenuList {...menuListProps}>
            {menuItems.map(({ key, children, onClick, ...itemProps }) => (
              <MenuItem
                key={key}
                onClick={(event) => {
                  handleMenuItemClick(event, onClick);
                }}
                {...itemProps}
              >
                {children}
              </MenuItem>
            ))}
          </MenuList>
        </MenuPopover>
      </Menu>
    );
  }
);
MenuButton.displayName = "MenuButton";
