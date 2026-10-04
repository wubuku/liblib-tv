// 批次 157-g：专攻「项目」面板 —— 手册说 testid 是 canvas-project-panel-popover，
// 行尾「更多」钮是 project-more-ordinary-<uuid>。本轮把这两种 testid 逐个点名找，并试多种点法。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
const rec = { 批次: '157g', 目的: '打开项目面板并找到副本的「更多」钮' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157g.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const { b, p } = await openCanvas();
const R = readers(p);
const 查 = (t) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 可见 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pop = Array.from(document.querySelectorAll('[data-testid="canvas-project-panel-popover"]')).filter(可见);
  return { 阶段: tag,
    面板: pop.map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), 盒: 盒(e),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      行: Array.from(e.querySelectorAll('a,button,[role=button],[role=menuitem]')).filter(可见)
        .map((x) => ({ tag: x.tagName, testid: x.getAttribute('data-testid'), aria: x.getAttribute('aria-label'),
          href: (x.getAttribute('href') || '').slice(-42), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26), 盒: 盒(x) })) })),
    更多钮: Array.from(document.querySelectorAll('[data-testid^="project-more"]')).filter(可见)
      .map((e) => ({ testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 盒: 盒(e) })) };
}, t);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { URL: p.url(), 状态行: await R.status() };
  rec.前 = await 查('前');
  console.log('前：面板', rec.前.面板.length, '| 更多钮', JSON.stringify(rec.前.更多钮));
  // 三种点法
  const 点法 = [];
  const t1 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  点法.push({ 名: 'trigger 中心', 点: t1 ? [t1.盒[2] + t1.盒[0] / 2, t1.盒[3] + t1.盒[1] / 2] : null });
  const t2 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-title-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  点法.push({ 名: 'title-trigger 中心', 点: t2 ? [t2.盒[2] + t2.盒[0] / 2, t2.盒[3] + t2.盒[1] / 2] : null });
  点法.push({ 名: 'title-trigger 左 1/4', 点: t2 ? [t2.盒[2] + t2.盒[0] / 4, t2.盒[3] + t2.盒[1] / 2] : null });
  rec.点法 = 点法;
  for (const z of 点法) {
    if (!z.点) continue;
    await p.mouse.click(z.点[0], z.点[1]); await p.waitForTimeout(1800);
    const q = await 查(z.名);
    console.log(`点法「${z.名}」(${z.点}) → 面板 ${q.面板.length} | 更多钮 ${q.更多钮.length}`);
    if (q.面板.length || q.更多钮.length) { rec.命中 = z.名; rec.面板 = q.面板; rec.更多钮 = q.更多钮; break; }
    for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  }
  落盘();
  if (rec.命中) {
    console.log('\n🆕 命中点法', rec.命中);
    for (const P of rec.面板) { console.log('面板', P.aria, JSON.stringify(P.盒), '|', P.逐字);
      for (const L of P.行) console.log('   行', JSON.stringify(L.盒), '|', L.逐字, '|', L.testid || '', '|', L.href); }
    console.log('更多钮', JSON.stringify(rec.更多钮, null, 1));
  } else { console.log('三种点法都没打开面板'); }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); 落盘(); }
try { await settle(p, R); } catch (e) {}
console.log('收尾 浮层', await R.overlays(), '| URL', p.url());
process.exit(0);
