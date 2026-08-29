"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "area[href]",
  "button",
  "input",
  "select",
  "textarea",
  "iframe",
  "object",
  "embed",
  "[contenteditable='true']",
  "[tabindex]",
].join(",");

function isDisabledElement(element: HTMLElement): boolean {
  if (
    element instanceof HTMLButtonElement ||
    element instanceof HTMLInputElement ||
    element instanceof HTMLSelectElement ||
    element instanceof HTMLTextAreaElement ||
    element instanceof HTMLOptGroupElement ||
    element instanceof HTMLOptionElement
  ) {
    return element.disabled;
  }
  return false;
}

function isHiddenFromFocus(element: HTMLElement): boolean {
  if (element.matches("[hidden], [aria-hidden='true'], [inert]")) return true;
  const hiddenAncestor = element.closest(
    "[hidden], [aria-hidden='true'], [inert]",
  );
  if (hiddenAncestor) return true;
  const styles = window.getComputedStyle(element);
  return styles.display === "none" || styles.visibility === "hidden";
}

export function getDirectorFocusableElements(
  root: HTMLElement,
): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
    .filter((element) => {
      if (element.tabIndex < 0 || isDisabledElement(element)) return false;
      if (element.getAttribute("type") === "hidden") return false;
      return !isHiddenFromFocus(element);
    })
    .filter((element) => element.getClientRects().length > 0);
}

function isFocusableTarget(element: HTMLElement): boolean {
  if (
    !element.isConnected ||
    (element.tabIndex < 0 && !element.hasAttribute("tabindex"))
  ) {
    return false;
  }
  if (isDisabledElement(element) || isHiddenFromFocus(element)) return false;
  return element.getClientRects().length > 0;
}

function focusElement(element: HTMLElement | null): boolean {
  if (!element || !isFocusableTarget(element)) return false;
  element.focus({ preventScroll: true });
  return document.activeElement === element;
}

type DirectorFocusReturnDisposition =
  | "trigger"
  | "canvas-root"
  | "workspace"
  | "unavailable";

interface UseDirectorFocusContainmentOptions {
  rootRef: RefObject<HTMLElement | null>;
  enabled?: boolean;
  initialFocus?: "root" | "first";
  returnFocus?: boolean;
  canvasRootSelector?: string;
  stopPropagation?: boolean;
}

interface UseDirectorFocusContainmentResult {
  restoreFocus: () => DirectorFocusReturnDisposition;
  returnDisposition: DirectorFocusReturnDisposition;
}

export function useDirectorFocusContainment({
  rootRef,
  enabled = true,
  initialFocus = "root",
  returnFocus = false,
  canvasRootSelector = "[data-libtv-canvas-focus-root]",
  stopPropagation = false,
}: UseDirectorFocusContainmentOptions): UseDirectorFocusContainmentResult {
  const returnTargetRef = useRef<HTMLElement | null>(null);
  const [returnDisposition, setReturnDisposition] =
    useState<DirectorFocusReturnDisposition>("unavailable");

  const restoreFocus = useCallback(() => {
    if (focusElement(returnTargetRef.current)) {
      setReturnDisposition("trigger");
      return "trigger" as const;
    }

    const canvasRoot = document.querySelector<HTMLElement>(canvasRootSelector);
    if (focusElement(canvasRoot)) {
      setReturnDisposition("canvas-root");
      return "canvas-root" as const;
    }

    const workspace = rootRef.current;
    if (focusElement(workspace)) {
      setReturnDisposition("workspace");
      return "workspace" as const;
    }

    setReturnDisposition("unavailable");
    return "unavailable" as const;
  }, [canvasRootSelector, rootRef]);

  useEffect(() => {
    if (!enabled) return;
    const root = rootRef.current;
    if (!root) return;

    const activeElement = document.activeElement;
    if (
      activeElement instanceof HTMLElement &&
      !root.contains(activeElement) &&
      activeElement.isConnected
    ) {
      returnTargetRef.current = activeElement;
    }

    const initialFrame = window.requestAnimationFrame(() => {
      if (initialFocus === "first") {
        const first = getDirectorFocusableElements(root)[0] ?? null;
        if (!focusElement(first)) root.focus({ preventScroll: true });
      } else {
        root.focus({ preventScroll: true });
      }
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const focusable = getDirectorFocusableElements(root);
      if (focusable.length === 0) {
        event.preventDefault();
        if (stopPropagation) event.stopPropagation();
        root.focus({ preventScroll: true });
        return;
      }

      const active = document.activeElement;
      const index =
        active instanceof HTMLElement ? focusable.indexOf(active) : -1;
      const nextIndex = event.shiftKey
        ? index <= 0
          ? focusable.length - 1
          : index - 1
        : index < 0 || index === focusable.length - 1
          ? 0
          : index + 1;
      event.preventDefault();
      if (stopPropagation) event.stopPropagation();
      focusable[nextIndex]?.focus({ preventScroll: true });
    };

    root.addEventListener("keydown", handleKeyDown);
    return () => {
      window.cancelAnimationFrame(initialFrame);
      root.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled, initialFocus, rootRef, stopPropagation]);

  useEffect(() => {
    if (!returnFocus) return;
    return () => {
      window.requestAnimationFrame(() => {
        restoreFocus();
      });
    };
  }, [restoreFocus, returnFocus]);

  return { restoreFocus, returnDisposition };
}
