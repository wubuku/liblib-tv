// 批次 158-a —— 普查画布上**带媒体的音频节点**，并读出各自的播放取流 key
//
// 🎯 靶子：`10-tasks/media-playback.md:386-391` 至今仍写着
//    「**仍未验证**：资源失效后的『重试播放』与空载态」，
//    而**同一个文件上方**「### 重试播放的两个分支（2026-10-03 批次 110 实测，两个分支都测到了）」
//    已经把两个分支的完整读数记下来了，`AUDIT.md:3800-3801` 也把它记成 ✅ 正面。
//    ⇒ 🔴 **正文这一段从未回填，是陈旧记述**，不是真的没测。
//    本轮做两件事：① 静态订正它；② **现场复现批次 110 的读数**，确认它今天仍然成立
//       （顺带补一张「音频播放失败」态的截图——本册目前没有这一态的图）。
//
// 🔑 批次 110 的配方（照抄，不重新发明）：
//   「换一个**从没播过**的节点」＋「换 `Network.setBlockedURLs` 这种更靠底层的手段」
//   ＋「**并且关掉浏览器缓存** —— 否则媒体早被缓存，拦截打在 cache hit 上」。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const rec = { 批次: '158a', 目的: '普查带媒体的音频节点 + 读播放取流 key' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b158a.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length), zoom: await R.zoom(), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ⚠️ getAttribute 与可见性无关 ⇒ 即使节点在视口外也能读到 src
  rec.普查 = await p.evaluate(() => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    const 在屏 = (r) => r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight;
    return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const id = n.getAttribute('data-id');
      const a = n.querySelector('audio');
      const v = n.querySelector('video');
      const 资源账 = ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || null;
      const 播钮 = n.querySelector('[data-testid="audio-simple-player"] button,[aria-label^="Play "],[aria-label^="播放"]');
      return { id, 标题: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
        有audio元素: !!a, 有video元素: !!v,
        音频src: a ? (a.getAttribute('src') || '').slice(0, 130) : null,
        视频src: v ? (v.getAttribute('src') || '').slice(0, 130) : null,
        资源账, 有播钮: !!播钮,
        播钮aria: 播钮 ? 播钮.getAttribute('aria-label') : null,
        盒: 盒(n), 在屏: 在屏(n.getBoundingClientRect()) };
    }).filter((z) => z.有audio元素 || z.有video元素 || z.有播钮);
  });
  落盘();
  const 有媒体 = rec.普查.filter((z) => z.有audio元素 || z.有video元素);
  console.log('\n=== 带 <audio>/<video> 元素的节点', 有媒体.length, '个 ===');
  for (const z of 有媒体) console.log(' ', z.id, '|', z.标题, '| audio', z.有audio元素, '| video', z.有video元素,
    '| 资源账', z.资源账, '| 在屏', z.在屏, '| 盒', JSON.stringify(z.盒));
  console.log('\n=== 播钮节点', rec.普查.filter((z) => z.有播钮).length, '个 ===');
  for (const z of rec.普查.filter((x) => x.有播钮)) console.log(' ', z.id, '|', z.播钮aria, '| 在屏', z.在屏, '| 盒', JSON.stringify(z.盒));
  console.log('\n=== 唯一 key 统计 ===');
  const keys = [...new Set(有媒体.map((z) => (z.音频src || z.视频src || '').match(/tos-cn-i-tb4\/[^\s"']+|[0-9a-f]{32}/)?.[0]).filter(Boolean))];
  console.log(keys);
  rec.keys = keys;
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); 落盘(); }
rec.收尾 = { 浮层: await R.overlays(), 积分: await R.credits() };
落盘();
console.log('异常', rec.异常 || '无');
process.exit(0);
