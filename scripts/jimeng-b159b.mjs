// 批次 159-b —— 用**正确的段**重跑「音频播放失败」两分支，并抓全册至今没有的那张截图
//
// 🔑 起因（批次 159-a 考古结论）：批次 158 拦的是取流 URL 的**第 1 段**（域名后紧跟的
//    32 位 hex），而批次 110 真正拦的是 **`tos-cn-v-148450/` 后面那一段 32 位混合大小写
//    key**（b110c 的正则 `/tos-cn-v-148450\/([A-Za-z0-9]+)\//`，落盘 key = `oERcOtF…`）。
//    `20-reference.md` 表格里早把它叫「**播放取流 key**」并写着「正确做法：从 `<audio>` 的
//    `src` 里取 key」—— 是本轮自己挑了没被验过的那一段。
//    ⇒ 本轮把两段**都记下来**，只拦**末段**那个。
//
// 🖼 本册至今**没有**「音频播放失败」态的截图（158d 的拍图分支没进）⇒ 本轮补上 `119`。
//
// 🔴 建-删护栏：建后差集恰好 1 且新节点选中、积分不变；收尾右键 → 上下文菜单 →「删除」
//    后断言回到 76 节点 / 0 选中 / 0 浮层 / 积分不变。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '159b', 目的: '用末段播放取流 key 精确拦 → 复现失败态两分支 → 拍 119' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b159b.json', import.meta.url), JSON.stringify(rec, null, 1));
const WAV = '/tmp/jimeng-b158-test-440hz-4s.wav';
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

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
  if (!SELF) throw new Error('自建节点没建成，停在这里');

  // ===== ① 不拦先播一次 → 从 CDP 事件流抓真实 Media URL =====
  cdp = await p.context().newCDPSession(p);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  const 请求 = [];
  cdp.on('Network.requestWillBeSent', (e) => { 请求.push({ 类型: e.type, url: (e.request.url || '').slice(0, 240) }); });

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

  const media = 请求.filter((z) => /Media/i.test(String(z.类型)));
  const url = (media[0] && media[0].url) || '';
  rec.抓到的URL = url;
  // 🔑 两段都记：第 1 段（批次 158 拦错的那段）vs 末段（批次 110 拦对的那段）
  rec.两段 = {
    第1段: (url.match(/^https:\/\/[^/]+\/([0-9a-f]{32})\//) || [])[1] || null,
    末段: (url.match(/tos-cn-v-148450\/([A-Za-z0-9]+)\//) || [])[1] || null,
  };
  console.log('两段 =', JSON.stringify(rec.两段));
  断言('① 抓到 Media URL，且**两段都能解析出来**', !!(rec.两段.第1段 && rec.两段.末段), rec.两段);
  const KEY = rec.两段.末段;

  if (KEY) {
    // ===== ② 拦**末段** + 重载页面 =====
    await cdp.send('Network.setBlockedURLs', { urls: ['*' + KEY + '*'] });
    rec.拦截 = '*' + KEY + '*';
    rec.拦的是哪一段 = '**末段**（`tos-cn-v-148450/` 后面那个 32 位 key）—— 批次 110 的成功配方';
    await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await p.waitForTimeout(11000);
    rec.重载后节点在 = await p.evaluate((id) => !!document.querySelector('.react-flow__node[data-id="' + id + '"]'), SELF);
    rec.重载后节点数 = (await idsOf(p)).length;
    断言('② 重载后自建节点仍在（上传是持久的）', rec.重载后节点在 === true, rec);
    await setZoom(p, 60); await p.waitForTimeout(1200);

    // 🔴 立规 26：播放钮只在**选中态**渲染 ⇒ 先选中再找
    const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect();
      return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在屏: r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight }; }, SELF);
    rec.重载后选中落 = 落;
    rec.重载后未选中时逐字 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) : null; }, SELF);
    rec.重载后未选中时播放钮 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      if (!n) return '节点不在'; const btn = n.querySelector('button[aria-label^="Play"]'); return btn ? btn.getAttribute('aria-label') : null; }, SELF);
    if (落 && 落.在屏) { await p.mouse.click(落.点[0], 落.点[1]); await p.waitForTimeout(1800); }
    rec.重载后选中数 = await selCount(p);

    const pb2 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 错: '节点不在' };
      const btn = n.querySelector('button[aria-label^="Play"]'); if (!btn) return { 错: 'no-play' };
      const r = btn.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, SELF);
    rec.重播钮 = pb2;
    if (pb2 && pb2.x != null) {
      await p.mouse.click(pb2.x, pb2.y);
      rec.采样 = [];
      for (let i = 0; i < 14; i++) {
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
        if (s.错态) { 落盘(); break; }
      }
      const 末 = rec.采样[rec.采样.length - 1];
      rec.失败态 = 末;
      console.log('\n🆕 失败态', JSON.stringify(末).slice(0, 700));
      断言('③ 🔴 **拦末段这次真的打中了**：出现 `音频播放失败` 且 `重试播放音频`', !!末.错态 && /重试播放/.test(String(末.重试钮 || '')), 末);
      断言('④ **资源账纹丝不动**（仍 1 ready / 0 failed）', /1 ready/.test(String(末.资源账 || '')) && /0 failed/.test(String(末.资源账 || '')), 末);
      断言('⑤ `<audio>` 从 DOM 消失、时长读数 0 个', 末.有audio === false && 末.时长testid数 === 0, 末);

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
        await p.mouse.click(末.重试盒[2] + 末.重试盒[0] / 2, 末.重试盒[3] + 末.重试盒[1] / 2);
        rec.恢复采样 = [];
        for (let i = 0; i < 16; i++) {
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
        断言('⑥ 解除拦截后点重试：错态消失、`<audio>` 回来', 末2.错态 === false && 末2.有audio === true, 末2);
        断言('⑦ 恢复后按钮直接变 **Pause** ⇒「已经在播」不是回到暂停', /Pause/.test(String(末2.播钮 || '')), 末2);
      }
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
断言('⑧ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 积分不变', rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
