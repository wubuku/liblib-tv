// 批次 195 b 轮：自造 6 秒 H.264 素材，走左栏上传通道建出**带媒体的视频节点**。
//
// 为什么造：a 轮普查实测**画布上 76 个节点里没有任何带媒体的视频/音频节点**
//   （`视频 1` 资源账 = null、无 <video>、按钮只有 Add tags）
//   ⇒ media-playback.md 的三档表（未选中 / 已选中未播 / 正在播）本轮**无法直接复测**，
//   必须先把「素材限制」解掉（沿用批次 101 的路子，第二次证明「素材限制＝没人造过」）。
//
// 🔴 三条纪律（同批次 101）：
//   ① 护栏：上传前存全画布 id 集合 → SELF **只能来自差集**，收尾**只删 SELF**。
//   ② 每步回读积分：视频上传是否免费此前只在批次 101 量过一次（805→805），本轮再验一次。
//   ③ 素材放 /tmp，不入 git。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const VIDEO = '/tmp/jimeng-b195-test.mp4';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);

const out = { 轮次: 'b195b', 素材: VIDEO, 起点: { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() } };
const log = (...a) => console.log(a.join(' '));
log('起点：', JSON.stringify(out.起点));

await setZoom(p, 50);

// ---- 护栏 ① ----
const idsBefore = new Set(基线.ids);
out.creditsBefore = await R.credits();

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
out.rail = rail;
log('左栏上传入口：', JSON.stringify(rail));

if (!rail.length) {
  log('🔴 找不到上传入口 ⇒ 停止（不上传不删除）');
} else {
  let chooserSeen = null;
  p.on('filechooser', async (fc) => {
    chooserSeen = { multiple: fc.isMultiple() };
    try { await fc.setFiles(VIDEO); log('   已 setFiles'); }
    catch (e) { log('   setFiles 失败：', e.message); }
  });

  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(700);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(2500);
  out.chooser = chooserSeen;

  let created = [];
  for (let k = 1; k <= 24; k++) {
    await p.waitForTimeout(1500);
    const now = await R.ids();
    created = now.filter((id) => !idsBefore.has(id));
    if (created.length) { out.gotAtMs = k * 1500; break; }
  }
  out.created = created;
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const newSel = selIds.filter((id) => !idsBefore.has(id));
  out.creditsAfterUpload = await R.credits();
  log('护栏：', JSON.stringify({ created, selIds, newSel, 积分前: out.creditsBefore, 积分后: out.creditsAfterUpload }));

  const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');

  if (SELF) {
    // 等资源处理完（上传即入账，但 processing→ready 需要时间）
    out.账序列 = [];
    for (let k = 0; k < 12; k++) {
      const t = await p.evaluate((i) => {
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        if (!n) return { 消失: true };
        const s = (n.innerText || '') + ' || ' + (n.getAttribute('aria-label') || '');
        const m = /((?:\d+ resources?:|No resources:)[^|]*)/.exec(s);
        return { 账: m ? m[0].trim() : null, video: n.querySelectorAll('video').length, img: n.querySelectorAll('img').length,
                 innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) };
      }, SELF);
      out.账序列.push({ 第几次采样: k + 1, ...t });
      if (t.账 && /1 ready/.test(t.账)) { out.就绪于第几次 = k + 1; break; }
      await p.waitForTimeout(2000);
    }
    log('账序列：', JSON.stringify(out.账序列, null, 1));
  }
}

out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
fs.writeFileSync('/tmp/b195b.json', JSON.stringify(out, null, 1));
await b.close();
