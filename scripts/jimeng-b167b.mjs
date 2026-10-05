// 批次 167-b —— 167-a 撞到的坑修掉之后，重跑同一个靶子。
//
// 🔴 167-a 的错：我按「class 名里含 image/video/audio」挑节点，
//    挑到的是 **`视频 1` —— 它逐字写着 `No resources: 0 ready, 0 processing, 0 failed.`**
//    ⇒ 那个右键项（aria 形如「将 b22-upload 保存到主体库」）**只在有就绪素材时**才出现。
//    📌 正确挑法不是「类型像媒体节点」，而是**读它逐字里那句资源账**：有 `ready` 才有那个菜单项。
//
// 🔑 第二个坑：真正带素材的那个节点是 `b22-upload`（`node_gref4sw056`，即批次 156 用的那个），
//    可它的屏上坐标是 **(1958, 1131)** —— **在 1280×720 视口之外** ⇒ 必须先把它带进视野。
//    做法：把缩放降到 20% 再定位，收尾**按起点值复原**（不是硬编码 60%）。
//
// ⛔ 只读：右键 →「保存到主体库」**只开对话框**，不填名称、不点保存，Esc 关闭。
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const CSS_LOCAL = '/tmp/jimeng-main.94b57a0e55.css';
const CSS_URL = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/css/main.94b57a0e55.css';
if (!fs.existsSync(CSS_LOCAL)) execSync(`curl -s -m 40 -o ${CSS_LOCAL} ${CSS_URL}`);
const css = fs.readFileSync(CSS_LOCAL, 'utf8');
const 解转义 = (s) => s.replace(/\\2c\s?/g, ',').replace(/\\\]/g, ']').replace(/\\\[/g, '[').replace(/\\\(/g, '(').replace(/\\\)/g, ')').replace(/\\\//g, '/').replace(/\\%/g, '%').replace(/\\\./g, '.');
const 类到声明 = new Map();
for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  for (const sel of m[1].split(',')) {
    const s = sel.trim();
    if (!/^\.[\w\\]/.test(s)) continue;
    const key = '.' + 解转义(s.slice(1));
    if (!类到声明.has(key)) 类到声明.set(key, []);
    类到声明.get(key).push(m[2].trim());
  }
}
const 解析类 = (cls) => {
  const out = [];
  for (const c of cls) {
    const d = 类到声明.get('.' + c); if (!d) continue;
    for (const decl of d) {
      const 尺寸 = decl.split(';').map((x) => x.trim()).filter((x) => /^(?:max-|min-)?(?:width|height|padding|gap)/.test(x));
      if (尺寸.length) out.push({ 类: c, 声明: 尺寸 });
    }
  }
  return out;
};

const rec = { 批次: '167b', 目的: '读「设置主体」对话框的机制（classList → 声明 → 直接子几何）' };
let 断言过 = true, 断言数 = 0, 断言预期 = 5;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b167b.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读对话框 = () => {
  const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]');
  if (!d) return { 找到: false };
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  const 子 = Array.from(d.children).map((c) => { const q = c.getBoundingClientRect(), s = getComputedStyle(c);
    return { cls: (typeof c.className === 'string' ? c.className : '').slice(0, 64), testid: c.getAttribute('data-testid'),
      盒: [Math.round(q.width), Math.round(q.height)], flex: s.flex, grow: s.flexGrow, overflow: s.overflow }; });
  return { 找到: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    classList: (typeof d.className === 'string' ? d.className : '').split(/\s+/).filter(Boolean),
    计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth, minHeight: cs.minHeight,
      padding: cs.padding, gap: cs.gap, display: cs.display, boxSizing: cs.boxSizing, overflow: cs.overflow },
    子, 子高合计: 子.reduce((s, z) => s + z.盒[1], 0),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) };
};

