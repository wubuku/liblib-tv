// e2e/frameos.spec.ts
// Playwright e2e tests for the FrameOS canvas route.
// Requires: npx playwright test (not yet wired — see below for wiring instructions).
//
// Run with:
//   npx playwright test e2e/frameos.spec.ts --headed

import { test, expect } from "@playwright/test";

test.describe("FrameOS canvas", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:3000/frameos/canvas/demo");
    await page.waitForSelector('[data-id="text-1"]');
  });

  test("renders all 7 default nodes with blue dashed edges", async ({ page }) => {
    // All 7 nodes (2 text + 3 video + 2 image)
    const nodes = await page.locator(".frameos-canvas .react-flow__node").count();
    expect(nodes).toBeGreaterThanOrEqual(7);

    // Edges should be blue dashed (stroke-dasharray)
    const firstEdge = page.locator(".react-flow__edge .react-flow__edge-path").first();
    const dashArray = await firstEdge.getAttribute("stroke-dasharray");
    expect(dashArray).toBe("7,5");
  });

  test("selecting a node shows floating-toolbar + prompt-bar", async ({ page }) => {
    // Click text-1
    await page.locator('[data-id="text-1"]').click();
    await page.waitForTimeout(300);

    // Floating toolbar visible
    await expect(page.locator(".floating-toolbar")).toBeVisible();

    // Prompt bar visible
    await expect(page.locator(".canvas-footer-prompt")).toBeVisible();
  });

  test("debug toggle reveals the node detail panel", async ({ page }) => {
    // Click DEBUG
    await page.locator(".debug-toggle").click();
    await page.waitForTimeout(200);

    // Click a node
    await page.locator('[data-id="image-1"]').click();
    await page.waitForTimeout(200);

    // Edit panel should be visible
    await expect(page.locator(".node-edit-panel")).toBeVisible();
  });

  test("right-click on node opens context menu", async ({ page }) => {
    const node = page.locator('[data-id="text-2"]');
    await node.click({ button: "right" });
    await page.waitForTimeout(200);
    // The context menu has a "复制节点" button
    await expect(page.getByText("复制节点")).toBeVisible();
  });

  test("keyboard shortcut Cmd+D duplicates node", async ({ page }) => {
    await page.locator('[data-id="text-1"]').click();
    await page.waitForTimeout(200);
    const before = await page.locator(".frameos-canvas .react-flow__node").count();
    await page.keyboard.press("Control+d");
    await page.waitForTimeout(200);
    const after = await page.locator(".frameos-canvas .react-flow__node").count();
    expect(after).toBe(before + 1);
  });

  test("toolbar buttons open / close help panel", async ({ page }) => {
    // Open help
    await page.keyboard.press("?");
    await page.waitForTimeout(200);
    await expect(page.getByText("快捷键 & 操作指南")).toBeVisible();
    // Close
    await page.keyboard.press("Escape");
    await page.waitForTimeout(200);
    await expect(page.getByText("快捷键 & 操作指南")).not.toBeVisible();
  });
});
