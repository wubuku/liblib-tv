// Batch G —— 把「从来没打开过的面板」一次开完。
//
// 翻了一遍全站可点的东西，发现下面这些在前面 6 个批次里**一次都没进去过**，
// 而它们全都是画布日常操作的一部分：
//
//   G1 生成历史（底部工具条）      G2 资产管理（左下角）
//   G3 小地图（切换小地图开关）    G4 节点里的「高级设置」展开
//   G5 工具箱（素材库面板里的「打开工具箱」）
//   G6 组操作条的「添加到工具箱」/「布局下拉」（batchF F2 定位失败，这轮换按坐标找）
//
// 安全边界：全程只读。不点任何生成、不提交表单、不上传、不删。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchG';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

/** 打开一个面板后，把「相对打开之前新出现的可交互元素」整个读出来。 */
async function panelSnapshot(minW = 200, minH = 150) {
  return page.evaluate(([mw, mh]) => {
    const cands = [...document.querySelectorAll('div,section,aside')]
      .filter((e) => { const r = e.getBoundingClientRect();
        return r.width >= mw && r.height >= mh && (e.innerText || '').trim().length > 8; })
      .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
                    - (a.getBoundingClientRect().width * a.getBoundingClientRect().height));
    if (!cands.length) return null;
    const host = cands[0];
    const r = host.getBoundingClientRect();
    const txt = (host.innerText || '').replace(/\s+/g, ' ').trim();
    return {
      cls: (host.className || '').toString().slice(0, 70),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: txt.slice(0, 900),
      charCount: txt.length,
      buttons: [...host.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"],[role="option"]')]
        .filter((b) => b.getBoundingClientRect().width > 0)
        .map((b) => (b.getAttribute('aria-label') || b.title || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 18))
        .filter(Boolean).slice(0, 40),
      inputs: [...host.querySelectorAll('input,textarea')]
        .filter((i) => i.getBoundingClientRect().width > 0)
        .map((i) => i.getAttribute('aria-label') || i.placeholder || '(无标签)').slice(0, 12),
      tabs: [...host.querySelectorAll('[role="tab"]')].filter((t) => t.getBoundingClientRect().width > 0)
        .map((t) => ({ t: (t.getAttribute('aria-label') || t.innerText || '').trim().slice(0, 14), sel: t.getAttribute('aria-selected') })),
    };
  }, [minW, minH]);
}

/** 页面上有没有长这样的大浮层（用来判断「面板到底开没开」）。 */
const hasOverlay = () => page.evaluate(() =>
  [...document.querySelectorAll('div,section')].some((e) => {
    const r = e.getBoundingClientRect();
    return r.width >= window.innerWidth * 0.6 && r.height >= window.innerHeight * 0.5
      && getComputedStyle(e).visibility !== 'hidden' && +getComputedStyle(e).opacity > 0.05;
  }));

