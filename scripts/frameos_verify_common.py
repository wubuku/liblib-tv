#!/usr/bin/env python3
"""Shared helpers for frameos canvas verifiers.

Batch 253: 抽出 229/232/234/251 各自重复的「框选起点扫描 + 拖拽框选」逻辑,
降低多脚本间的漂移维护成本。行为与抽离前逐字节等价 (同一 JS 扫描与拖拽参数)。
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

# 计算框选几何: 目标节点包围盒 + 纯 pane 起点扫描 (bbox 上方 25px 水平线)
_MARQUEE_BOX_JS = """
((cfg) => {
  const targets = cfg.ids
    .map((id) => document.querySelector('.react-flow__node[data-id=\\'' + id + '\\']')?.getBoundingClientRect())
    .filter(Boolean);
  if (targets.length < cfg.need) {
    const all = [...document.querySelectorAll('.react-flow__node')].map((n) => n.getBoundingClientRect()).slice(0, cfg.need);
    targets.push(...all);
  }
  const minX = Math.min(...targets.map((r) => r.left));
  const minY = Math.min(...targets.map((r) => r.top));
  const maxX = Math.max(...targets.map((r) => r.right));
  const maxY = Math.max(...targets.map((r) => r.bottom));
  // 沿包围盒上方 25px 的水平线扫描, 找到纯 pane 起点
  let start = null;
  for (let x = minX - 20; x <= maxX; x += 12) {
    const y = minY - 25;
    const el = document.elementFromPoint(x, y);
    const extraHit = (cfg.extraExclude || []).some((sel) => el?.closest(sel));
    if (el?.closest('.react-flow__pane') && !el?.closest('.react-flow__node') && !el?.closest('.resize-handle') && !el?.closest('[class*=minimap]') && !el?.closest('button') && !extraHit) {
      start = { x, y };
      break;
    }
  }
  if (!start) start = { x: 150, y: 400 };
  return { start, end: { x: maxX + 15, y: maxY + 15 } };
})"""

_SELECTED_IDS_JS = (
    """[...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id'))"""
)


def marquee_box(
    page: Page,
    data_ids: list[str],
    need: int = 2,
    extra_exclude: list[str] | None = None,
) -> dict[str, Any]:
    """计算框选矩形 (起点已做纯 pane 扫描)。extra_exclude 为额外的 closest 排除选择器。"""
    return page.evaluate(
        _MARQUEE_BOX_JS, {"ids": data_ids, "need": need, "extraExclude": extra_exclude or []}
    )


def marquee_select(
    page: Page,
    data_ids: list[str],
    need: int = 2,
    wait_ms: int = 500,
    steps: int = 8,
    extra_exclude: list[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """执行框选拖拽, 返回 (框选几何, 选中节点 id 列表)。"""
    boxes = marquee_box(page, data_ids, need, extra_exclude)
    page.mouse.move(boxes["start"]["x"], boxes["start"]["y"])
    page.mouse.down()
    for i in range(1, steps + 1):
        x = boxes["start"]["x"] + (boxes["end"]["x"] - boxes["start"]["x"]) * i / steps
        y = boxes["start"]["y"] + (boxes["end"]["y"] - boxes["start"]["y"]) * i / steps
        page.mouse.move(x, y)
    page.mouse.up()
    page.wait_for_timeout(wait_ms)
    selected_ids = page.evaluate(_SELECTED_IDS_JS)
    return boxes, selected_ids


def attach_errors(page: Page) -> list[str]:
    """挂接 console/pageerror/dialog 监听, 返回错误收集列表 (各 verifier 共用)。"""
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.on("dialog", lambda d: d.dismiss())
    return errors


# Batch 334: 画布内容自 Batch 333 起**真的**跨刷新持久化（localStorage）。
# 这对验证器有两重影响，必须显式处理，不能靠「刷新后回到初值」的旧假设：
#   1. 测试隔离 —— 前一个 verifier 留下的节点会被下一个读到
#      （曾导致 batch327 刷新后节点重叠、click 被 intercept 而超时失败）；
#   2. 起点确定 —— 需要「干净起点」时必须显式清空存储。
FRAMEOS_CANVAS_STORAGE_KEY = "frameos.canvasData.v1"
FRAMEOS_DEMO_URL = "http://localhost:4317/frameos/canvas/demo"


def goto_clean_canvas(page: Page, base_url: str | None = None) -> None:
    """打开 demo 画布并**确保存储为空**，使每次验证都从 fixture 初值开始。

    先 goto 一次拿到同源上下文，再清 localStorage，最后 reload 让应用以
    干净状态启动（store 初值 = fixture）。
    """
    import os

    url = f"{(base_url or os.environ.get('LIBLIB_BASE_URL', 'http://localhost:4317'))}/frameos/canvas/demo"
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    page.evaluate(
        "([k]) => { try { localStorage.removeItem(k); } catch {} }",
        [FRAMEOS_CANVAS_STORAGE_KEY],
    )
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(1000)
