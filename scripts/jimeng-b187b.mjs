// 批次 187 b 轮：**把主体节点的两处新读数量实** ——
//   ① ⊕ 按钮尺寸 19×19（手册第 24 行写的是「屏上恒为 36×36」）；
//   ② 它的描述文案 `Empty subject: main missing, 0 auxiliaries, voice missing. Select`
//      —— 批次 176/180/181 那张「类型 × 描述文案」交叉表里**没有这一种**，
//         因为当时画布上**一个主体节点都没有**。
//
// 做法：再建一个主体节点（纯 CRUD、零成本），**同轮里同时读一个别的类型做尺寸对照**
//（同屏、同缩放、同一次读数，排除「缩放不同」这种解释），读完按 id 删掉。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '187b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 菜单删除 = async (id) => {
  if (!(await 标题坐标(id))) { await p.mouse.move(640, 400); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); }
  const pt = await 标题坐标(id); if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: '无删除项或禁用' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id)) };
};
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
try {
  // 对照组：**先**读一个既有类型（video）的 ⊕ 尺寸，同一次读数里做对照
  const 对照 = await p.evaluate(() => {
    const n = document.querySelector('.react-flow__node-video'); if (!n) return null;
    return { 型: 'video', 加号: Array.from(n.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => { const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), 屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; }) };
  });
  rec.对照组video = 对照;
  const 按钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '主体');
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(按钮[0], 按钮[1]); await p.waitForTimeout(4000);
  const 新增 = (await id集()).filter((i) => !前id.includes(i));
  rec.新增 = 新增;
  if (新增.length) {
    const nid = 新增[0];
    rec.主体读数 = await p.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const 宿主 = document.getElementById(`canvas-node-description-${i}`);
      const r = n.getBoundingClientRect();
      const 宿主r = 宿主 ? 宿主.getBoundingClientRect() : null;
      return { aria: n.getAttribute('aria-label'), 标题: (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0],
        节点屏上: { w: Math.round(r.width), h: Math.round(r.height) },
        ariaDescribedby: n.getAttribute('aria-describedby'),
        描述宿主: 宿主 ? { 标签: 宿主.tagName, 逐字: (宿主.innerText || '').trim(), class: (宿主.className || '').toString().slice(0, 80),
          屏上: { w: Math.round(宿主r.width), h: Math.round(宿主r.height) },
          在节点内: !!宿主.closest('.react-flow__node'), 是节点第一层: 宿主.parentElement === n } : null,
        节点内逐字: (n.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 160),
        加号: Array.from(n.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => { const b = e.getBoundingClientRect();
          const cs = getComputedStyle(e);
          return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
            屏上: { w: Math.round(b.width), h: Math.round(b.height) }, fontSize: cs.fontSize, padding: cs.padding }; }) };
    }, nid);
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
const 现存 = await id集();
rec.收尾前 = { 现在节点数: 现存.length, 本轮多出: 现存.filter((i) => !前id.includes(i)) };
rec.清理 = [];
for (const id of 现存.filter((i) => !前id.includes(i))) rec.清理.push({ id, ...(await 菜单删除(id)) });
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
