// 批次 158-c —— 复现「音频播放失败」态：**按扩展名拦**，并用 CDP 请求事件把**真 key 抓出来**
//
// 🔴 158-b 踩到的坑（写下来免得下一轮再踩）：
//   **`<audio>` 元素在点播放之前根本不在 DOM 里。**
//   158-b 的做法是「先读 `src` 拿到 key → 再按 key 拦 → 再点播放」，
//   于是 `src` 读到 `null`、`KEY` 为 `undefined`、拦截根本没装上，整段实验被跳过。
//   ⇒ 📌 立规 25：**「先知道要拦什么、再触发它」在「元素是懒创建的」场景下不成立**。
//      正确顺序是「**先拦宽一点、再触发、再从事件流里读出真值**」。
//
// ✅ 本轮：装 `Network.setBlockedURLs`（按 `*.wav` / `*.mp4` / `*.m4a` / `*.mp3` / `*.aac`）
//    ＋ `setCacheDisabled(true)`（批次 105 f 轮老坑：否则媒体早被缓存，拦截打在 cache hit 上）
//    → 点播放 → 采失败态 → **从 `Network.requestWillBeSent` 里捞真 key** → 拍图
//    → 解除拦截 → 点「重试播放音频」→ 采恢复态 → 删干净。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '158c', 目的: '按扩展名拦取流 → 复现「音频播放失败」两分支 + 抓真 key + 拍图' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b158c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const WAV = '/tmp/jimeng-b158-test-440hz-4s.wav';
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const { b, p } = await openCanvas();
const R = readers(p);
let cdp = null; let SELF = null; const 请求 = [];
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 组: await 组数(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));
  断言('⓪ 护栏：建前 76 节点 / 0 选中 / 0 组', 建前.length === 76 && rec.起点.选中 === 0 && rec.起点.组 === 0, rec.起点);

  // ---- 上传 ----
  p.on('filechooser', async (fc) => { try { await fc.setFiles(WAV); rec.已选文件 = true; } catch (e) { rec.选文件错 = String(e.message || e).slice(0, 160); } });
  const 上传 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '上传');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!上传) throw new Error('找不到上传钮');
  await p.mouse.click(上传[0], 上传[1]);
  await p.waitForTimeout(12000);
  const 建后 = await idsOf(p);
  const 差 = 建后.filter((x) => !建前.includes(x));
  SELF = 差.length === 1 ? 差[0] : null;
  rec.建后 = { 数: 建后.length, 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits() };
  落盘();
  console.log('建后', JSON.stringify(rec.建后));
  断言('① 差集恰好 1、新节点选中、**积分不变**', SELF != null && 差.length === 1 && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);

  if (SELF) {
    // 等资源 ready
    let 账 = null;
    for (let i = 0; i < 20; i++) {
      const q = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
        return { 资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null,
          播钮: (() => { const b2 = n.querySelector('button[aria-label^="Play"]'); return b2 ? b2.getAttribute('aria-label') : null; })() }; }, SELF);
      if (q.资源账 && /ready/.test(q.资源账)) { 账 = q; rec.就绪 = { 秒: i + 1, ...q }; break; }
      await p.waitForTimeout(1500);
    }
    console.log('就绪', JSON.stringify(rec.就绪));
    断言('② 资源账出现 `ready`', !!账, rec.就绪);

    // ---- 装拦截（按扩展名）+ 抓请求流 ----
    cdp = await p.context().newCDPSession(p);
    await cdp.send('Network.enable');
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    cdp.on('Network.requestWillBeSent', (e) => { 请求.push({ url: (e.request.url || '').slice(0, 200), 类型: e.type }); });
    cdp.on('Network.loadingFailed', (e) => { 请求.push({ 失败: e.errorText, 类型: e.type }); });
    const 模式 = ['*.wav*', '*.mp4*', '*.m4a*', '*.mp3*', '*.aac*'];
    await cdp.send('Network.setBlockedURLs', { urls: 模式 });
    rec.拦截模式 = 模式;
    落盘();
    console.log('已装拦截 + 关缓存:', JSON.stringify(模式));

    // ---- 点播放 ----
    const pb = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const btn = n.querySelector('button[aria-label^="Play"]'); if (!btn) return { 错: 'no-play' };
      const r = btn.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), aria: btn.getAttribute('aria-label'),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }, SELF);
    rec.播放钮 = pb;
    console.log('播放钮', JSON.stringify(pb));
    if (pb && pb.x != null) {
      await p.mouse.click(pb.x, pb.y);
      rec.失败态采样 = [];
      for (let i = 0; i < 10; i++) {
        await p.waitForTimeout(700);
        const s = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
          const err = n.querySelector('[data-testid="audio-playback-error"]');
          const a = n.querySelector('audio');
          const rb = n.querySelector('button[aria-label^="重试播放"]');
          const r = err ? err.getBoundingClientRect() : null;
          return { 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 170),
            资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null,
            错态: !!err, 错态盒: r ? [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] : null,
            错态逐字: err ? (err.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) : null,
            错态结构: err ? Array.from(err.querySelectorAll('*')).slice(0, 6).map((e) => ({ tag: e.tagName, role: e.getAttribute('role'),
              aria: e.getAttribute('aria-label'), 逐字: (e.innerText || e.textContent || '').trim().slice(0, 24) })) : null,
            重试钮: rb ? rb.getAttribute('aria-label') : null,
            重试盒: rb ? (() => { const q = rb.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; })() : null,
            有audio: !!a, 时长testid数: n.querySelectorAll('[data-testid^="audio-duration"]').length }; }, SELF);
        rec.失败态采样.push(s);
        if (s.错态) { 落盘(); break; }
      }
      const 末 = rec.失败态采样[rec.失败态采样.length - 1];
      rec.失败态 = 末;
      console.log('\n🆕 失败态', 串(末, 1400));
      // 🆕 从请求流里捞真 key
      const 媒体请求 = 请求.filter((z) => z.url && /\.(wav|mp4|m4a|mp3|aac)/i.test(z.url));
      rec.媒体请求 = 媒体请求;
      rec.真key = 媒体请求.length ? (媒体请求[0].url.match(/tos-cn-i-tb4\/[^\s"'?]+/)?.[0] || 媒体请求[0].url) : null;
      console.log('🆕 媒体请求', 串(媒体请求, 900));
      console.log('🆕 真 key =', rec.真key);
      落盘();
      断言('③ 拦掉取流后卡片变「音频播放失败」且出现 `重试播放音频`', !!末.错态 && /重试播放/.test(String(末.重试钮 || '')), 末);
      断言('④ **资源账纹丝不动**（仍 ready / 0 failed）', /1 ready/.test(String(末.资源账 || '')) && /0 failed/.test(String(末.资源账 || '')), 末);
      断言('⑤ `<audio>` 元素从 DOM 消失、时长读数 0 个', 末.有audio === false && 末.时长testid数 === 0, 末);

      if (末.错态 && 末.错态盒) {
        // 拍图（失败态）
        rec.hl = await p.evaluate((bx) => { const ov = document.createElement('div'); ov.id = '__hl__';
          ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (bx[2] - 4) + 'px;top:' + (bx[3] - 4) + 'px;width:' + (bx[0] + 8) + 'px;height:' + (bx[1] + 8) + 'px;';
          document.body.appendChild(ov); return true; }, 末.错态盒);
        await p.waitForTimeout(500);
        await p.screenshot({ path: new URL('./119-audio-playback-error-retry.png', 出图).pathname });
        rec.图 = 'screenshots/119-audio-playback-error-retry.png';
        await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
        console.log('① 已拍 119');

        // ---- 解除拦截 → 点重试 → 恢复分支 ----
        await cdp.send('Network.setBlockedURLs', { urls: [] });
        rec.已解除 = true;
        await p.mouse.click(末.重试盒[2] + 末.重试盒[0] / 2, 末.重试盒[3] + 末.重试盒[1] / 2);
        rec.恢复采样 = [];
        for (let i = 0; i < 12; i++) {
          await p.waitForTimeout(600);
          const s = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
            const a = n.querySelector('audio');
            return { 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 150),
              错态: !!n.querySelector('[data-testid="audio-playback-error"]'),
              有audio: !!a, readyState: a ? a.readyState : null, duration: a ? a.duration : null,
              paused: a ? a.paused : null, currentTime: a ? Math.round(a.currentTime * 100) / 100 : null,
              播钮: (() => { const b2 = n.querySelector('button[aria-label^="Pause"],button[aria-label^="Play"]'); return b2 ? b2.getAttribute('aria-label') : null; })() }; }, SELF);
          rec.恢复采样.push(s);
          if (!s.错态 && s.有audio) { 落盘(); break; }
        }
        const 末2 = rec.恢复采样[rec.恢复采样.length - 1];
        rec.恢复态 = 末2;
        console.log('🆕 恢复态', JSON.stringify(末2));
        断言('⑥ 解除拦截后点重试，错态消失、`<audio>` 回来', 末2.错态 === false && 末2.有audio === true, 末2);
        断言('⑦ 恢复后按钮直接变 **Pause** ⇒「已经在播」不是回到暂停', /Pause/.test(String(末2.播钮 || '')), 末2);
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ---- 收尾：关拦截 → 删 SELF ----
try { if (cdp) { await cdp.send('Network.setBlockedURLs', { urls: [] }).catch(() => {}); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }).catch(() => {}); rec.拦截已清 = true; } } catch (e) {}
try {
  if (SELF) {
    const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
    if (落) {
      await p.mouse.click(落[0], 落[1]); await p.waitForTimeout(1400);
      await p.mouse.click(落[0], 落[1], { button: 'right' }); await p.waitForTimeout(1600);
      const del = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return null;
        const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')); if (!it) return { 错: 1 };
        const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      rec.删除落点 = del;
      if (del && !del.错) { await p.mouse.click(del[0], del[1]); await p.waitForTimeout(2000); }
    }
    for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }
} catch (e) { rec.删异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

try { await settle(p, R); } catch (e) {}
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') {
  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
}
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.SELF = SELF;
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无', '| 删异常', rec.删异常 || '无');
断言('⑧ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 积分不变', rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
