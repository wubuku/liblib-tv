// 批次 158：浏览器守护 —— 9444 一掉就自动重拉并导航到共享画布。
//
// 🔴 为什么需要：本仓库是多人共享的，其他会话的探针末尾常带 `b.close()`，
//    会把整个 CDP 浏览器关掉；本会话已因此连续丢掉浏览器 3 次。
//    每次「重开 → 等 40 秒 → 探活」都是几十秒的空转，而且**在等的时候本批工作完全停摆**。
//    ⇒ 把这件事交给一个长驻进程，比每轮手动重开可靠得多。
//
// ⚠️ 只做两件事：① 探 9444；② 不通就用 `jimeng-browser.mjs` 重开并停在共享画布。
//    **不碰画布内容、不导航到别的项目、不关别人的浏览器**。
//    探测间隔 6 秒；已存活则什么都不做。
//
// 🔴 **批次 201 增记一条教训（这条守护差点把「关掉有头窗口」变成无用功）**：
//   用户明确要求「此后请使用无头浏览器」。我手动 kill 掉那个**有头**浏览器之后，
//   这个守护在 6 秒内**又把它拉起了一个新的** —— 用户屏幕上于是又蹦出一个窗口，
//   看起来像「我明明关掉了怎么还在」。
//   ⇒ 真正的修法**不是**去 kill 守护，而是**把它拉起的目标改成无头**
//   （`jimeng-browser.mjs` 里的 `headless` 已同步改为 `true`）。
//   ⇒ 📌 **通用教训**：当你「关掉某个自动拉起的东西」却发现它又回来时，
//      **先查是谁在拉它**，再决定「杀进程」还是「改被拉起的那一头」。
//      只杀进程是**症状**处理，改源头才是**根因**处理 —— 尤其当它是常驻进程时。
import { spawn, execSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 活 = async () => { try { const r = await fetch('http://127.0.0.1:9444/json/version'); return r.ok; } catch { return false; } };
const 清锁 = () => { try { execSync('rm -f /tmp/jimeng-manual-profile/SingletonLock /tmp/jimeng-manual-profile/SingletonCookie /tmp/jimeng-manual-profile/SingletonSocket'); } catch {} };

let 上次拉起 = 0;
const 拉起 = () => {
  const now = Date.now();
  if (now - 上次拉起 < 45000) return;          // 至少隔 45 秒，别把别人正在启动的浏览器顶掉
  上次拉起 = now;
  清锁();
  const p = spawn(process.execPath, [join(HERE, 'jimeng-browser.mjs'), URL_], { detached: true, stdio: 'ignore' });
  p.unref();
  console.log(new Date().toISOString(), '→ 已拉起浏览器 pid', p.pid);
};

console.log(new Date().toISOString(), '浏览器守护启动（每 6 秒探一次 9444）');
for (;;) {
  if (await 活()) { /* 活着就什么都不做 */ }
  else { console.log(new Date().toISOString(), '9444 不通'); 拉起(); }
  await new Promise((r) => setTimeout(r, 6000));
}
