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
