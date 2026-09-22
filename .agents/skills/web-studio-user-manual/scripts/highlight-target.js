(() => {
  const ROOT_ID = "__canvas_user_manual_overlay__";

  function clear() {
    document.getElementById(ROOT_ID)?.remove();
  }

  async function show(target, options = {}) {
    if (!(target instanceof Element)) {
      throw new Error("highlight target must be a DOM Element");
    }

    clear();
    target.scrollIntoView({ block: "center", inline: "nearest" });
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );

    const rect = target.getBoundingClientRect();
    const style = getComputedStyle(target);
    const visible =
      rect.width > 0 &&
      rect.height > 0 &&
      rect.bottom > 0 &&
      rect.right > 0 &&
      rect.top < window.innerHeight &&
      rect.left < window.innerWidth &&
      style.visibility !== "hidden" &&
      style.display !== "none" &&
      Number.parseFloat(style.opacity || "1") > 0;
    if (!visible) {
      throw new Error("highlight target is not visibly rendered");
    }

    const left = Math.max(4, rect.left - 4);
    const top = Math.max(4, rect.top - 4);
    const right = Math.min(window.innerWidth - 4, rect.right + 4);
    const bottom = Math.min(window.innerHeight - 4, rect.bottom + 4);

    const root = document.createElement("div");
    root.id = ROOT_ID;
    root.setAttribute("aria-hidden", "true");
    Object.assign(root.style, {
      position: "fixed",
      inset: "0",
      zIndex: "2147483647",
      pointerEvents: "none",
    });

    const border = document.createElement("div");
    Object.assign(border.style, {
      position: "fixed",
      left: `${left}px`,
      top: `${top}px`,
      width: `${Math.max(1, right - left)}px`,
      height: `${Math.max(1, bottom - top)}px`,
      boxSizing: "border-box",
      border: `3px solid ${options.color || "#e02020"}`,
      borderRadius: `${options.radius ?? 6}px`,
      boxShadow: "0 0 0 2px rgba(255,255,255,.95), 0 2px 10px rgba(0,0,0,.35)",
    });

    const badge = document.createElement("div");
    badge.textContent = String(options.step ?? "1");
    Object.assign(badge.style, {
      position: "fixed",
      left: `${Math.max(4, left - 10)}px`,
      top: `${Math.max(4, top - 14)}px`,
      minWidth: "26px",
      height: "26px",
      padding: "0 6px",
      boxSizing: "border-box",
      borderRadius: "13px",
      background: options.color || "#e02020",
      color: "#fff",
      font: "700 15px/26px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      textAlign: "center",
      boxShadow: "0 1px 4px rgba(0,0,0,.4)",
    });

    root.append(border, badge);
    document.documentElement.appendChild(root);
    return {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
    };
  }

  window.canvasUserManualHighlight = { show, clear };
})();
