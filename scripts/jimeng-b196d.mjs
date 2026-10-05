// 批次 196 d 轮：当场重做一次上传，在 `Upload complete` **还在页面上**时定位它属于哪个容器。
//
// c 轮三处（裸页面 / 开资产库 / 悬停左栏）全部 0 命中 ⇒ a 轮抓到的是**上传完成那一瞬的残留**，
// 时间过去就没了。这本身是一条读数：**那条状态串不是常驻的**。
//
// 本轮：传一次 → 立刻（0.5s / 2s / 5s 三个时点）扫全页 + 扫资产库 dialog，
//   并打印每个命中的**祖先链**，定位它挂在谁下面。
//   收尾把新节点删掉（护栏同批次 195）。
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const VIDEO = '/tmp/jimeng-b196-probe.mp4';
const NAME = 'jimeng-b196-probe.mp4';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b196d', 探针文件: NAME };

execSync(`ffmpeg -y -f lavfi -i "testsrc2=size=320x180:rate=15:duration=3" -pix_fmt yuv420p -c:v libx264 -profile:v baseline -level 3.0 -movflags +faststart ${VIDEO} 2>/dev/null`);
log('探针素材已造（3 秒 / 320x180，尽量小）');

await setZoom(p, 50);
const idsBefore = new Set(await R.ids());
out.上传前积分 = await R.credits();

const 上传入口 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
  .find((x) => (x.getAttribute('aria-label') || '') === '上传' && x.getBoundingClientRect().width > 0);
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
p.on('filechooser', async (fc) => { try { await fc.setFiles(VIDEO); } catch (e) { log('setFiles 失败', e.message); } });
if (!上传入口) { out.中止 = '找不到上传入口'; }
else {
  await p.mouse.click(上传入口[0], 上传入口[1]); await p.waitForTimeout(1200);
  let created = [];
  for (let k = 1; k <= 20; k++) { await p.waitForTimeout(1000); created = (await R.ids()).filter((x) => !idsBefore.has(x)); if (created.length) break; }
  out.created = created;
  out.上传后积分 = await R.credits();
  log('新节点：', JSON.stringify(created), '| 积分', out.上传前积分, '→', out.上传后积分);
}

const 扫 = (时点) => p.evaluate((nm) => {
  const hits = [];
  for (const n of document.querySelectorAll('span,div,p')) {
    const t = (n.innerText || '').trim();
    if (t.length > 120 || !t.includes(nm)) continue;
    // 只要最内层（没有子元素也含这段文字的）
    if (Array.from(n.children).some((c) => (c.innerText || '').includes(nm))) continue;
    const r = n.getBoundingClientRect();
    hits.push({ 文字: t.slice(0, 100), 屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100) });
  }
  const dlg = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return { 命中: hits, 命中数: hits.length,
    资产库里有: dlg ? (dlg.innerText || '').includes(nm) : false,
    资源账: (document.body.innerText.match(/(\d+ resources?:[^\n]*)/) || [])[0] || null };
}, NAME);

const 祖先链 = () => p.evaluate((nm) => {
  for (const n of document.querySelectorAll('span,div,p')) {
    const t = (n.innerText || '').trim();
    if (t.length > 120 || !t.includes(nm)) continue;
    if (Array.from(n.children).some((c) => (c.innerText || '').includes(nm))) continue;
    const 链 = []; let e = n;
    for (let k = 0; k < 14 && e && e !== document.body; k++) { const b = e.getBoundingClientRect();
      链.push({ 层: k, tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
        aria: e.getAttribute('aria-label'), cls: (e.className || '').toString().slice(0, 60),
        屏上: [b.x, b.y, b.width, b.height].map((z) => Math.round(z * 100) / 100) });
      e = e.parentElement; }
    return 链;
  }
  return null;
}, NAME);

// 三个时点各扫一次
out.时点 = {};
for (const [名, 等] of [['上传后0.5s', 500], ['上传后2s', 1500], ['上传后5s', 3000]]) {
  await p.waitForTimeout(等);
  out.时点[名] = await 扫(名);
  log(名, '：命中', out.时点[名].命中数, '| 资产库里有 =', out.时点[名].资产库里有, '|', JSON.stringify(out.时点[名].命中.slice(0, 3)));
  if (out.时点[名].命中数 > 0 && !out.祖先链) out.祖先链 = await 祖先链();
}
if (out.祖先链) { log('祖先链：'); for (const l of out.祖先链) log(`   L${l.层} ${l.tag}${l.role ? '[role=' + l.role + ']' : ''}${l.testid ? '[testid=' + l.testid + ']' : ''}${l.aria ? '[aria=' + l.aria + ']' : ''} @${JSON.stringify(l.屏上)}`); }
else log('🔴 三个时点都没抓到那条状态串');

// 资源账此刻的样子
out.此刻账 = await p.evaluate(() => (document.body.innerText.match(/[\d]+ resources?:[^\n]*/g) || []).slice(0, 4));
log('此刻画布上的资源账：', JSON.stringify(out.此刻账));

// 收尾：删掉探针节点
const SELF = out.created && out.created.length === 1 ? out.created[0] : null;
if (SELF) {
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (pt) {
    await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(900);
    const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => /^删除/.test(e.innerText.trim()));
      if (!it) return null; const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (项) { await p.mouse.click(项[0], 项[1]); await p.waitForTimeout(1500); }
    await p.keyboard.press('Escape');
  }
  out.已删 = !(await R.ids()).includes(SELF);
  log('探针节点已删：', out.已删);
}
fs.writeFileSync('/tmp/b196d.json', JSON.stringify(out, null, 1));
await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
