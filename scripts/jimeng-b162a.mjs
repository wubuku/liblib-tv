// 批次 162-a —— 两个缺口一次验完：
//   ① `20-reference.md` 尺寸表里「图片（空）」一行写着「本轮**未测**」、
//      「480 级方形」是旧记录未复核 —— 建一个**空图片节点**量准。
//   ② `assets-and-upload.md` 用「**该画布的资产库确实没有任何素材**」当阻塞理由 ——
//      而批次 158 实测**上传是持久的**（重载页面后自建节点仍在画布上），
//      那批上传的 WAV / PNG 还在不在？资产库是不是已经**不再为空**了？
//
// 🔴 建-删护栏：只建**一个**自建节点，收尾右键 → 上下文菜单 →「删除」后断言回到 76。
// ⛔ 只读：绝不点「生成」「确认上传」等任何提交类按钮。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos } from './jimeng-b139-lib.mjs';

const rec = { 批次: '162a', 目的: '量「空图片节点」尺寸并复核「资产库是否仍为空」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b162a.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const { b, p } = await openCanvas();
const R = readers(p);
let SELF = null;

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ================= ① 资产库复核（先做只读的，别把状态搞乱） =================
  const 资产钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  rec.资产钮 = 资产钮;
  断言('⓪ 左栏找得到「资产库」按钮', !!资产钮, { 资产钮 });
  if (资产钮) {
    await p.mouse.click(资产钮[0], 资产钮[1]);
    await p.waitForTimeout(2600);
    rec.资产库 = await p.evaluate(() => {
      const 面板 = document.querySelector('[class*="asset"], [data-testid*="asset"], [data-testid*="library"]');
      const 大面板 = Array.from(document.querySelectorAll('div')).filter((d) => {
        const r = d.getBoundingClientRect();
        return r.width > 500 && r.height > 300 && /素材|资产库/.test(d.innerText || '');
      }).slice(-1)[0];
      const 宿 = 大面板 || 面板;
      const 页签 = 宿 ? Array.from(宿.querySelectorAll('[role=tab],button')).map((t) => (t.innerText || '').trim()).filter(Boolean).slice(0, 12) : [];
      return {
        找到宿主: !!宿,
        testid: 宿 ? 宿.getAttribute('data-testid') : null,
        盒: 宿 ? (() => { const r = 宿.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })() : null,
        逐字: 宿 ? (宿.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) : null,
        页签,
        img数: 宿 ? 宿.querySelectorAll('img').length : null,
        video数: 宿 ? 宿.querySelectorAll('video').length : null,
        卡片类名: 宿 ? Array.from(new Set(Array.from(宿.querySelectorAll('div')).map((d) => d.className).filter((c) => typeof c === 'string' && /card|item|asset/i.test(c)))).slice(0, 6) : null,
      };
    });
    console.log('资产库 =', JSON.stringify(rec.资产库).slice(0, 700));
    落盘();
    await p.screenshot({ path: new URL('./122-asset-library-state.png', 出图).pathname });
    rec.图1 = 'screenshots/122-asset-library-state.png';
    // 关掉面板：点面板外空白
    await p.mouse.click(900, 690); await p.waitForTimeout(1500);
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
    rec.关面板后浮层 = await R.overlays();
  }

  // ================= ② 建一个空图片节点 =================
  const 图钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '图片'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  rec.图片钮 = 图钮;
  断言('① 左栏找得到「图片」按钮', !!图钮, { 图钮 });
  if (图钮) {
    await p.mouse.click(图钮[0], 图钮[1]);
    await p.waitForTimeout(3200);
    const 建后 = await idsOf(p);
    const 差 = 建后.filter((x) => !建前.includes(x));
    SELF = 差.length === 1 ? 差[0] : null;
    rec.建后 = { 数: 建后.length, 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits() };
    落盘();
    console.log('建后 =', JSON.stringify(rec.建后));
    断言('② 差集恰好 1、新节点选中、**积分不变**', SELF != null && 差.length === 1 && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);

    if (SELF) {
      await p.waitForTimeout(2200);
      rec.节点 = await p.evaluate((id) => {
        const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 不在: true };
        const r = n.getBoundingClientRect();
        const tr = n.querySelector('.react-flow__transform');
        const 内 = Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'));
        return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
          className: n.className,
          内部testid: [...new Set(内)],
          img数: n.querySelectorAll('img').length,
          内部盒: Array.from(n.querySelectorAll('div')).slice(0, 6).map((d) => { const q = d.getBoundingClientRect();
            return { 盒: [Math.round(q.width), Math.round(q.height)], testid: d.getAttribute('data-testid'), cls: (d.className || '').slice(0, 50) }; }),
          transform: tr ? getComputedStyle(tr).transform : null };
      }, SELF);
      rec.canvas坐标 = (await canvasPos(p))[SELF] || null;
      console.log('节点 =', JSON.stringify(rec.节点).slice(0, 800));
      落盘();

      // 反算 canvas 尺寸：屏上尺寸 / 缩放
      const 缩放 = 0.6;
      if (rec.节点.盒) {
        rec.推算 = { 屏上: [rec.节点.盒[0], rec.节点.盒[1]],
          canvas: [Math.round(rec.节点.盒[0] / 缩放), Math.round(rec.节点.盒[1] / 缩放)] };
      }
      console.log('推算 =', JSON.stringify(rec.推算));
      断言('③ 屏上与 canvas 尺寸都读到了', !!rec.节点.盒, rec.节点);

      rec.工具条 = await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return null;
        const r = t.getBoundingClientRect(); const 挂 = t.closest('.react-flow__node');
        return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          挂在节点id: 挂 ? 挂.getAttribute('data-id') : null,
          按钮: Array.from(t.querySelectorAll('button,[role=button]')).map((e) => ({ value: e.getAttribute('data-toolbar-value'), aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').trim().slice(0, 12) })) }; });
      console.log('工具条 =', JSON.stringify(rec.工具条).slice(0, 500));

      await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return false;
        const r = n.getBoundingClientRect(); const ov = document.createElement('div'); ov.id = '__hl__';
        ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (r.x - 4) + 'px;top:' + (r.y - 4) + 'px;width:' + (r.width + 8) + 'px;height:' + (r.height + 8) + 'px;';
        document.body.appendChild(ov); return true; }, SELF);
      await p.waitForTimeout(600);
      await p.screenshot({ path: new URL('./122-empty-image-node.png', 出图).pathname });
      rec.图2 = 'screenshots/122-empty-image-node.png';
      await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
      console.log('🖼 已拍 122');
      落盘();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ---- 收尾：右键 → 上下文菜单 → 删除 ----
try {
  if (SELF) {
    const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
    if (落) {
      await p.mouse.click(落[0], 落[1]); await p.waitForTimeout(1400);
      await p.mouse.click(落[0], 落[1], { button: 'right' }); await p.waitForTimeout(1700);
      const del = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return { 错: 'no-menu' };
        const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')); if (!it) return { 错: 'no-删除项' };
        const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      rec.删除落点 = del;
      if (del && !del.错) { await p.mouse.click(del[0], del[1]); await p.waitForTimeout(2400); }
    }
    for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }
} catch (e) { rec.删异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

try { await settle(p, R); } catch (e) {}
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.SELF = SELF;
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无', '| 删异常', rec.删异常 || '无');
断言('④ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
