// 批次 157-h —— 🔴 **善后执行**：删掉 157-c 复制出来的项目副本「测试项目5」
//
// 已知路径（157-g 实测）：
//   顶栏 `canvas-project-trigger`（20×28）→ 面板 `canvas-project-panel-popover`
//   （`SECTION`，aria 逐字 `Project panel`，**实测 `240×400@18,52`**，手册记的 `240×280@12,52` 是
//    五个项目时的读数；现在 8 个项目，高度随行数长）
//   → 每行行尾 `28×28` 的「更多」钮，testid = `project-more-ordinary-<项目 uuid>`、aria 逐字 `<项目名>的更多操作`
//
// ⚠️ **只删本批产生的那一个**（uuid `f43b795d-…`）。
//    面板里还有 `测试项目4 / 3 / 2 / 1` 四个**早就在的**副本（多半是更早批次或并行会话留下的），
//    **一个都不许动** —— 不是本轮的责任，且可能是别人的。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '157h', 目的: '删除项目副本「测试项目5」(f43b795d)' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157h.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 本批 = 'f43b795d-db00-4faa-9d9b-c899db06fb07';

const { b, p } = await openCanvas();
const R = readers(p);

const 开面板 = async () => {
  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!t) return { 错: 'no-trigger' };
  await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1800);
  return await p.evaluate(() => {
    const pop = document.querySelector('[data-testid="canvas-project-panel-popover"]');
    if (!pop) return { 开: false };
    return { 开: true, 逐字: (pop.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      项目: Array.from(pop.querySelectorAll('[data-testid^="project-more-ordinary-"]')).map((e) => {
        const r = e.getBoundingClientRect();
        return { uuid: (e.getAttribute('data-testid') || '').replace('project-more-ordinary-', ''),
          aria: e.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }) };
  });
};
const 菜单快照 = (阶段) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const ms = Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).filter((x) => x.getBoundingClientRect().width > 60);
  return { 阶段: tag, 数: ms.length, 菜单: ms.map((m) => ({ role: m.getAttribute('role'), testid: m.getAttribute('data-testid'),
    盒: 盒(m), 逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
    项: Array.from(m.querySelectorAll('[role=menuitem],button')).map((x) => { const r = x.getBoundingClientRect();
      return { 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }).filter((z) => z.盒[0] > 0) })) };
}, 阶段);

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { URL: p.url(), 项目名: await p.evaluate(() => (document.querySelector('[data-testid="canvas-project-title-trigger"]') || {}).innerText || ''), 状态行: await R.status() };
  console.log('起点', JSON.stringify(rec.起点));

  rec.面板 = await 开面板();
  落盘();
  console.log('\n🆕 面板', 串(rec.面板, 1400));
  const 我的 = ((rec.面板 || {}).项目 || []).find((z) => z.uuid === 本批);
  rec.本批行 = 我的 || null;
  断言('① 面板里找得到本批副本的「更多」钮', !!我的, { uuid: 本批, 全部: (rec.面板 || {}).项目 });
  rec.删前面板逐字 = (rec.面板 || {}).逐字;

  if (我的) {
    await p.mouse.click(我的.盒[2] + 我的.盒[0] / 2, 我的.盒[3] + 我的.盒[1] / 2);
    await p.waitForTimeout(1900);
    rec.更多菜单 = await 菜单快照('更多菜单');
    落盘();
    console.log('\n🆕 点「更多」后', 串(rec.更多菜单, 1800));
    const 项 = (rec.更多菜单.菜单 || []).flatMap((m) => m.项 || []);
    rec.更多项 = 项;
    断言('② 「更多」弹出了菜单', (rec.更多菜单.数 || 0) > 0, { 数: rec.更多菜单.数 });
    const 删除 = 项.find((z) => /删除|移除|Delete|Remove/.test(z.逐字 + (z.aria || '')));
    rec.删除项 = 删除 || null;
    断言('③ 菜单里有「删除」项', !!删除, { 项: 项.map((z) => z.逐字) });
    if (删除) {
      await p.mouse.click(删除.盒[2] + 删除.盒[0] / 2, 删除.盒[3] + 删除.盒[1] / 2);
      await p.waitForTimeout(2200);
      rec.点删后 = await 菜单快照('点删后');
      rec.点删后浮层 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=alertdialog]'))
        .filter((x) => x.getBoundingClientRect().width > 60)
        .map((x) => { const r = x.getBoundingClientRect();
          return { role: x.getAttribute('role'), testid: x.getAttribute('data-testid'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
            逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
            按钮: Array.from(x.querySelectorAll('button,[role=button]')).map((y) => { const yr = y.getBoundingClientRect();
              return { 逐字: (y.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: y.getAttribute('aria-label'),
                盒: [Math.round(yr.width), Math.round(yr.height), Math.round(yr.x), Math.round(yr.y)] }; }).filter((z) => z.盒[0] > 0) }; }));
      rec.点删后URL = p.url();
      落盘();
      console.log('\n🆕 点「删除」后', 串(rec.点删后浮层, 2200), '| URL', rec.点删后URL);
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }
try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { URL: p.url(), 状态行: await R.status(), 节点数: (await idsOf(p)).length, 浮层: await R.overlays(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);
