// 批次 167-a —— 接住 166 留下的第二条静态信号：
// 「设置主体」对话框手册记 **`548×688`**，而 **548 与 688 在三张样式表里都不存在**
// （唯一一次 548 是 `153.548px`）⇒ 极可能也是**内容累加**，而不是定尺。
//
// 本轮只做**机制读取**，不猜：把它的 classList、计算样式、四个直接子的几何全读出来，
// 拿到机制之后再由 167-b **预测**并打视口阶梯 —— 与 165/166 同一套路：
// **量到机制 → 用机制预测 → 打预测**，而不是量到一组数就收工。
//
// ⛔ 只读：右键带媒体的节点 →「保存到主体库」**只开对话框**，**不填名称、不点保存**
//    （目标是账号级主体库写入，立规 20），Esc 关闭，断言浮层归零。
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';

const CSS_URL = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/css/main.94b57a0e55.css';
const CSS_LOCAL = '/tmp/jimeng-main.94b57a0e55.css';
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
    const d = 类到声明.get('.' + c);
    if (!d) continue;
    for (const decl of d) {
      const 尺寸 = decl.split(';').map((x) => x.trim()).filter((x) => /^(?:max-|min-)?(?:width|height|padding|gap)/.test(x));
      if (尺寸.length) out.push({ 类: c, 声明: 尺寸 });
    }
  }
  return out;
};

const rec = { 批次: '167a', 目的: '读「设置主体」对话框的机制：classList → 声明 → 四个直接子几何' };
let 断言过 = true, 断言数 = 0, 断言预期 = 4;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b167a.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读对话框 = () => {
  const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]');
  if (!d) return { 找到: false };
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  const 子 = Array.from(d.children).map((c) => { const q = c.getBoundingClientRect(), s = getComputedStyle(c);
    return { cls: (typeof c.className === 'string' ? c.className : '').slice(0, 70), testid: c.getAttribute('data-testid'),
      盒: [Math.round(q.width), Math.round(q.height)], flex: s.flex, grow: s.flexGrow, overflow: s.overflow }; });
  return { 找到: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    classList: (typeof d.className === 'string' ? d.className : '').split(/\s+/).filter(Boolean),
    计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth, minHeight: cs.minHeight,
      padding: cs.padding, gap: cs.gap, display: cs.display, boxSizing: cs.boxSizing, overflow: cs.overflow },
    子, 子高合计: 子.reduce((s, z) => s + z.盒[1], 0),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
  console.log('起点', JSON.stringify(rec.起点));

  // ① 找一个**带媒体**的节点（手册记：右键项逐字形如「将 b22-upload 保存到主体库」）
  rec.候选节点 = await p.evaluate(() => {
    const n = Array.from(document.querySelectorAll('.react-flow__node')).filter((x) => /image|video|audio/.test(x.className));
    return n.map((x) => { const r = x.getBoundingClientRect();
      return { id: x.getAttribute('data-id'), cls: x.className.replace('react-flow__node ', ''),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
        逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; }).slice(0, 12);
  });
  console.log('候选带媒体节点 =', JSON.stringify(rec.候选节点).slice(0, 600));
  const 目标 = (rec.候选节点.find((z) => z.在视口内) || rec.候选节点[0]);
  rec.目标节点 = 目标;
  断言('⓪ 画布上找得到带媒体的节点可右键', !!目标, { 候选数: rec.候选节点.length });

  if (目标) {
    // ② 右键 → 找「保存到主体库」那一项
    const cx = Math.round(目标.盒[2] + 目标.盒[0] / 2), cy = Math.round(目标.盒[3] + 目标.盒[1] / 2);
    await p.mouse.click(cx, cy); await p.waitForTimeout(1200);
    await p.mouse.click(cx, cy, { button: 'right' }); await p.waitForTimeout(1800);
    const 菜单项 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .map((m) => { const r = m.getBoundingClientRect();
        return { 逐字: (m.innerText || '').trim(), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
    rec.右键菜单 = 菜单项;
    console.log('右键菜单项 =', JSON.stringify(菜单项.map((z) => z.逐字)));
    const 项 = 菜单项.find((z) => z.逐字.includes('保存到主体库'));
    断言('① 右键菜单里有「保存到主体库」', !!项, { 菜单项: 菜单项.map((z) => z.逐字) });

    if (项) {
      await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(2800);
      const 读 = await p.evaluate(读对话框);
      if (读.找到) {
        读.解析 = 解析类(读.classList);
        rec.对话框 = 读;
        console.log('\nclassList =', JSON.stringify(读.classList));
        console.log('解析声明 =', JSON.stringify(读.解析));
        console.log('计算样式 =', JSON.stringify(读.计算));
        console.log('四个直接子 =', JSON.stringify(读.子));
        console.log('子高合计 =', 读.子高合计, '｜ 对话框高 =', 读.盒[1]);
        断言('② 对话框读数与手册记的 548×688 一致（订正前的基线核对）',
          读.盒[0] === 548 && 读.盒[1] === 688, 读.盒);
        断言('③ classList 里**没有**任何高度类名（若如此，688 就是内容高度）',
          !读.classList.some((c) => /^h-\[/.test(c) || /^h-\d/.test(c)), 读.classList.filter((c) => /^(max-|min-)?h-/.test(c)));
        await p.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/125-subject-export-dialog-mechanism.png', import.meta.url).pathname });
        rec.图 = 'screenshots/125-subject-export-dialog-mechanism.png';
      } else {
        rec.没找到对话框 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog]')).map((d) => d.getAttribute('data-testid')));
        断言('④ 找得到对话框', false, rec.没找到对话框);
      }
      落盘();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); console.log('异常', rec.异常); 断言过 = false; }
finally {
  for (let k = 0; k < 4; k++) { try { await p.keyboard.press('Escape'); await p.waitForTimeout(700); } catch (e) {} }
  try { await settle(p, R); } catch (e) {}
  rec.收尾 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 选中: await R.selCount(), 浮层: await R.overlays(), 积分: await R.credits() };
  console.log('收尾', JSON.stringify(rec.收尾));
  断言('⛔ 收尾回到基线（76 节点 / 0 选中 / 浮层 0 / 积分不变，未产生任何持久写入）',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
  if (断言数 < 断言预期) { console.log(`⛔ 断言只跑了 ${断言数}/${断言预期} 条 —— 中途崩了`); 断言过 = false; }
  rec.断言执行数 = 断言数; rec.断言预期数 = 断言预期; rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
