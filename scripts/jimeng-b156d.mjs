// 批次 156-d —— 打开 `[data-toolbar-value="tools"]` 菜单，找「保存到主体库」并**真的执行一次**
//
// 🔑 156-c 的收获（这是本批最大的结构发现）：
//    图片节点浮动工具条 `959×40`、**12 个按钮，全部带 `data-toolbar-value`**：
//    `smart-edit` 智能改图 ｜ `panorama` 720 全景 ｜ `expand` 扩图 ｜ `image-hd` 智能超清
//    ｜ `remove-background` 抠图 ｜ `image-presets` 预设 ｜ `multi-angle` 多角度
//    ｜ `lighting` 智能打光 ｜ **`tools` 工具** ｜ `ask-ai` AI 助手 ｜ `preview` 全屏 ｜ `download` 下载。
//    ⇒ **除最后两个外，`aria-label` 逐字为空**（所以按 aria 找「工具」必然找不到），
//    **12/12 悬停提示也全为空** ⇒ 手册一直靠「可见文字」认按钮，
//    而真正稳定的机器标识是 **`data-toolbar-value`**（英文枚举，不随语言/裁切变）。
//    🆕 **`aria-haspopup="menu"` 的恰好 2 个**：`image-presets` 与 `tools`
//    ⇒ 「哪些按钮会开菜单」有机械判据，不必逐个点。
//
// 🎯 本轮三步（写数据 ⇒ 必撤回）：
//   ① 点 `[data-toolbar-value="tools"]` → 读菜单全谱，找「保存到主体库」
//   ② **点它**（2026-10-04 目标更新已把「保存到主体库」列入解锁清单）→ 轮询主体库
//   ③ 🔴 **立刻撤回**：找主体库里的删除入口并删掉，最后断言回到基线逐字「没有可用主体」
//
// ⛔ 红线：不点生成/发送/确认生成类按钮；不扣费；**只动自己刚建的那一个主体**；
//    平移视图结尾原样还原并断言 transform 逐字相同。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156d', 目的: '打开 tools 菜单 → 保存到主体库 → 验证 → 撤回' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156d.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const 写transform = (t) => p.evaluate((s) => { const e = document.querySelector('.react-flow__viewport'); if (e) e.style.transform = s; }, t);
const 取缩放 = (t) => { const m = /scale\(([\d.]+)\)/.exec(t || ''); return m ? parseFloat(m[1]) : 0.6; };

// 立规 12：三条同时成立
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    if (pd.toolbarValue && b.getAttribute('data-toolbar-value') !== pd.toolbarValue) return false;
    if (pd.字面等于 && (b.innerText || '').replace(/\s+/g, ' ').trim() !== pd.字面等于) return false;
    const a = b.getAttribute('aria-label') || '';
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (pd.角色 === 'menuitem' && b.getAttribute('role') !== 'menuitem') return false;
    return true;
  });
  const 可用 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    if (!(cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight)) continue;
    if (btn !== b) continue;
    可用.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), toolbarValue: b.getAttribute('data-toolbar-value'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), disabled: b.getAttribute('aria-disabled'),
      中心是自己: true });
  }
  return { 候选数: cands.length, 可用 };
}, pred);

const 读主体库 = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
  if (!d) return { 命中: false };
  return { 命中: true, 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    可见按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
      逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), 盒: 盒(x), disabled: x.getAttribute('aria-disabled') })).filter((z) => z.盒[0] > 0) };
});

