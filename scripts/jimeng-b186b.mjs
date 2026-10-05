// 批次 186 b 轮：**给「下载受资源状态约束」这个推论配正向守卫** ——
// 造一个**带资源**的音频节点，看它的「下载」是不是就变成可用了。
//
// 186 的六类普查读数：
//   image（有资源）9 项 200×372，下载**可用**
//   video（空）7 项 200×292，下载禁用，原因逐字「没有可用的就绪资源」
//   audio（空）7 项 200×292，下载禁用，原因逐字「没有可用的就绪资源」
//   text 7 项，下载**可用**；timeline / external 7 项，禁用，原因「请选择至少一个组、文本、图片或视频项」
// ⇒ 「下载」**在六种类型上都存在**，变的只是**能不能用**。
// ⇒ 手册说它是「类型白名单」，但视频/音频的禁用原因与「有没有资源」而不是「什么类型」相关
//    —— **这一步还是推论**，必须有正向守卫。
//
// 守卫做法：合成一段 1 秒 440Hz 的 WAV（`/tmp/jimeng-b186-tone.wav`，纯本地合成、不下载），
// 用左栏「上传」把它传上去，得到一个**带资源**的音频节点，读它的「下载」。
// ⛔ 不点「下载」（会落盘文件）、不生成、不分享。
// ⚠️ 收尾必须删掉这个上传出来的节点，并核验原有 76 个 id 逐个仍在。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
import fs from 'node:fs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '186b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 读菜单 = async (id) => {
  if (!(await 标题坐标(id))) await p.mouse.move(640, 400), await p.keyboard.press('Shift+Digit1'), await p.waitForTimeout(2400);
  const pt = await 标题坐标(id);
  if (!pt) return { 失败: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => { const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null }; }) }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (!m) return { 失败: '菜单没开' };
  const 下 = m.项.find((x) => x.名 === '下载' || x.名.startsWith('下载'));
  return { 几何: m.几何, 项数: m.项.length, 全部项: m.项.map((x) => x.名),
    下载: 下 ? { 在: true, 禁用: 下.禁用, 原因逐字: 下.禁用 ? 下.第二段 : null } : { 在: false } };
};
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
rec.音频文件 = fs.existsSync('/tmp/jimeng-b186-tone.wav') ? fs.statSync('/tmp/jimeng-b186-tone.wav').size + ' 字节' : '没有';
try {
  // ① 传文件：左栏「上传」→ **必须用 p.on('filechooser') 全局监听**（手册记过 waitForEvent 会超时）
  const 上传点 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '上传');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  rec.上传按钮 = 上传点;
  if (!上传点) rec.说明 = '左栏没有「上传」按钮';
  else {
    let chooser = null;
    const onChooser = (c) => { chooser = c; };
    p.on('filechooser', onChooser);
    await p.mouse.click(上传点[0], 上传点[1]);
    await p.waitForTimeout(1500);
    p.off('filechooser', onChooser);
    if (!chooser) rec.说明 = '没有触发 filechooser';
    else {
      rec.chooser = { 多选: chooser.isMultiple(), 接受类型长度: (await p.evaluate(() => { const e = document.querySelector('input[type=file]'); return e ? (e.getAttribute('accept') || '').length : -1; })) };
      await chooser.setFiles('/tmp/jimeng-b186-tone.wav');
      await p.waitForTimeout(7000);
      const 新增 = (await id集()).filter((i) => !前id.includes(i));
      rec.上传后新增 = 新增;
      if (!新增.length) rec.说明 = '上传后没有新节点';
      else {
        const nid = 新增[0];
        rec.新节点 = { id: nid, aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), nid),
          标题: await p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], nid),
          class: await p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"]`)?.className || '').toString(), nid) };
        // 等缩略图/资源就位，再读菜单
        await p.waitForTimeout(6000);
        rec.带资源节点的菜单 = await 读菜单(nid);
        rec.状态行 = await R.status();
      }
    }
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
// 收尾：删掉本轮上传出来的节点
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
const 现存 = await id集();
const 残留 = 现存.filter((i) => !前id.includes(i));
rec.收尾前 = { 现在节点数: 现存.length, 本轮多出: 残留 };
rec.清理 = [];
for (const id of 残留) rec.清理.push({ id, ...(await 菜单删除(id)) });
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
