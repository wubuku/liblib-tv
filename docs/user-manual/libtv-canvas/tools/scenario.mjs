// 取证场景运行器 —— 把「点开某个面板 → 记录真实文案 → 拍图」这件事标准化。
//
// 为什么要有这个：前面每个探针都在重复写「开面板 / dump 文本 / 截图 / 关掉」。
// 复用它的收益是证据格式统一，能直接喂给 task-inventory 与 AUDIT。
import { mkdir, writeFile, appendFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { closePromos, shot, shotHighlighted, injectHighlight } from './lib.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const EV = resolve(HERE, '.evidence');

/** 开始一个批次，写 .evidence/<batch>.json 头。 */
export async function beginBatch(batch, meta) {
  await mkdir(EV, { recursive: true });
  const file = resolve(EV, `${batch}.json`);
  await writeFile(file, JSON.stringify({ batch, started: new Date().toISOString(), meta, steps: [] }, null, 2));
  return file;
}

export async function logStep(batch, step) {
  const file = resolve(EV, `${batch}.json`);
  const raw = JSON.parse(await (await import('node:fs/promises')).readFile(file, 'utf8'));
  raw.steps.push(step);
  await writeFile(file, JSON.stringify(raw, null, 2));
  console.log(`\n### ${step.id} — ${step.title}`);
  if (step.target) console.log('  locator:', step.target);
  if (step.visible_text) console.log('  text   :', String(step.visible_text).replace(/\s+/g, ' ').slice(0, 1400));
  if (step.evidence) console.log('  evidence:', JSON.stringify(step.evidence).slice(0, 900));
  if (step.shot) console.log('  shot   :', step.shot);
  return step;
}

/** 关掉「知道了 / 关闭浏览器通知提示」这类一次性提示，保证画面干净。 */
export async function clearToasts(page) {
  for (let i = 0; i < 3; i += 1) {
    let hit = false;
    for (const n of ['知道了', '关闭浏览器通知提示']) {
      const b = page.getByRole('button', { name: n, exact: true });
      if (await b.count()) { await b.first().click({ timeout: 2000 }).catch(() => {}); hit = true; await page.waitForTimeout(250); }
    }
    if (!hit) break;
  }
}

/** 只读地把「视口里新出现的、带文字的面板级元素」找出来（DOM 差集法，不猜 class）。 */
export async function fingerprint(page) {
  return page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return r.width > 120 && r.height > 60 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05;
    };
    const out = [];
    for (const el of document.querySelectorAll('div,section,aside,ul,nav,[role="dialog"],[role="menu"],[role="listbox"]')) {
      if (!vis(el)) continue;
      const r = el.getBoundingClientRect();
      out.push({
        sig: `${el.tagName}|${(el.className || '').toString().slice(0, 40)}|${Math.round(r.x)},${Math.round(r.y)}`,
        all: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 1600),
        area: Math.round(r.width * r.height),
        buttons: [...el.querySelectorAll('button,[role="menuitem"],[role="option"],a')]
          .filter((b) => { const br = b.getBoundingClientRect(); return br.width > 1 && br.height > 1; })
          .map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 24))
          .filter(Boolean).slice(0, 40),
      });
    }
    return out;
  });
}

export function diffPanels(before, after) {
  const seen = new Set(before.map((b) => b.sig));
  return after.filter((a) => !seen.has(a.sig)).sort((a, b) => a.area - b.area);
}

export { closePromos, shot, shotHighlighted, injectHighlight };
