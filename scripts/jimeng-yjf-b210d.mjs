// 会话 mvs_fb62b78 · 批次 210 d 轮：把 1215~1230 那段「梯度」**钉死还是否掉**。
//
// c 轮（每档新开页，9 臂 0 无效）读到：
//   1200 → −44.5555 ｜ 1210 → −44.5555 ｜ 1215 → **+25.5079** ｜ 1220 → −20.2609
//   1225 → −73.808 ｜ 1230 → −137.045 ｜ 1240 → −144.659 ｜ 1260 → −145.309 ｜ 1280 → −144.836
//
// 🔴 这有两种完全相反的解释，**必须分开**，否则会把「还没收敛」写成「机制」：
//   (A) 真的存在一段**渐变带**（1210~1240 之间 ty 连续地走过去）；
//   (B) 这几档的**取景动画还没结束**，我读到的是中间态 ——
//       而 6 帧/3.6 秒里每档只出现「初始值 + 某一个值」两个，
//       看起来「稳定」，其实可能只是**停在动画的某个平台上**。
//
// 本轮怎么分：
//   ① 每档连采 **20 帧 / 16 秒**（c 轮只有 6 帧 / 3.6 秒）——
//      若动画还没完，后面几帧会**继续走**（取值变多）；若真稳定，20 帧只剩 1 个值。
//   ② **1220 跑两遍**（`1220#1` / `1220#2`）—— 若同一宽度两次读数不同，
//      那就不是「这条宽度就是这个值」，而是**未收敛/有随机性**，结论要相应收窄。
//   ③ 1200 与 1280 当**对照臂**（已知稳定的两个分支）——
//      用来证明「20 帧能看出未收敛」这件事本身是有效的：两个对照臂都该 20 帧只出 1 个值。
import fs from 'node:fs';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 帧数 = 20;
const 间隔 = 800;
// 对照臂 1200 / 1280；带 #2 的是重复臂
const 臂集 = [1200, 1220, '1220#2', 1225, 1230, 1280];
const log = (...a) => console.log(a.join(' '));
const OUT = '/tmp/b210d.json';
const out = { 轮次: 'b210d', 帧数, 间隔ms: 间隔, 间隔总计ms: 帧数 * 间隔,
  要分的两种解释: { A: '真的存在渐变带', B: '取景动画未结束，读到中间态' },
  对照臂: ['1200', '1280'], 重复臂: ['1220#2'], 无效臂: 0, 结果: {} };

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

const 读vp = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
};

for (const 臂 of 臂集) {
  const w = typeof 臂 === 'number' ? 臂 : 1220;
  const 键 = String(臂);
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    await p.keyboard.press('Escape');        // 🔴 清场必须在开面板之前（立规 87）
    await p.waitForTimeout(400);
    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.结果[键] = { 无效: '找不到搜索钮' }; out.无效臂++; continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1200);
    await p.evaluate(() => {
      const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
      if (e) {
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
        e.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2000);

    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      const id = tid.replace('canvas-search-result-node_', 'node_');
      if (!e) return { 存在: false };
      const r = e.getBoundingClientRect();
      return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        节点在: !!document.querySelector(`.react-flow__node[data-id="${id}"]`) };
    }, 目标);
    if (!前置.存在 || !前置.节点在) {
      out.结果[键] = { 无效: !前置.存在 ? '目标行不在' : '画布上找不到目标节点' };
      out.无效臂++; log(键, '⛔ 无效臂'); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);
    const 序列 = [];
    for (let k = 0; k < 帧数; k++) {                      // 🔴 20 帧 / 16 秒，不是 6 帧 / 3.6 秒
      序列.push(await p.evaluate(读vp));
      await p.waitForTimeout(间隔);
    }
    const ty序列 = 序列.map((f) => f && f[1]);
    const 有效ty = ty序列.filter((t) => Number.isFinite(t));
    if (有效ty.length === 0) { out.结果[键] = { 无效: '20 帧全空', 序列 }; out.无效臂++; continue; }

    const 去重 = [...new Set(有效ty)];
    const 判定 = 去重.length === 1 ? '20 帧只出 1 个 ty 值 = 真稳定'
      : (去重.length <= 3 ? `出现 ${去重.length} 个值：${JSON.stringify(去重)} = 还在走/多相`
        : `出现 ${去重.length} 个值 = 明显未收敛`);
    out.结果[键] = {
      宽: w, ty序列, 去重, 去重个数: 去重.length,
      首值: 有效ty[0], 末值: 有效ty[有效ty.length - 1],
      总位移: Math.round((有效ty[有效ty.length - 1] - 有效ty[0]) * 10000) / 10000,
      判定, 断言: { 读到数了: 有效ty.length > 0, 真稳定: 去重.length === 1 },
    };
    log(键, '| 宽', w, '| 去重', JSON.stringify(去重), '| 首', 有效ty[0], '→ 末', 有效ty[有效ty.length - 1],
      '| 位移', out.结果[键].总位移, '|', 判定);
  } catch (e) { out.结果[键] = { 出错: e.message }; out.无效臂++; log(键, '🔴', e.message); }
  finally { try { await p.close(); } catch {} fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); }
}

out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
log('无效臂：', out.无效臂, '/', 臂集.length);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
await b.close();
