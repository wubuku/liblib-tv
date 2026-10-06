/**
 * 批次 234：给「**同一个动作、同一个节点，窗口宽度不同 ⇒ 取景缩放不同**」这件事配两张图。
 *
 * 📌 为什么值得配图：这是最近十来个批次里**最反直觉、也最容易被用户当成故障**的一条 ——
 *   用户点搜索定位一个节点，看到画面缩放不是 `50%`，第一反应是「出问题了」。
 *   而实测：把窗口宽度调进 `1212`–`1230` 这个约 `19px` 宽的区间，取景落点就会低于 `50%`。
 *   手册此前只有文字，**没有图**，而这条恰好是「看图才说得清」的。
 *
 * 📌 两张图各自要证明什么（写死，避免拍脑袋）：
 *   ① `1215`：凹口**内** ⇒ 落点 `0.289269`（约 `29%`）—— 注意**不是** `50%`
 *   ② `1235`：凹口**右侧** ⇒ 落点恰好 `0.5`（`50%`）—— 同一个节点、同一个动作
 *   ⇒ 两张并排就是「差别只在窗口宽度」的直接证据。
 *
 * 🔴 纪律：
 *   · **先验 DOM 再画框，最后才截图**（截图放在所有可能抛异常的读数之后）
 *   · 画框是**注入 DOM**（往 `.react-flow__viewport` 里加两个绝对定位的 div），
 *     框的颜色/位置**读回校验**后才 shutter
 *   · `alt` 里不出现 `**`，且与 manifest / 正文引用**逐字一致**
 *
 * ⛔ 只点搜索结果行定位节点；不新建、不上传、不删除、不触发生成。
 *
 * 用法：node scripts/jimeng-b234.mjs  （落盘 screenshots/197-*.png、198-*.png，读数 /tmp/b234.json）
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b234.json';
const 靶 = { id: 'node_tadm1nyykc', 名: '音频 68', 词: ['音频 68', '音频', '68'] };
const 两档 = [
  { w: 1215, 期望: '凹口内', 期望落点: 0.289269 },
  { w: 1235, 期望: '凹口右侧（封顶）', 期望落点: 0.5 },
];
const 框色 = 'rgba(255, 92, 0, 0.95)';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b234', 两档: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 档 of 两档) {
  const p = await ctx.newPage();
  const 记 = { w: 档.w, 期望: 档.期望 };
  try {
    await p.setViewportSize({ width: 档.w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    // ---- ① 打开搜索并点结果行，定位到「音频 68」 ----
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!inp) return false;
      inp.focus(); inp.select();
      return true;
    });
    if (!有框) throw new Error('找不到搜索输入框');
    let 点 = null;
    for (const 词 of 靶.词) {
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 读 = await p.evaluate((nid) => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        return { 回读: inp ? inp.value : null, 有行: !!e };
      }, 靶.id.replace(/^node_/, ''));
      if (读.有行 && 读.回读 === 词) {
        点 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          const r = e.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
        }, 靶.id.replace(/^node_/, ''));
        if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); 记.用的词 = 词; break; }
      }
    }
    if (!点) throw new Error('候选词都没命中那一行');
    await p.keyboard.press('Escape');
    await p.waitForTimeout(600);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(900);

    // ---- ② 全部读数都放在画框/截图之前（截图放最后） ----
    const 读 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const zoomBtn = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const zr = zoomBtn ? zoomBtn.getBoundingClientRect() : null;
      const nr = n ? n.getBoundingClientRect() : null;
      return {
        scale: m ? Number(m[1]) : null,
        缩放按钮aria: zoomBtn ? zoomBtn.getAttribute('aria-label') : null,
        缩放按钮矩形: zr ? [Math.round(zr.x), Math.round(zr.y), Math.round(zr.width), Math.round(zr.height)] : null,
        节点屏上: nr ? [Math.round(nr.width), Math.round(nr.height)] : null,
        节点中心: nr ? [Math.round(nr.x + nr.width / 2), Math.round(nr.y + nr.height / 2)] : null,
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
        innerW: window.innerWidth,
      };
    }, 靶.id);
    Object.assign(记, 读);
    记.期望落点 = 档.期望落点;
    记.落点吻合 = 读.scale !== null && Math.abs(读.scale - 档.期望落点) < 1e-4;
    log(`【w=${档.w}】落点 ${读.scale}（期望 ${档.期望落点}，${记.落点吻合 ? '✅ 吻合' : '🔴 不吻合'}）｜ 缩放按钮 ${读.缩放按钮aria} ｜ 节点屏上 ${JSON.stringify(读.节点屏上)}`);

    if (!记.落点吻合) throw new Error('落点与预期不符，不截图（避免拍到与正文矛盾的图）');

    // ---- ③ 画框：缩放读数 + 被定位的节点；画完读回校验 ----
    const 框校验 = await p.evaluate(([zr, nc, 色]) => {
      const 层 = document.createElement('div');
      层.setAttribute('data-b234', '1');
      层.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
      const 画 = (x, y, w, h, 宽) => {
        const d = document.createElement('div');
        d.style.cssText = `position:absolute;left:${x - 3}px;top:${y - 3}px;width:${w + 6}px;height:${h + 6}px;border:${宽}px solid ${色};border-radius:3px`;
        层.appendChild(d);
        return d;
      };
      const a = 画(zr[0], zr[1], zr[2], zr[3], 3);
      const c = 画(nc[0] - 26, nc[1] - 26, 52, 52, 2);
      document.body.appendChild(层);
      const ra = a.getBoundingClientRect();
      const rc = c.getBoundingClientRect();
      return {
        框1: [Math.round(ra.x), Math.round(ra.y), Math.round(ra.width), Math.round(ra.height)],
        框2: [Math.round(rc.x), Math.round(rc.y), Math.round(rc.width), Math.round(rc.height)],
        层在: document.querySelectorAll('[data-b234="1"]').length === 1,
      };
    }, [读.缩放按钮矩形, 读.节点中心, 框色]);
    记.框校验 = 框校验;
    if (!框校验.层在 || 框校验.框1[2] <= 0 || 框校验.框2[2] <= 0) throw new Error('画框校验没过，不截图');
    log(`【w=${档.w}】画框校验 缩放读数框=${JSON.stringify(框校验.框1)} 节点框=${JSON.stringify(框校验.框2)}`);

    // ---- ④ 最后才截图 ----
    const 文件 = `screenshots/${档.w === 1215 ? '197-framing-zoom-1215-inside-notch.png' : '198-framing-zoom-1235-capped.png'}`;
    const abs = 'docs/user-manual/jimeng-canvas/' + 文件;
    await p.screenshot({ path: abs });
    const buf = fs.readFileSync(abs);
    记.file = 文件;
    记.sha256 = crypto.createHash('sha256').update(buf).digest('hex');
    记.字节 = buf.length;
    log(`【w=${档.w}】已截图 ${文件}（${buf.length} 字节，sha256 ${记.sha256.slice(0, 16)}…）`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 w=${档.w} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.两档.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
await b.close();