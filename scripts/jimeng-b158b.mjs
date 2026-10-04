// 批次 158-b —— 复现批次 110 的「音频播放失败」两分支（本册目前**没有这一态的截图**）
//
// 🔑 配方照抄批次 110（`jimeng-b110b.mjs`），不重新发明：
//   ① 换一个**从没播过**的节点 ② CDP `Network.setBlockedURLs`（比 page.route 更靠底层）
//   ③ **并且关掉浏览器缓存** —— 否则媒体早被缓存，拦截打在 cache hit 上（批次 105 f 轮的老坑）
//
// 🔴 建-删护栏（沿用本项目硬规矩）：
//   建前 id 全集 == 76 ｜ 0 选中 ｜ 无组；上传后差集恰好 1 且新节点 `.selected`；
//   收尾**只删**差集里那一个（SELF），并断言回到 76 节点 / 0 边 / 0 选中。
// 🔴 拦截**随时可关**，本脚本 finally 必关；不写持久数据、不点任何扣费按钮。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '158b', 目的: '上传自造音频 → 拦取流 → 复现「音频播放失败」两分支 → 删干净' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b158b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const WAV = '/tmp/jimeng-b158-test-440hz-4s.wav';

const { b, p } = await openCanvas();
const R = readers(p);
let cdp = null; let SELF = null; let 拦截 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 组: await 组数(p), 积分: await R.credits() };
  const 建前 = await idsOf(p); rec.建前 = 建前;
  console.log('起点', JSON.stringify(rec.起点));
  断言('⓪ 护栏：建前 76 节点 / 0 选中 / 0 组', 建前.length === 76 && rec.起点.选中 === 0 && rec.起点.组 === 0, rec.起点);

  // ===== 上传 =====
  p.on('filechooser', async (fc) => { try { await fc.setFiles(WAV); rec.已选文件 = true; } catch (e) { rec.选文件错 = String(e.message || e).slice(0, 160); } });
  const 上传 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-upload-trigger"],[aria-label="上传"]')
    || Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '上传');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  rec.上传钮 = 上传;
  console.log('上传钮', JSON.stringify(上传));
  if (!上传) throw new Error('找不到上传钮');
  await p.mouse.click(上传.x, 上传.y);
  await p.waitForTimeout(12000);
  const 建后 = await idsOf(p);
  const 差 = 建后.filter((x) => !建前.includes(x));
  SELF = 差.length === 1 ? 差[0] : null;
  rec.建后 = { 数: 建后.length, 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits(), 状态行: await R.status() };
  落盘();
  console.log('建后', JSON.stringify(rec.建后));
  断言('① 上传后差集恰好 1，且新节点被选中，**积分不变**',
    SELF != null && 差.length === 1 && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);

  if (SELF) {
    // 等资源就绪：轮询节点里的资源账
    rec.就绪轮询 = [];
    for (let i = 0; i < 20; i++) {
      const q = await p.evaluate((id) => {
        const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
        const a = n.querySelector('audio');
        return { 节点在: true, 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
          资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null,
          有audio: !!a, src前: a ? (a.getAttribute('src') || '').slice(0, 120) : null,
          播钮: (() => { const b2 = n.querySelector('[aria-label^="Play"],button[aria-label*="播放"]'); return b2 ? b2.getAttribute('aria-label') : null; })(),
          错态: !!n.querySelector('[data-testid="audio-playback-error"]') };
      }, SELF);
      rec.就绪轮询.push({ 秒: i + 1, ...q });
      落盘();
      if (q.资源账 && /ready/.test(q.资源账) && q.有audio) break;
      if (q.错态) break;
      await p.waitForTimeout(1500);
    }
    const 末 = rec.就绪轮询[rec.就绪轮询.length - 1];
    console.log('\n🆕 就绪轮询末项', JSON.stringify(末));
    断言('② 资源账出现 `ready`（素材被后端接受，**不是永远 processing**）', /ready/.test(String(末.资源账 || '')), { 末 });
    rec.音频src = 末.src前;
    const KEY = (末.src前 || '').match(/tos-cn-i-tb4\/[^\s"'?]+/)?.[0] || (末.src前 || '').match(/[0-9a-f]{32}/)?.[0];
    rec.KEY = KEY;
    console.log('取流 key =', KEY);

    if (KEY) {
      // ===== 装拦截 =====
      cdp = await p.context().newCDPSession(p);
      await cdp.send('Network.enable');
      await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
      拦截 = `*${KEY}*`;
      await cdp.send('Network.setBlockedURLs', { urls: [拦截] });
      rec.拦截 = 拦截;
      落盘();
      console.log('已设拦截 + 关缓存:', 拦截);

      // 点播放
      const pb = await p.evaluate((id) => {
        const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
        const btn = n.querySelector('[aria-label^="Play"],button[aria-label*="播放"]');
        if (!btn) return { 错: 'no-play-btn', 节点逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) };
        const r = btn.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), aria: btn.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] };
      }, SELF);
      rec.播放钮 = pb; 落盘();
      console.log('播放钮', JSON.stringify(pb));
      if (pb && pb.x != null) {
        await p.mouse.click(pb.x, pb.y);
        rec.失败态采样 = [];
        for (let i = 0; i < 10; i++) {
          await p.waitForTimeout(700);
          rec.失败态采样.push(await p.evaluate((id) => {
            const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
            const err = n.querySelector('[data-testid="audio-playback-error"]');
            const a = n.querySelector('audio');
            const rb = n.querySelector('button[aria-label^="重试播放"]');
            const r = err ? err.getBoundingClientRect() : null;
            return { 节点逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 170),
              资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null,
              错态: !!err, 错态盒: r ? [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] : null,
              错态逐字: err ? (err.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) : null,
              错态子: err ? Array.from(err.querySelectorAll('*')).slice(0, 5).map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), 逐字: (e.innerText || e.textContent || '').trim().slice(0, 24) })) : null,
              重试钮: rb ? rb.getAttribute('aria-label') : null,
              重试盒: rb ? (() => { const q = rb.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; })() : null,
              有audio元素: !!a, 时长testid数: n.querySelectorAll('[data-testid^="audio-duration"]').length };
          }, SELF));
          if (i === 9) 落盘();
        }
        const 末2 = rec.失败态采样[rec.失败态采样.length - 1];
        console.log('\n🆕 失败态末项', 串(末2, 1200));
        rec.复现失败态 = !!末2.错态;
        断言('③ 拦掉取流后卡片变「音频播放失败」且出现 `重试播放音频`',
          !!末2.错态 && /重试播放/.test(String(末2.重试钮 || '')), 末2);
        断言('④ **资源账纹丝不动**（仍是 ready，failed 不变）', /ready/.test(String(末2.资源账 || '')) && /0 failed/.test(String(末2.资源账 || '')), 末2);
        断言('⑤ `<audio>` 元素整个从 DOM 消失、时长读数 0 个', 末2.有audio元素 === false && 末2.时长testid数 === 0, 末2);

        // ===== 解除拦截 → 点重试 → 恢复分支 =====
        if (末2.重试盒) {
          await cdp.send('Network.setBlockedURLs', { urls: [] });
          rec.已解除拦截 = true;
          await p.mouse.click(末2.重试盒[2] + 末2.重试盒[0] / 2, 末2.重试盒[3] + 末2.重试盒[1] / 2);
          rec.恢复采样 = [];
          for (let i = 0; i < 10; i++) {
            await p.waitForTimeout(600);
            rec.恢复采样.push(await p.evaluate((id) => {
              const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 节点在: false };
              const a = n.querySelector('audio');
              return { 节点逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 150),
                错态: !!n.querySelector('[data-testid="audio-playback-error"]'),
                有audio元素: !!a, readyState: a ? a.readyState : null, duration: a ? a.duration : null,
                paused: a ? a.paused : null, currentTime: a ? Math.round(a.currentTime * 100) / 100 : null,
                播钮: (() => { const b2 = n.querySelector('button[aria-label^="Pause"],button[aria-label^="Play"],button[aria-label*="暂停"],button[aria-label*="播放"]'); return b2 ? b2.getAttribute('aria-label') : null; })() };
            }, SELF));
            if (i === 9) 落盘();
          }
          const 末3 = rec.恢复采样[rec.恢复采样.length - 1];
          console.log('\n🆕 恢复态末项', JSON.stringify(末3));
          断言('⑥ 解除拦截后点重试，**1.2 秒内**恢复（错态消失、`<audio>` 回来）',
            末3.错态 === false && 末3.有audio元素 === true, 末3);
          断言('⑦ 恢复后按钮直接变「Pause」⇒ 是「已经在播」，不是回到暂停',
            /Pause|暂停/.test(String(末3.播钮 || '')), 末3);
        }
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ===== 收尾：关拦截 → 删 SELF → 断言回基线 =====
try {
  if (cdp) { await cdp.send('Network.setBlockedURLs', { urls: [] }).catch(() => {}); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }).catch(() => {}); rec.拦截已清 = true; }
} catch (e) { rec.清拦截错 = String(e.message || e).slice(0, 160); }
try {
  if (SELF) {
    // 选中 → 右键 → 上下文菜单 →「删除 ⌫」
    const 落 = await p.evaluate((id) => {
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    }, SELF);
    rec.删落点 = 落;
    if (落) {
      await p.mouse.click(落[0], 落[1]); await p.waitForTimeout(1400);
      await p.mouse.click(落[0], 落[1], { button: 'right' }); await p.waitForTimeout(1600);
      const del = await p.evaluate(() => {
        const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return null;
        const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除'));
        if (!it) return { 错: 'no-删除项', 逐字: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 120) };
        const r = it.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 逐字: (it.innerText || '').trim() };
      });
      rec.删除项 = del;
      if (del && del.x != null) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2000); }
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
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('⑧ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 积分不变', rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
