// 批次 101 · a 轮：**解除 `media-playback.md` 的素材阻塞**。
//
// 🔑 **全册最陈旧的一页**（普查 78，120 行）被一条阻塞卡住：
//    「双击重播 / 进度条点击跳转 / 拖动音量滑杆」三项**需要一个能播的视频节点**，
//    批次 62 写明「这是**素材限制**，条件一变（能拿到可播的视频）就该回来测」。
//    ⇒ 但**解除阻塞的路径一直没人走过**：批次 64 已经实测过
//    「左栏上传支持**视频 20 种**格式，**上传免费**（805→805）」。
//    ⇒ 本轮用 OpenCV 自造一个 H.264 测试视频（640×360 / 6 秒 / 画面逐帧带秒数），
//    **走上传通道**造出带媒体的视频节点。
//
// 视频内容是**为肉眼验证设计的**：逐帧大号秒数 + 帧号 + 横向往复的方块
// ⇒ 画面只要在动，就能证明「正在播放」，不依赖任何时间读数。
//
// 🔴 三条纪律：
//   ① **护栏同批次 97**：上传前存全画布 id 集合 → 上传后取差集 → `SELF` **只能来自差集**，
//      绝不用「取最后一个」「取 selected 的」猜。收尾**只删 `SELF`**。
//   ② **每步回读积分**：视频上传是否免费**此前没验过**（批次 64 只验过 PNG）。
//   ③ **不上传进 git**：素材放 `/tmp`，符合仓库卫生。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const VIDEO = '/tmp/jimeng-b101-test-avc1.mp4';

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await setZoom(60);

// ---- 护栏 ①：上传前的 id 集合 ----
const idsBefore = new Set(await allIds());
out.idsBefore = idsBefore.size;
out.creditsBefore = await credits();
log('上传前：id 数', idsBefore.size, '｜积分', out.creditsBefore);

// ---- 定位左栏「上传」并挂上 filechooser 监听（**必须全局 on**，waitForEvent 在 CDP 下超时）----
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
out.rail = rail;
log('左栏上传入口：', JSON.stringify(rail));

if (!rail.length) { log('🔴 找不到上传入口 ⇒ 停止（不上传不删除）'); }
else {
  let chooserSeen = null;
  p.on('filechooser', async (fc) => {
    chooserSeen = { multiple: fc.isMultiple() };
    log('   filechooser 触发，isMultiple =', fc.isMultiple());
    try { await fc.setFiles(VIDEO); log('   已 setFiles：', VIDEO); }
    catch (e) { log('   setFiles 失败：', e.message); }
  });

  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(700);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(2500);
  out.chooser = chooserSeen;

  // 服务端处理可能要时间，轮询等节点出现
  let created = [];
  for (let k = 1; k <= 20; k++) {
    await p.waitForTimeout(1500);
    const now = await allIds();
    created = now.filter((id) => !idsBefore.has(id));
    if (created.length) { out.gotAtMs = k * 1500; break; }
  }
  out.created = created;
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const newSel = selIds.filter((id) => !idsBefore.has(id));
  out.guard = { before: idsBefore.size, after: (await allIds()).length, created, selIds, newSel };
  out.creditsAfterUpload = await credits();
  log('护栏：', JSON.stringify(out.guard));
  log('上传后积分：', out.creditsAfterUpload, '（上传前', out.creditsBefore, '）');

  const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');

  if (SELF) {
    out.selfInfo = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), cls: n.className, translate: n.style.transform,
        screen: `${Math.round(r.width * 100) / 100}×${Math.round(r.height * 100) / 100}@${Math.round(r.x)},${Math.round(r.y)}`,
        innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 80),
        innerTestids: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
        innerAria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
        media: Array.from(n.querySelectorAll('video,audio')).map((e) => ({ tag: e.tagName,
          src: (e.getAttribute('src') || '').slice(0, 90), currentSrc: (e.currentSrc || '').slice(0, 90),
          paused: e.paused, dur: e.duration, muted: e.muted, vol: e.volume, readyState: e.readyState,
          w: e.videoWidth, h: e.videoHeight, loop: e.loop })),
        imgs: Array.from(n.querySelectorAll('img')).map((e) => ({ src: (e.getAttribute('src') || '').slice(0, 80),
          nw: e.naturalWidth, nh: e.naturalHeight })) }; }, SELF);
    log('SELF 结构：', JSON.stringify(out.selfInfo, null, 1));
  }
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow() };
log('本轮终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b101a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
