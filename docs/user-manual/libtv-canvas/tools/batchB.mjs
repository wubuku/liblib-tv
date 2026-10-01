// Batch B —— 添加节点面板 + 九类节点的创建与编辑面。
//
// 安全边界：本批只创建**免费**节点（文本节点），其余生成类节点一律只打开配置面板、
// 记录字段后关闭，**绝不点生成/提交**（余额 20 积分，且 SKILL 明令禁止真实生成）。
// 导演台会先在画布建卡再进 3D 工作区，本批只建卡、不进 3D（留给 M6）。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted, fingerprint, diffPanels } from './scenario.mjs';

const B = 'batchB';
await beginBatch(B, { note: '添加节点九类；只创建免费节点，生成类一律只读到提交前一步' });

const { browser, page } = await launch();

const nodeCount = () =>
  page.evaluate(() => document.querySelectorAll('.react-flow__node, [data-id][class*="node"]').length);

async function openPanelFor(loc, settle = 1200) {
  const before = await fingerprint(page);
  await loc.click({ timeout: 6000 });
  await page.waitForTimeout(settle);
  const neu = diffPanels(before, await fingerprint(page));
  return neu.length ? neu[neu.length - 1] : null;
}

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);
  console.log('节点基线数:', await nodeCount());

  // ── B1 添加节点面板全貌
  const addBtn = page.getByRole('button', { name: '添加节点', exact: true }).first();
  await addBtn.click();
  await page.waitForTimeout(1300);
  const addPanel = (await fingerprint(page)).sort((a, b) => b.area - a.area)[0];
  const addItems = await page.evaluate(() => {
    const hosts = [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 180 && r.height > 150 && /智能剪辑/.test(el.innerText || '');
    });
    const host = hosts[hosts.length - 1];
    if (!host) return [];
    return [...host.querySelectorAll('button,[role="menuitem"]')]
      .filter((b) => b.getBoundingClientRect().width > 4)
      .map((b) => ({
        text: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30),
        aria: b.getAttribute('aria-label'),
        rect: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
      }));
  });
  await logStep(B, {
    id: 'B1-add-node-panel', title: '添加节点面板：九类节点 + 添加资源分区',
    target: 'role=button name="添加节点"（底部工具条第一个）',
    visible_text: addPanel?.all,
    evidence: addItems,
    shot: await shot(page, 'B1-add-node-panel.png'),
  });

  // 逐项高亮（给正文配图）
  for (const it of addItems.filter((i) => i.text)) {
    try {
      const loc = page.locator('button').filter({ hasText: new RegExp(`^${it.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) }).first();
      if (await loc.count()) await shotHighlighted(page, loc, `B1-item-${it.text.replace(/[^\w一-龥]/g, '')}.png`, { step: 1 });
    } catch { /* 跳过取不到的项 */ }
  }

  // ── B2 创建文本节点（免费）
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await addBtn.click();
  await page.waitForTimeout(900);
  const textBtn = page.locator('button').filter({ hasText: /^文本/ }).first();
  if (await textBtn.count()) {
    await textBtn.click();
    await page.waitForTimeout(2200);
    console.log('创建文本节点后节点数:', await nodeCount());
    const nodeInfo = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node');
      if (!n) return { none: true };
      const r = n.getBoundingClientRect();
      return {
        text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 300),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        editable: !!n.querySelector('[contenteditable="true"]'),
        inputs: [...n.querySelectorAll('input,textarea')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label'), type: i.type })),
        buttons: [...n.querySelectorAll('button')].map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim()).filter(Boolean),
      };
    });
    await logStep(B, {
      id: 'B2-text-node', title: '文本节点：创建后的样子与可编辑区',
      target: '添加节点 → 文本',
      evidence: { ...nodeInfo, nodeCount: await nodeCount() },
      visible_text: nodeInfo.text,
      shot: await shot(page, 'B2-text-node-created.png'),
    });
  }

  // ── B3 双击画布 = 同一个添加节点面板（研究记录如此，实测确认）
  await page.mouse.dblclick(700, 420);
  await page.waitForTimeout(1400);
  const dblPanel = (await fingerprint(page)).sort((a, b) => b.area - a.area)[0];
  await logStep(B, {
    id: 'B3-dblclick-empty', title: '双击画布空白处',
    target: '画布空白双击（空画布提示「双击画布 自由生成节点」）',
    visible_text: dblPanel?.all?.slice(0, 400),
    shot: await shot(page, 'B3-dblclick-panel.png'),
  });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);

  // ── B4..B8 生成类节点：只开配置面板，不提交
  const GENERIC = ['图片', '视频', '音频', '脚本'];
  for (const name of GENERIC) {
    await addBtn.click();
    await page.waitForTimeout(900);
    const b = page.locator('button').filter({ hasText: new RegExp(`^${name}`) }).first();
    if (!(await b.count())) { console.log(`节点入口未找到: ${name}`); await page.keyboard.press('Escape'); continue; }
    const panel = await openPanelFor(b, 2200);
    const created = await nodeCount();
    await logStep(B, {
      id: `B4-node-${name}`, title: `${name}节点：创建后的配置面板（未提交生成）`,
      target: `添加节点 → ${name}`,
      evidence: { nodeCountAfter: created },
      visible_text: panel?.all?.slice(0, 1200) || (await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node');
        return n ? (n.innerText || '').replace(/\s+/g, ' ').slice(0, 1200) : null;
      })),
      shot: await shot(page, `B4-node-${name}.png`),
    });
    // 记录该节点面板上的全部可交互控件，供 20-reference 建字段表
    const fields = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node');
      const scope = n || document;
      return {
        inputs: [...scope.querySelectorAll('input,textarea')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label'), val: i.value, type: i.type })).slice(0, 20),
        buttons: [...scope.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || (b.innerText || '').trim().replace(/\s+/g, ' ')).slice(0, 26)).filter(Boolean).slice(0, 30),
        selects: [...scope.querySelectorAll('[role="combobox"],[role="listbox"],[role="radio"],[role="switch"]')].map((e) => (e.getAttribute('aria-label') || (e.innerText || '').trim().replace(/\s+/g, ' ')).slice(0, 30)).slice(0, 20),
      };
    });
    await logStep(B, { id: `B4-node-${name}-fields`, title: `${name}节点字段清单`, evidence: fields });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }
} finally {
  await browser.close();
}