const { b, p } = await openCanvas();
const R = readers(p);
let 起始缩放 = null;
try {
  await keyGuard(p); await settle(p, R); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
  const m = /(\d+)%/.exec(rec.起点.缩放 || ''); 起始缩放 = m ? parseInt(m[1], 10) : 60;
  console.log('起点', JSON.stringify(rec.起点), '→ 起始缩放', 起始缩放 + '%');

  // ① 按**资源账**挑节点（不是按 class）
  rec.有资源的节点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
    .map((x) => { const r = x.getBoundingClientRect();
      return { id: x.getAttribute('data-id'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
        有资源: !/No resources/.test(x.innerText || ''), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
    .filter((z) => z.有资源));
  console.log('有资源的节点 =', JSON.stringify(rec.有资源的节点).slice(0, 400));
  断言('⓪ 画布上确有**带就绪素材**的节点', rec.有资源的节点.length > 0, { 数: rec.有资源的节点.length });

  // ② 降到 20% 把它带进视野
  rec.降缩放 = await setZoom(p, 20);
  console.log('降缩放 =', JSON.stringify(rec.降缩放));
  await p.waitForTimeout(1500);

  const 目标 = await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.react-flow__node'))
      .find((n) => !/No resources/.test(n.innerText || '') && /b22-upload/.test(n.innerText || ''))
      || Array.from(document.querySelectorAll('.react-flow__node')).find((n) => !/No resources/.test(n.innerText || ''));
    if (!x) return null;
    const r = x.getBoundingClientRect();
    return { id: x.getAttribute('data-id'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
  });
  rec.目标 = 目标;
  console.log('目标节点 =', JSON.stringify(目标));
  断言('① 目标节点已进视野（20% 缩放后）', !!目标 && 目标.在视口内, { 目标 });

  if (目标 && 目标.在视口内) {
    await p.mouse.click(目标.中心[0], 目标.中心[1]); await p.waitForTimeout(1100);
    await p.mouse.click(目标.中心[0], 目标.中心[1], { button: 'right' }); await p.waitForTimeout(1800);
    const 项 = await p.evaluate(() => {
      const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => /保存到主体库/.test(x.innerText || ''));
      if (!m) return null;
      const r = m.getBoundingClientRect();
      return { 逐字: (m.innerText || '').trim(), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    });
    rec.菜单项 = 项;
    断言('② 右键菜单里有「保存到主体库」', !!项, { 项 });
    if (项) {
      await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
      const 读 = await p.evaluate(读对话框);
      if (读.找到) {
        读.解析 = 解析类(读.classList);
        rec.对话框 = 读;
        console.log('\nclassList =', JSON.stringify(读.classList));
        console.log('解析声明 =', JSON.stringify(读.解析));
        console.log('计算样式 =', JSON.stringify(读.计算));
        console.log('直接子 =', JSON.stringify(读.子));
        console.log('子高合计 =', 读.子高合计, '｜ 对话框高 =', 读.盒[1], '｜ 盒 =', JSON.stringify(读.盒));
        断言('③ 读数与手册记的 548×688 一致（订正前的基线核对）', 读.盒[0] === 548 && 读.盒[1] === 688, 读.盒);
        await p.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/125-subject-export-dialog-mechanism.png', import.meta.url).pathname });
        rec.图 = 'screenshots/125-subject-export-dialog-mechanism.png';
        断言('④ 截图已拍', true, null);
      } else { 断言('⑤ 找得到对话框', false, await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog]')).map((d) => d.getAttribute('data-testid')))); }
      落盘();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); console.log('异常', rec.异常); 断言过 = false; }
finally {
  for (let k = 0; k < 4; k++) { try { await p.keyboard.press('Escape'); await p.waitForTimeout(700); } catch (e) {} }
  try {
    if (起始缩放) { rec.复原缩放 = await setZoom(p, 起始缩放); console.log('缩放已复原 →', JSON.stringify(rec.复原缩放)); }
  } catch (e) { rec.缩放复原异常 = String(e).slice(0, 200); }
  try { await settle(p, R); } catch (e) {}
  try {
    const mm = await R.minimap();
    if (!mm || mm.ariaPressed !== 'true') {   // 手册纪律：缩放操作会关掉小地图，收尾要重开
      const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
        const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1300); }
      rec.小地图已重开 = true;
    }
  } catch (e) {}
  rec.收尾 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 选中: await R.selCount(), 浮层: await R.overlays(),
    缩放: await R.zoom(), 积分: await R.credits(), 小地图: await R.minimap() };
  console.log('收尾', JSON.stringify(rec.收尾));
  断言('⛔ 收尾回到基线（76 节点 / 0 选中 / 浮层 0 / 缩放复原 / 积分不变，无任何持久写入）',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 &&
    String(rec.收尾.积分) === String(rec.起点.积分) && (rec.收尾.缩放 || '').includes(String(起始缩放)),
    { 起点: rec.起点, 收尾: rec.收尾 });
  if (断言数 < 断言预期) { console.log(`⛔ 断言只跑了 ${断言数}/${断言预期} 条 —— 中途崩了`); 断言过 = false; }
  rec.断言执行数 = 断言数; rec.断言预期数 = 断言预期; rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
