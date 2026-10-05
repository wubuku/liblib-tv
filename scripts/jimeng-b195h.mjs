// 批次 195 h 轮：删掉已播过的节点，换一个**从没播过**的新素材节点，重拍 189/190。
//
// g 轮的守卫正确地拦下了两张图，原因是**两个不同的原因**，都不是 bug：
//   ① 189：我的断言写「无 <video>」——**错**。手册第 32 行早写明「没有 <video> 元素」只在静止态成立，
//      取消选中后 `<video>` **仍留在 DOM 里**（g 轮实测 currentTime 冻在 2.857、元素还在）。
//      ⇒ 放宽成「选中=false 且 无大播放键 且 无控件行」，`<video>` 只作读数记录。
//   ② 190：这个节点 f 轮**已经播过** ⇒ 点标题行拿到的是「**播完暂停**」态（7 个按钮、控件行在），
//      而手册三档表第三行本来就写着「正在播 / **播完暂停**」共用一档。
//      ⇒ 要拿到真正的「**从没播过**」那一档，必须换一个全新节点。
//
// 🔴 护栏：删除只删 SELF（g 轮护栏拿到的差集 id），新节点也只删自己那一个。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';
import { execSync } from 'node:child_process';

const OLD = 'node_anew4vmz06';
const NEW_VIDEO = '/tmp/jimeng-b195b-test.mp4';
const OUTDIR = 'docs/user-manual/jimeng-canvas/screenshots';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b195h', 删掉的旧节点: OLD, 新素材: NEW_VIDEO };

// ---- 造第二个素材（换个文件名，避免与旧素材同名被去重）----
execSync(`ffmpeg -y -f lavfi -i "testsrc2=size=640x360:rate=30:duration=8" -pix_fmt yuv420p -c:v libx264 -profile:v baseline -level 3.0 -movflags +faststart ${NEW_VIDEO} 2>/dev/null`);
log('新素材已造：', NEW_VIDEO);

// ---- 删旧节点：右键菜单 → 删除（只删 SELF）----
const 删节点 = async (id) => {
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, id);
  if (!pt) return { 跳过: '节点不在' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(900);
  const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => /^删除/.test(e.innerText.trim()));
    if (!it) return null; const r = it.getBoundingClientRect(); return { 文案: it.innerText.trim(), 坐标: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (!项) { await p.keyboard.press('Escape'); return { 跳过: '菜单里没有删除项' }; }
  await p.mouse.click(项.坐标[0], 项.坐标[1]); await p.waitForTimeout(1400);
  return { 点了: 项.文案, 还在: (await R.ids()).includes(id) };
};
await setZoom(p, 26);
out.删除旧节点 = await 删节点(OLD);
out.删除后节点数 = (await R.ids()).length;
log('删除旧节点：', JSON.stringify(out.删除旧节点), '| 节点数', out.删除后节点数);

// ---- 上传新素材 ----
await setZoom(p, 50);
const idsBefore = new Set(await R.ids());
out.上传前积分 = await R.credits();
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
if (!rail.length) { out.上传 = { 跳过: '找不到上传入口' }; }
else {
  p.on('filechooser', async (fc) => { try { await fc.setFiles(NEW_VIDEO); } catch (e) { log('setFiles 失败', e.message); } });
  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(2500);
  let created = [];
  for (let k = 1; k <= 24; k++) { await p.waitForTimeout(1500); created = (await R.ids()).filter((id) => !idsBefore.has(id)); if (created.length) break; }
  out.上传 = { created, 上传后积分: await R.credits() };
  log('新节点：', JSON.stringify(created), '| 积分', out.上传前积分, '→', out.上传后积分);
}

// ---- 等资源就绪 ----
const SELF = (out.上传 && out.上传.created && out.上传.created.length === 1) ? out.上传.created[0] : null;
out.SELF = SELF;
log('新 SELF =', SELF);
if (!SELF) { out.中止 = '没有拿到唯一新节点 ⇒ 不测不删'; fs.writeFileSync('/tmp/b195h.json', JSON.stringify(out, null, 1)); out.收尾 = await endState(p, R, 基线); await b.close(); process.exit(0); }

out.就绪序列 = [];
for (let k = 0; k < 10; k++) {
  const t = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { 消失: true };
    const s = (n.innerText || '') + ' || ' + (n.getAttribute('aria-label') || '');
    const m = /((?:\d+ resources?:|No resources:)[^|]*)/.exec(s);
    return { 账: m ? m[0].trim() : null, video: n.querySelectorAll('video').length, innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 90) }; }, SELF);
  out.就绪序列.push(t); if (t.账 && /1 ready/.test(t.账)) break; await p.waitForTimeout(2000);
}
log('就绪：', JSON.stringify(out.就绪序列.at(-1)));
fs.writeFileSync('/tmp/b195h.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