async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}
async function safe(id, title, target, fn) {
  try { await fn(); } catch (e) {
    console.log(`  ✗ ${id}: ${String(e).split('\n')[0].slice(0, 160)}`);
    await logStep(B, { id, title, target, failed: true, visible_text: `执行抛错：${String(e).split('\n')[0].slice(0, 300)}` });
  }
}
/** 关掉可能挡住下一次的浮层：Esc → 点遮罩 → 找「关闭」。 */
async function dismiss() {
  for (let i = 0; i < 3; i += 1) {
    if (!(await hasOverlay())) break;
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(700);
    if (!(await hasOverlay())) break;
    const c = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button,[role="button"]')]
        .filter((x) => x.getBoundingClientRect().width > 0)
        .map((x) => ({ t: (x.getAttribute('aria-label') || x.title || '').trim(), x: Math.round(x.getBoundingClientRect().x), y: Math.round(x.getBoundingClientRect().y) }))
        .find((x) => /^(关闭|Close|取消)$/i.test(x.t));
      return b || null;
    });
    if (c) { await page.mouse.click(c.x + 7, c.y + 7); await page.waitForTimeout(900); }
  }
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '补齐六个从未打开过的面板：生成历史 / 资产管理 / 小地图 / 高级设置 / 工具箱 / 组操作条菜单' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(400, 300, '图片');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);
  console.log('节点:', JSON.stringify(await nodesOf()));

  // ── G1 生成历史
  await safe('G1-history', '生成历史面板', '点底部工具条「生成历史」', async () => {
    await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(3000);
    const snap = await panelSnapshot();
    await shot(page, 'M-01-生成历史.png');
    await logStep(B, { id: 'G1-history', title: '生成历史面板', target: '点底部工具条「生成历史」',
      evidence: { overlay: await hasOverlay(), panel: snap },
      visible_text: snap ? `浮层 ${JSON.stringify(snap.rect)}；文案 ${JSON.stringify(snap.text.slice(0, 300))}；按钮 ${JSON.stringify(snap.buttons)}` : '没找到面板',
      shot: 'M-01-生成历史.png' });
    await dismiss();
  });

  // ── G2 资产管理（左下角）
  await safe('G2-asset-management', '资产管理面板', '点左下角「资产管理」', async () => {
    await page.getByRole('button', { name: '资产管理', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(3000);
    const snap = await panelSnapshot();
    await shot(page, 'M-02-资产管理.png');
    await logStep(B, { id: 'G2-asset-management', title: '资产管理面板', target: '点左下角「资产管理」',
      evidence: { overlay: await hasOverlay(), panel: snap, url: page.url() },
      visible_text: snap ? `浮层 ${JSON.stringify(snap.rect)}；文案 ${JSON.stringify(snap.text.slice(0, 300))}；按钮 ${JSON.stringify(snap.buttons)}` : '没找到面板',
      shot: 'M-02-资产管理.png' });
    await dismiss();
  });

  // ── G3 小地图
  await safe('G3-minimap', '小地图', '点左下角「切换小地图」', async () => {
    const before = await page.evaluate(() => ({
      minimapSel: !!document.querySelector('.react-flow__minimap'),
      aria: (document.querySelector('button[aria-label="切换小地图"]') || {}).getAttribute?.('aria-pressed') || null,
    }));
    await page.getByRole('button', { name: '切换小地图', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2200);
    const after = await page.evaluate(() => {
      const m = document.querySelector('.react-flow__minimap');
      if (!m) return { exists: false };
      const r = m.getBoundingClientRect();
      return { exists: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        nodes: m.querySelectorAll('.react-flow__minimap-node').length,
        cls: (m.className || '').toString().slice(0, 60) };
    });
    await shot(page, 'M-03-小地图.png');
    await logStep(B, { id: 'G3-minimap', title: '小地图', target: '点左下角「切换小地图」',
      evidence: { before, after },
      visible_text: `点之前 ${JSON.stringify(before)}；点之后 ${JSON.stringify(after)}`, shot: 'M-03-小地图.png' });
    // 点回去，恢复默认
    await page.getByRole('button', { name: '切换小地图', exact: true }).first().click({ timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(1200);
  });

  // ── G4 节点里的「高级设置」展开
  await safe('G4-advanced-settings', '节点里的「高级设置」', '选中图片节点后展开它的「高级设置」', async () => {
    const f = (await nodesOf())[0];
    await page.mouse.click(f.x + Math.min(80, f.w / 2), f.y + 12);
    await page.waitForTimeout(1200);
    const before = await page.evaluate(() => (document.querySelector('.react-flow__node.selected')?.innerText || '').replace(/\s+/g, ' ').slice(0, 400));
    const adv = page.getByRole('button', { name: /高级设置/ }).first();
    const found = await adv.count();
    let after = null;
    if (found) {
      await adv.click({ timeout: 5000 });
      await page.waitForTimeout(1800);
      after = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 700),
          h: Math.round(r.height),
          controls: [...n.querySelectorAll('input,select,textarea,[role="slider"],[role="switch"]')]
            .filter((e) => e.getBoundingClientRect().width > 0)
            .map((e) => ({ tag: e.tagName.toLowerCase(), type: e.getAttribute('type') || e.getAttribute('role') || '',
              t: (e.getAttribute('aria-label') || e.placeholder || e.closest('label')?.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16) })).slice(0, 20) };
      });
    }
    await shot(page, 'M-04-图片节点-高级设置.png');
    await logStep(B, { id: 'G4-advanced-settings', title: '节点里的「高级设置」', target: '选中图片节点 → 点「高级设置」',
      evidence: { buttonFound: found, nodeTextBefore: before, nodeTextAfter: after?.text, nodeHeightAfter: after?.h, controls: after?.controls },
      visible_text: `「高级设置」按钮 ${found ? '有' : '无'}；展开后节点文本 ${JSON.stringify(after?.text?.slice(0, 400))}；控件 ${JSON.stringify(after?.controls)}`,
      shot: 'M-04-图片节点-高级设置.png' });
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(800);
  });

  // ── G5 工具箱（从素材库面板的「打开工具箱」进）
  await safe('G5-toolbox', '工具箱', '点「素材库」→「打开工具箱」', async () => {
    await page.getByRole('button', { name: '素材库', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2000);
    const opener = page.getByText('打开工具箱', { exact: true }).first();
    const found = await opener.count();
    if (!found) throw new Error('素材库面板里找不到「打开工具箱」');
    await opener.click({ timeout: 5000 });
    await page.waitForTimeout(3000);
    const snap = await panelSnapshot();
    await shot(page, 'M-05-工具箱.png');
    await logStep(B, { id: 'G5-toolbox', title: '工具箱', target: '点「素材库」→「打开工具箱」',
      evidence: { openerFound: found, overlay: await hasOverlay(), panel: snap, url: page.url() },
      visible_text: snap ? `文案 ${JSON.stringify(snap.text.slice(0, 400))}；按钮 ${JSON.stringify(snap.buttons)}` : '没找到面板',
      shot: 'M-05-工具箱.png' });
    await dismiss();
  });

  // ── G6 组操作条剩下的两个动作（这轮按坐标找，不靠文案）
  await safe('G6-group-actions', '组操作条「添加到工具箱」与「布局下拉」', '成组后读出操作条每一枚动作的坐标，再逐个点开只读', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    await addNodeAt(300, 300, '文本');
    await addNodeAt(1000, 300, '音频');
    await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);
    const plain = (await nodesOf()).filter((n) => !n.isGroup);
    const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
    const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
    await page.keyboard.down('Shift');
    await page.mouse.move(40, 80); await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1300);
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);

    // 组操作条上所有叶子元素（没有子元素的 div/span），按 x 排序 —— 这就是每一枚动作
    const leaves = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const r = g.getBoundingClientRect();
      return [...g.querySelectorAll('div,span')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 60 && !e.querySelector('div,span');
      }).map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
          x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
          w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity }; })
        .sort((a, b) => a.x - b.x);
    });
    console.log('  组操作条叶子元素:', JSON.stringify(leaves));

    const results = [];
    for (const c of leaves || []) {
      if (c.w > 200) continue;              // 跳过整条容器
      if (c.t === '整组执行') { results.push({ ...c, opened: 'SKIPPED（会跑生成、扣积分）' }); continue; }
      await page.mouse.click(c.x, c.y);
      await page.waitForTimeout(1800);
      const pop = await page.evaluate(() => {
        const els = [...document.querySelectorAll('[role="menu"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"]')]
          .filter((d) => d.getBoundingClientRect().width > 40);
        return els.length ? els[els.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
      });
      results.push({ ...c, opened: pop || '（无弹出内容）' });
      if (pop) await shot(page, 'M-06-组操作条-布局下拉.png');
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(900);
    }
    await logStep(B, { id: 'G6-group-actions', title: '组操作条「添加到工具箱」与「布局下拉」',
      target: '成组后把操作条拆成每一枚动作，逐个点开只读（跳过「整组执行」）',
      evidence: { leaves, results },
      visible_text: results.map((r) => `${r.t || `(w${r.w})`}[x=${r.x}] → ${r.opened}`).join('；'),
      shot: (results.some((r) => r.opened && r.opened !== '（无弹出内容）')) ? 'M-06-组操作条-布局下拉.png' : undefined });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
