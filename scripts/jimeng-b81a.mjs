// 批次 81 · A：`00-quickstart.md` 的**逐条清单对账**。
// 为什么打这一页：页面时效性普查里它是**唯一「0 次批次提及」**的读者页
// —— 即从未被任何一轮实测对齐过，而它是读者的**第一页**，清单类断言最显眼。
//
// 页面上的清单（待核）：
//   左栏 9 项：文本/图片/视频/音频/时间线/主体/导演台/资产库/上传
//   底部 dock：工具切换/小地图/显示连线/缩放值
//   顶栏：返回首页/画布标题/项目/节点 N/已保存/搜索/生成历史/积分/用户菜单
//   右下：与 AI 对话
//   缩放菜单：适配画布 ⇧1（navigate-canvas.md 记 7 项）
//
// 🔒 全程只读：**只打开缩放菜单看逐字，不点任何一项**；不点任何生成/发送/下载。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, stable: true }; } return { scale: await scaleOf(), stable: false }; };
/** 只读枚举：把某个容器里「可点的可见元素」逐字列出来。 */
const enumerate = (rootSel, kind) => p.evaluate(([sel, k]) => {
  const root = sel === 'body' ? document.body : document.querySelector(sel);
  if (!root) return { root: sel, found: false };
  const seen = [];
  for (const e of root.querySelectorAll('button,[role="button"],[role="menuitem"],[role="tab"],a,input')) {
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.05) continue;
    if (b.width < 4 || b.height < 4) continue;          // 跳过 0×0 常驻占位
    const txt = (e.innerText || '').trim().split('\n')[0];
    const aria = (e.getAttribute('aria-label') || '').trim();
    const title = (e.getAttribute('title') || '').trim();
    const name = aria || txt || title;
    if (!name) continue;
    seen.push({ name: name.slice(0, 40), aria: aria.slice(0, 40), text: txt.slice(0, 30),
      box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
      testid: e.getAttribute('data-testid') || '', role: e.getAttribute('role') || e.tagName.toLowerCase(),
      disabled: e.getAttribute('aria-disabled') === 'true' || e.disabled === true });
  }
  return { root: sel, kind: k, found: true, count: seen.length, items: seen };
}, [rootSel, kind]);
try {
  const z = await settle(); log('开场 scale', JSON.stringify(z), '|', await status());
  out.viewport = await p.evaluate(() => ({ w: innerWidth, h: innerHeight, dpr: devicePixelRatio,
    url: location.pathname, zoomLabel: (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label') }));

  // ———— 1 左栏：先找出它的容器（不猜 testid） ————
  out.railProbe = await p.evaluate(() => {
    // 逐个候选元素，看谁同时包含「文本/视频/音频」这类入口词
    const want = ['文本', '图片', '视频', '音频'];
    const cands = [];
    for (const e of document.querySelectorAll('div,nav,aside,section')) {
      const t = (e.innerText || '');
      if (e.querySelectorAll('button,[role="button"]').length < 5) continue;
      const hit = want.filter((w) => t.includes(w)).length;
      if (hit < 3) continue;
      const b = e.getBoundingClientRect();
      if (b.width > 400 || b.height > innerHeight) continue;
      cands.push({ tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 50),
        testid: e.getAttribute('data-testid') || '', role: e.getAttribute('role') || '',
        box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
        buttons: e.querySelectorAll('button,[role="button"]').length });
    }
    return cands;
  });
  log('左栏候选容器：', JSON.stringify(out.railProbe, null, 1));
  const railSel = (out.railProbe[0] && (out.railProbe[0].testid ? `[data-testid="${out.railProbe[0].testid}"]` : null)) || null;
  out.rail = await enumerate(railSel || 'body', '左栏');
  log(`左栏（根=${railSel || 'body'}）共 ${out.rail.count} 项：`, JSON.stringify(out.rail.items.map((x) => x.name), null, 0));

  // ———— 2 底部 dock ————
  out.dockProbe = await p.evaluate(() => {
    const cands = [];
    for (const e of document.querySelectorAll('div,nav,footer')) {
      const b = e.getBoundingClientRect();
      if (b.height < 20 || b.height > 90) continue;
      if (b.y < innerHeight - 120) continue;                      // 贴底
      const btns = e.querySelectorAll('button,[role="button"]');
      if (btns.length < 2) continue;
      cands.push({ tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 46),
        testid: e.getAttribute('data-testid') || '', buttons: btns.length,
        box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}` });
    }
    return cands;
  });
  log('底部候选：', JSON.stringify(out.dockProbe, null, 1));
  const dockSel = (out.dockProbe[0] && out.dockProbe[0].testid) ? `[data-testid="${out.dockProbe[0].testid}"]` : null;
  out.dock = await enumerate(dockSel || 'body', '底部 dock');
  log(`底部 dock（根=${dockSel || 'body'}）共 ${out.dock.count} 项：`, JSON.stringify(out.dock.items.map((x) => x.name), null, 0));

  // ———— 3 顶栏 ————
  out.topbarProbe = await p.evaluate(() => {
    const cands = [];
    for (const e of document.querySelectorAll('div,header,nav')) {
      const b = e.getBoundingClientRect();
      if (b.height < 24 || b.height > 90) continue;
      if (b.y > 90) continue;                                      // 贴顶
      cands.push({ tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 46),
        testid: e.getAttribute('data-testid') || '', buttons: e.querySelectorAll('button,[role="button"]').length,
        box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}` });
    }
    return cands;
  });
  log('顶栏候选：', JSON.stringify(out.topbarProbe, null, 1));
  const topSel = (out.topbarProbe[0] && out.topbarProbe[0].testid) ? `[data-testid="${out.topbarProbe[0].testid}"]` : null;
  out.topbar = await enumerate(topSel || 'body', '顶栏');
  log(`顶栏（根=${topSel || 'body'}）共 ${out.topbar.count} 项：`, JSON.stringify(out.topbar.items.map((x) => x.name), null, 0));

  // ———— 4 「与 AI 对话」是否存在（右下角） ————
  out.aiChat = await p.evaluate(() => {
    const hits = Array.from(document.querySelectorAll('button,[role="button"],[role="dialog"],div'))
      .filter((e) => { const t = ((e.getAttribute('aria-label') || '') + ' ' + (e.innerText || '')).trim();
        return /与\s*AI\s*对话|AI\s*对话|与AI对话/.test(t); })
      .map((e) => { const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { tag: e.tagName, testid: e.getAttribute('data-testid') || '',
          cls: (e.getAttribute('class') || '').slice(0, 46), role: e.getAttribute('role') || '',
          text: (e.innerText || '').trim().split('\n').slice(0, 2).join(' / ').slice(0, 40),
          box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
          visible: cs.display !== 'none' && cs.visibility !== 'hidden' && b.width > 1 }; })
      .filter((x) => x.box.split('@')[1] !== '0,0');
    return hits;
  });
  log('「与 AI 对话」命中：', JSON.stringify(out.aiChat, null, 1));

  // ———— 5 缩放菜单逐字（**只打开不点**） ————
  const zb = await p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!zb) throw new Error('缩放按钮没找到');
  await p.mouse.click(zb.x, zb.y); await p.waitForTimeout(1200);
  out.zoomMenu = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return { found: false };
    const r = m.getBoundingClientRect();
    return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}`,
      count: m.querySelectorAll('[role="menuitem"]').length,
      items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => ({ text: (e.innerText || '').split('\n').filter(Boolean)[0] || '',
        shortcut: (e.innerText || '').split('\n').filter(Boolean).slice(1).join(' ').slice(0, 24),
        disabled: e.getAttribute('aria-disabled') === 'true', cursor: getComputedStyle(e).cursor })) };
  });
  log('缩放菜单：', JSON.stringify(out.zoomMenu, null, 1));
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);   // ⚠️ 一次
  log('Esc 后菜单还在吗 =', await p.evaluate(() => Array.from(document.querySelectorAll('[role="menu"]')).some((e) => e.getBoundingClientRect().width > 1)));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  const zf = await settle();
  out.end = { status: await status(), zoomLabel: await labelOf(), scale: zf.scale };
  log('终态', JSON.stringify(out.end));
  writeFileSync(new URL('./_tmp-b81.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
