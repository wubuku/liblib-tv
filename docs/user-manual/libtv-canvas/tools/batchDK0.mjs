// Batch DK-0：`runCount` 到底是「点开用了一次」还是「生成过一次」？
//
// DJ 已经把字段名坐实为 `runCount`，但**语义未验**。本轮做一次**受控的因果实验**：
//
//   ① 读出某张卡当前显示的数字（记死）
//   ② **点那张卡**（已知后果：画布上多一个 `m-` 前缀的「素材-风格」节点）
//   ③ **刷新页面重进广场**，找同一张卡，再读它的数字
//   ④ 比对：变了没有？变了多少？
//
// ⚠️ 安全与清理（沿用 CZ 已验证过的协议）：
//   · 点卡**不扣积分**（CZ 实测 `20 → 20`），不触发生成；
//   · ⭐ 清理只删**本轮自己建的那一个**：靠「点之前存基线 data-id 列表」+ 新增 id，
//     再核 `m-` 前缀 + 名字以「素材-」开头 —— 三条同时成立才删；
//   · 绝不碰历史遗留对象。
//
// ⚠️ 归因纪律：⭐ **一次只点一张**，且前后都重新进广场读数
//   （避免「广场自己在刷新计数」被误当成「我点的」）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

const { browser, page } = await launch();

const boot = async () => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
  const pk = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return null; const r = b.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }
};

const openPlaza = async () => {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(2000);
  await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
  await page.waitForTimeout(4500);
};

// ⭐ 读一屏卡：名字 + 显示的数字 + 卡片中心（两层容器按 DI-1 定的）
const readCards = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return [];
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const out = []; const seen = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    let L3 = null;
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { L3 = p; break; }
    }
    if (!L3) continue;
    const cr = L3.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 620) continue;
    const k = `${Math.round(cr.x)},${Math.round(cr.y)}`;
    if (seen.has(k)) continue; seen.add(k);
    const 数字 = [...L3.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && /^\d+(\.\d+)?w?$/.test((e.innerText || '').trim()))
      .map((e) => (e.innerText || '').trim());
    const 行 = (L3.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
    out.push({ 卡名: 行[0] || '(读不到)', 数字: 数字[0] || null, 中心: [Math.round(cr.x + cr.width / 2), Math.round(cr.y + 60)] });
  }
  return out;
});

const nodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node[data-id]')].map((n) => ({ id: n.getAttribute('data-id'), 名: (n.innerText || '').split('\n')[0].trim().slice(0, 24) })));

// ---------- ① 基线 ----------
await boot();
out.基线节点 = await nodes();
LOG(`基线画布节点 ${out.基线节点.length} 个`);
await openPlaza();
out.点之前 = await readCards();
LOG(`\n点之前读到 ${out.点之前.length} 张卡：`);
for (const c of out.点之前) LOG(`  「${c.卡名}」 数字=${c.数字}`);

// ⭐ 选一张**数字不带 w**（便于精确比较）的卡
const 目标 = out.点之前.find((c) => c.数字 && !c.数字.endsWith('w'));
if (!目标) { LOG('⛔ 没有不带 w 的卡，换批次'); } else {
  LOG(`\n⭐ 目标卡：「${目标.卡名}」 数字=${目标.数字}，点击坐标 ${JSON.stringify(目标.中心)}`);

  // ---------- ② 点它 ----------
  await page.mouse.click(目标.中心[0], 目标.中心[1]);
  await page.waitForTimeout(3000);
  out.点之后节点 = await nodes();
  const 新增 = out.点之后节点.filter((n) => !out.基线节点.some((b) => b.id === n.id));
  LOG(`点之后节点 ${out.点之后节点.length} 个，新增 ${JSON.stringify(新增)}`);

  // ---------- ③ 刷新重进，再读同一张卡 ----------
  await boot();
  await openPlaza();
  out.点之后 = await readCards();
  const 复读 = out.点之后.find((c) => c.卡名 === 目标.卡名);
  LOG(`\n⭐ 刷新后同一张卡：「${复读?.卡名}」 数字=${复读?.数字}（点之前是 ${目标.数字}）`);

  const 解析 = (t) => { if (!t) return null; return t.endsWith('w') ? parseFloat(t.slice(0, -1)) * 10000 : Number(t); };
  const a = 解析(目标.数字); const b = 解析(复读?.数字);
  out.对比 = { 前: 目标.数字, 后: 复读?.数字 ?? null, 前值: a, 后值: b, 差值: a !== null && b !== null ? b - a : null };
  LOG(`⭐ 差值: ${out.对比.差值}`);

  // ⭐ 顺带：同一屏里**别的卡**有没有跟着变？（排除「广场整体刷新」的归因）
  const 其它变化 = [];
  for (const c0 of out.点之前) {
    if (c0.卡名 === 目标.卡名) continue;
    const c1 = out.点之后.find((x) => x.卡名 === c0.卡名);
    if (c1 && c1.数字 !== c0.数字) 其它变化.push({ 卡名: c0.卡名, 前: c0.数字, 后: c1.数字 });
  }
  out.其它卡变化 = 其它变化;
  LOG(`⭐ 同一屏其它卡有变化的吗: ${其它变化.length} 个 ${JSON.stringify(其它变化)}`);

  // ---------- ④ 清理 ----------
  out.清理 = { 新增, 已删: [] };
  for (const n of 新增) {
    const 三条 = !out.基线节点.some((b) => b.id === n.id) && /^m-/.test(n.id) && /^素材-/.test(n.名);
    if (!三条) { LOG(`  ⛔ ${n.id}「${n.名}」不满足三条清理条件，不动`); continue; }
    // ⛔ ⛔ 先按 ESC 退出可能的编辑态，再点节点 → Delete
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    await page.evaluate((id) => {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!el) return;
      const r = el.getBoundingClientRect();
      el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r.x + 40, clientY: r.y + 20 }));
    }, n.id);
    await page.waitForTimeout(1200);
    // ⚠️ 不用 ⌘A（会全选）；只删这一个
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1500);
    const 还在 = (await nodes()).some((x) => x.id === n.id);
    LOG(`  ${还在 ? '⛔ 仍在' : '✅ 已删'} ${n.id}「${n.名}」`);
    if (!还在) out.清理.已删.push(n.id);
  }
  // 复核
  out.清理后节点 = await nodes();
  const 剩余新增 = out.清理后节点.filter((n) => !out.基线节点.some((b) => b.id === n.id));
  LOG(`\n⭐ 清理后节点 ${out.清理后节点.length} 个；与基线相比仍多出: ${JSON.stringify(剩余新增)}`);
  out.清理干净 = 剩余新增.length === 0 && out.清理后节点.length === out.基线节点.length;
  LOG(`⭐ 清理是否干净: ${out.清理干净 ? '✅ 是' : '⛔ 否'}`);
}

await writeFile(new URL('./batchDK0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDK0.json ===');
await browser.close();
