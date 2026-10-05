/**
 * 批次 219 的即时验证：🔴 **完全不点搜索**，只等页面加载后 `scale` 落定，读它是什么。
 *
 * 批次 219 的逐帧记录显示：
 *   · `scale` 的动画在 `t ≈ 8900ms` 就结束；
 *   · 而「搜索面板点结果行」发生在 `t ≈ 10300ms`（音频 68 约 `t≈9150`）；
 *   · **点完之后 `scale` 一字未变。**
 * ⇒ 那段动画**不是取景动画**，「终态 scale」可能是**页面加载时应用恢复上一次视口**的落点，
 *   而**不是**「点搜索结果行」这个动作的结果。
 *
 * 本脚本只做一件事：开页 → 等 `12s` → 读 `scale`。**中间不点任何东西。**
 * 若读到的值与批次 219 的「落点」一致 ⇒ 「点搜索」这一步是空操作。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b219b.json';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b219b-不点搜索' };

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return { vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
    缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    状态行: (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null,
    节点数: document.querySelectorAll('.react-flow__node').length };
});

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
out.读数 = [];
for (const w of [1212, 1216, 1232]) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    const 早 = await 读(p);
    await p.waitForTimeout(12000);
    const 晚 = await 读(p);
    out.读数.push({ w, 开页后即读: 早, 等12秒后: 晚 });
    log(`w=${w} 开页即读 s=${早.vp ? 早.vp[2] : null} ｜ 等 12s 后 s=${晚.vp ? 晚.vp[2] : null} ｜ ${晚.缩放aria} ｜ ${晚.状态行}`);
  } catch (e) { log(`w=${w} 🔴 ${e.message}`); out.读数.push({ w, 出错: e.message }); }
  finally { try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
}
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
