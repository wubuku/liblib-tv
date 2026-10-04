// 批次 159-c —— 🔴 按批次 110 的**原配方**重跑：不重载页面，直接 `a.load()` 强制重新取流
//
// 🔑 两轮自我订正走到这里：
//   158d：拦「第 1 段 hex」＋**重载页面** ⇒ 没打中
//   159b：拦「末段 key」（= 批次 110 用的那一段）＋**重载页面** ⇒ 仍然没打中
//   159a 考古：批次 110 全程**没有重载页面**，它是在同一页面里直接
//         `document.querySelector('audio').load()` **强制重新取流**
//         （`jimeng-b110e.mjs:86-91` 逐字：`a.load()`）。
//   ⇒ 本轮去掉「重载」这一步，并加上 **`Network.loadingFailed` 计 `blockedReason`**，
//     这样「拦截到底有没有生效」是**量出来的**，不是从界面反推的。
//
// 🔴 建-删护栏同 159-b。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '159c', 目的: '不重载页面 + a.load() 强制重取流 → 拦到底生不生效（用 blockedReason 量）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b159c.json', import.meta.url), JSON.stringify(rec, null, 1));
const WAV = '/tmp/jimeng-b158-test-440hz-4s.wav';
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const { b, p } = await openCanvas();
const R = readers(p);
let cdp = null; let SELF = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 组: await 组数(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  p.on('filechooser', async (fc) => { try { await fc.setFiles(WAV); rec.已选文件 = true; } catch (e) { rec.选文件错 = String(e.message || e).slice(0, 160); } });
  const 上传 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '上传');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(上传[0], 上传[1]);
  await p.waitForTimeout(12000);
  const 建后 = await idsOf(p);
  const 差 = 建后.filter((x) => !建前.includes(x));
  SELF = 差.length === 1 ? 差[0] : null;
  rec.建后 = { 数: 建后.length, 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits() };
  落盘();
  console.log('建后', JSON.stringify(rec.建后));
  断言('⓪ 差集恰好 1、新节点选中、**积分不变**', SELF != null && 差.length === 1 && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);
  if (!SELF) throw new Error('自建节点没建成');

  // ===== ① 装监听 → 点播一次（不拦）→ 抓 Media URL =====
  cdp = await p.context().newCDPSession(p);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  let 命中 = [];
  cdp.on('Network.requestWillBeSent', (e) => { if (e.type === 'Media') 命中.push({ k: 'req', url: (e.request.url || '').slice(0, 200) }); });
  cdp.on('Network.loadingFailed', (e) => { if (e.type === 'Media') 命中.push({ k: 'failed', reason: e.blockedReason || null, err: e.errorText || null }); });

  for (let i = 0; i < 20; i++) {
    const q = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
      return { 资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null }; }, SELF);
    if (q.资源账 && /ready/.test(q.资源账)) { rec.就绪秒 = i + 1; break; }
    await p.waitForTimeout(1500);
  }
  const pb = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 错: '节点不在' };
    const btn = n.querySelector('button[aria-label^="Play"]'); if (!btn) return { 错: 'no-play' };
    const r = btn.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), aria: btn.getAttribute('aria-label') }; }, SELF);
  rec.播放钮 = pb;
  await p.mouse.click(pb.x, pb.y);
  await p.waitForTimeout(4000);

  const req = 命中.filter((z) => z.k === 'req');
  const url = (req[0] && req[0].url) || '';
  rec.抓到的URL = url;
  rec.两段 = {
    第1段: (url.match(/^https:\/\/[^/]+\/([0-9a-f]{32})\//) || [])[1] || null,
    末段: (url.match(/tos-cn-v-148450\/([A-Za-z0-9]+)\//) || [])[1] || null,
  };
  console.log('两段 =', JSON.stringify(rec.两段), '| 首播请求数 =', req.length);
  const KEY = rec.两段.末段;
  断言('① 抓到 Media URL 且末段 key 解析成功', !!KEY, rec.两段);

  if (KEY) {
    // ===== ② 装拦截（**不重载页面**）→ a.load() 强制重新取流 =====
    命中 = [];
    await cdp.send('Network.setBlockedURLs', { urls: ['*' + KEY + '*'] });
    rec.拦截 = '*' + KEY + '*';
    rec.拦的是哪一段 = '**末段**（`tos-cn-v-148450/` 后面那个 32 位 key），与批次 110 b110c/d/e 逐字同一段';
    rec.与110的差别 = '**没有重载页面**；改为在页面内 `a.load()` 强制重新取流（`jimeng-b110e.mjs:86-91` 的原配方）';

    const forced = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      const a = n && n.querySelector('audio'); if (!a) return { __err: 'no-audio' };
      const src = (a.getAttribute('src') || '').slice(0, 200);
      a.load();
      return { ok: true, src, readyState: a.readyState, networkState: a.networkState }; }, SELF);
    rec.强制load = forced;
    落盘();
    console.log('a.load() =', JSON.stringify(forced).slice(0, 300));
    断言('② 页面内 `a.load()` 找得到 `<audio>` 元素', !!forced && !forced.__err, forced);

    rec.采样 = [];
    for (let i = 0; i < 16; i++) {
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
      rec.采样.push(s);
      rec.命中快照 = 命中.slice(-8);
      落盘();
      if (s.错态) break;
    }
    const 末 = rec.采样[rec.采样.length - 1];
    rec.失败态 = 末;
    rec.拦截事件 = 命中.slice();
    const 被拦次数 = 命中.filter((z) => z.k === 'failed' && z.reason).length;
    rec.被拦次数 = 被拦次数;
    console.log('\n🆕 失败态 =', JSON.stringify(末).slice(0, 600));
    console.log('🆕 Media 事件 =', JSON.stringify(命中).slice(0, 600));
    落盘();
    断言('③ ⭐ **拦截真的生效**（`loadingFailed` 带 `blockedReason`）', 被拦次数 > 0, { 被拦次数, 事件: 命中.slice(0, 6) });
    断言('④ ⭐ **失败态出现**：`音频播放失败` ＋ `重试播放音频`', !!末.错态 && /重试播放/.test(String(末.重试钮 || '')), 末);
    断言('⑤ **资源账纹丝不动**（仍 1 ready / 0 failed）', /1 ready/.test(String(末.资源账 || '')) && /0 failed/.test(String(末.资源账 || '')), 末);
    断言('⑥ `<audio>` 从 DOM 消失、时长读数 0 个', 末.有audio === false && 末.时长testid数 === 0, 末);

    if (末.错态 && 末.错态盒) {
      await p.evaluate((bx) => { const ov = document.createElement('div'); ov.id = '__hl__';
        ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (bx[2] - 4) + 'px;top:' + (bx[3] - 4) + 'px;width:' + (bx[0] + 8) + 'px;height:' + (bx[1] + 8) + 'px;';
        document.body.appendChild(ov); return true; }, 末.错态盒);
      await p.waitForTimeout(600);
      await p.screenshot({ path: new URL('./119-audio-playback-error-retry.png', 出图).pathname });
      rec.图 = 'screenshots/119-audio-playback-error-retry.png';
      await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
      console.log('🖼 已拍 119');

      await cdp.send('Network.setBlockedURLs', { urls: [] });
      rec.已解除 = true;
      命中 = [];
      await p.mouse.click(末.重试盒[2] + 末.重试盒[0] / 2, 末.重试盒[3] + 末.重试盒[1] / 2);
      rec.恢复采样 = [];
      for (let i = 0; i < 18; i++) {
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
      rec.恢复期事件 = 命中.slice();
      console.log('🆕 恢复态 =', JSON.stringify(末2));
      断言('⑦ 解除拦截后点重试：错态消失、`<audio>` 回来', 末2.错态 === false && 末2.有audio === true, 末2);
      断言('⑧ 恢复后按钮直接变 **Pause** ⇒「已经在播」不是回到暂停', /Pause/.test(String(末2.播钮 || '')), 末2);
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { if (cdp) { await cdp.send('Network.setBlockedURLs', { urls: [] }).catch(() => {}); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }).catch(() => {}); rec.拦截已清 = true; } } catch (e) {}
try {
  if (SELF) {
    const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
    if (落) {
      await p.mouse.click(落[0], 落[1]); await p.waitForTimeout(1400);
      await p.mouse.click(落[0], 落[1], { button: 'right' }); await p.waitForTimeout(1700);
      const del = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return { 错: 'no-menu' };
        const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')); if (!it) return { 错: 'no-删除项' };
        const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      rec.删除落点 = del;
      if (del && !del.错) { await p.mouse.click(del[0], del[1]); await p.waitForTimeout(2200); }
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
断言('⑨ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 积分不变', rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