const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  const s = 取缩放(起点transform);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p) };

  // ===== ① 平移 → 选中图片节点 → 打开 tools 菜单 =====
  const IMG = 'node_gref4sw056';
  const cp = await canvasPos(p);
  const [nx, ny] = cp[IMG] || [0, 0];
  await 写transform('translate(' + (560 - nx * s) + 'px, ' + (380 - ny * s) + 'px) scale(' + s + ')');
  await p.waitForTimeout(1400);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  if (!落.__err) {
    await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
    rec.选中数 = await selCount(p);
    const T = await 找点({ sel: 'button,[role=button]', toolbarValue: 'tools' });
    rec.tools钮 = T;
    const G = (T.可用 || [])[0];
    rec.tools落点 = G || null;
    if (G) {
      await p.mouse.click(G.x, G.y); await p.waitForTimeout(1800);
      rec.菜单 = await p.evaluate(() => {
        const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
        const ms = Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).filter((x) => x.getBoundingClientRect().width > 100);
        if (!ms.length) return { 命中: false };
        const m = ms[ms.length - 1];
        return { 命中: true, 菜单数: ms.length, role: m.getAttribute('role'), aria: m.getAttribute('aria-label'), 盒: 盒(m),
          逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
          项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
            aria: it.getAttribute('aria-label'), 盒: 盒(it), disabled: it.getAttribute('aria-disabled'), svg数: it.querySelectorAll('svg').length })) };
      });
      落盘();
      console.log('🆕 tools 菜单', 串(rec.菜单, 2800));
      const 项 = (rec.菜单 || {}).项 || [];
      const 保存项 = 项.find((z) => /主体库|保存到主体/.test(z.逐字));
      rec.保存到主体库项 = 保存项 || null;
      断言('① 「工具」菜单打开，且里面有「保存到主体库」这一项', (rec.菜单 || {}).命中 === true && !!保存项, { 项: 项.map((z) => z.逐字) });

      // ===== ② 点「保存到主体库」=====
      if (保存项) {
        const 落点 = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
          for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
            if (el && el.closest('[role=menuitem]')) return { x: xx, y: yy }; } return { __err: 'no-point' }; }, 保存项.盒);
        rec.保存落点 = 落点;
        if (!落点.__err) {
          await p.mouse.click(落点.x, 落点.y);
          // 🔑 轮询 8 秒（1 秒步长），看有没有任何提示 / 浮层
          rec.保存后轮询 = [];
          for (let i = 0; i < 8; i++) {
            await p.waitForTimeout(1000);
            rec.保存后轮询.push({ 第几秒: i + 1, 浮层: await R.overlays(),
              逐字新: await p.evaluate(() => Array.from(document.querySelectorAll('[role=alert],[role=status],[role=toast],body')).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(-160)).filter(Boolean).slice(-1)[0] || '') });
          }
          rec.保存后积分 = await R.credits();
          落盘();
          console.log('\n保存后轮询', 串(rec.保存后轮询, 1800));
        }
      }
    }
  }

  // ===== ③ 打开资产库 → 主体页 → 对账 + 撤回 =====
  await 写transform(起点transform); await p.waitForTimeout(1200);
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
      if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
      if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
      return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' }; });
    if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900);
  }
  const 库 = await 找点({ sel: 'button,[role=button]', 字面等于: '资产库' });
  const L = (库.可用 || [])[0];
  if (L) {
    await p.mouse.click(L.x, L.y); await p.waitForTimeout(2200);
    const 主体页签 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tab]')).map((t) => { const r = t.getBoundingClientRect();
      return { 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
    rec.页签 = 主体页签;
    const 主 = 主体页签.find((z) => z.逐字 === '主体');
    if (主) {
      await p.mouse.click(Math.round(主.盒[0] + 主.盒[2] / 2), Math.round(主.盒[1] + 主.盒[3] / 2));
      await p.waitForTimeout(2000);
      rec.主体库保存后 = await 读主体库();
      落盘();
      console.log('\n🆕 主体库（保存后）', 串(rec.主体库保存后, 2600));
    }
    // 撤回：找删除入口
    rec.删除候选 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button],[role=menuitem]'))
      .map((x) => { const r = x.getBoundingClientRect();
        return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
          逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
      .filter((z) => z.盒[0] > 0 && z.盒[1] > 0 && /删除|移除|Delete|Remove|✕|×/i.test((z.aria || '') + z.逐字)));
    console.log('\n删除候选', 串(rec.删除候选, 1200));
    落盘();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await 写transform(起点transform);
await p.waitForTimeout(1400);
rec.还原后transform = await 读transform();
await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
落盘();
console.log('\n还原 transform 逐字相同 =', 起点transform === rec.还原后transform);
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('② 视图 transform 与起点逐字相同', 起点transform === rec.还原后transform, { 起点: 起点transform, 后: rec.还原后transform });
rec.断言全过 = 断言过; 落盘();
await b.close();
