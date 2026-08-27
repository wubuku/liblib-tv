"use client";

import { useCallback, useEffect, useRef } from "react";
import type {
  FocusEventHandler,
  KeyboardEventHandler,
  PointerEventHandler,
} from "react";
import { useDirectorStore } from "@/store/directorStore";

type DirectorGestureBoundaryOptions = {
  commandKind: string;
  targetId?: string | null;
  fieldScope?: string | null;
};

type DirectorGestureBoundaryHandlers = {
  onFocus: FocusEventHandler<HTMLElement>;
  onBlur: FocusEventHandler<HTMLElement>;
  onPointerDown: PointerEventHandler<HTMLElement>;
  onPointerUp: PointerEventHandler<HTMLElement>;
  onPointerCancel: PointerEventHandler<HTMLElement>;
  onKeyDown: KeyboardEventHandler<HTMLElement>;
};

export function useDirectorGestureBoundary(
  {
    commandKind,
    targetId = null,
    fieldScope = null,
  }: DirectorGestureBoundaryOptions,
): DirectorGestureBoundaryHandlers {
  const activeRef = useRef(false);
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );

  const begin = useCallback(() => {
    if (activeRef.current) return;
    const result = beginDirectorGesture({
      commandKind,
      targetId,
      fieldScope,
    });
    if (result.disposition === "COMMITTED") {
      activeRef.current = true;
    }
  }, [beginDirectorGesture, commandKind, fieldScope, targetId]);

  const commit = useCallback(() => {
    if (!activeRef.current) return;
    activeRef.current = false;
    commitDirectorGesture();
  }, [commitDirectorGesture]);

  const cancel = useCallback(() => {
    if (!activeRef.current) return;
    activeRef.current = false;
    cancelDirectorGesture();
  }, [cancelDirectorGesture]);

  useEffect(() => {
    let previousGesture = useDirectorStore.getState().history.activeGesture;
    return useDirectorStore.subscribe((state) => {
      const nextGesture = state.history.activeGesture;
      if (nextGesture === previousGesture) return;
      previousGesture = nextGesture;
      if (!nextGesture) activeRef.current = false;
    });
  }, []);

  return {
    onFocus: begin,
    onBlur: commit,
    onPointerDown: begin,
    onPointerUp: (event) => {
      if (
        event.currentTarget instanceof HTMLInputElement &&
        event.currentTarget.type === "number"
      ) {
        return;
      }
      commit();
    },
    onPointerCancel: cancel,
    onKeyDown: (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        cancel();
        return;
      }
      if (
        event.key !== "Tab" &&
        event.key !== "Shift" &&
        event.key !== "Alt" &&
        event.key !== "Control" &&
        event.key !== "Meta"
      ) {
        begin();
      }
    },
  };
}
