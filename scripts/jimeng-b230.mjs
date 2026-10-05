/**
 * 批次 230：**`文本 1` 与 `文本 3` 的带子起点一样吗？** —— 判「`w*` 是逐节点状态还是按族规则」的一刀。
 *
 * 🔴 为什么这是「最便宜的一刀」：
 *   批次 221–229 一路排除下来，`w*` **不是** CSS 宽度（批次 226：两个 `569×320` 不同）、
 *   **不是** CSS 高度（批次 223）、**不是** `class` 的 kind（批次 224）⇒ 剩下唯一没排除的
 *   解释就是「**`w*` 是每个节点各自的状态**」。
 *   要证成它，只需要一组**同族同尺寸**的对照：
 *     `文本 1`（`node_3bfb9r79qe`，`320×320`，`react-flow__node-text`）
 *     `文本 3`（`node_5gftn3dnt1`，`320×320`，`react-flow__node-text`）  ← 批次 229 已测：`1004`–`1300` 全封顶
 *   **若两者的封顶边界不同 ⇒ `w*` 是逐节点状态**（因为 kind 与尺寸都被控住了，别的都没变）。
 *
 * 📌 **为什么用二分而不是线性扫**（批次 229 的教训）：
 *   线性扫 `1092 → 1004` 用了 `12` 臂、约 `30` 分钟（浏览器里有十几个画布页签在抢资源，
 *   实测每臂约 `2.5` 分钟）。封顶边界是个**单调**的分界（上封顶 / 下不封顶）⇒ 可以二分。
 *   区间 `[900, 1092]` 二分 `6` 步就把边界夹到 `±3px`，只要 `6` 臂 ≈ `15` 分钟。
 *
 * 🔴 **二分的不变量**（写错就会二分到错误的一半）：
 *   记 `lo` = 已知**不封顶**（或区间下界）、`hi` = 已知**封顶**。
 *   测 `mid`：封顶 ⇒ `hi = mid`；不封顶 ⇒ `lo = mid`。
 *   收敛后边界在 `(lo, hi]`。
 *
 * 收尾：对照臂会在边界附近各测 `文本 1` 与 `文本 3` 各一次，
 *   **同一个 `w`、同一个节点、只换目标** ⇒ 若两者读数不同，就是直接的反例。
 *
 * ⛔ 只读 + 只点搜索结果行定位；不新建、不上传、不删除任何节点。
 *
 * 用法：node scripts/jimeng-b230.mjs  （原始读数 /tmp/b230.json，日志 /tmp/b230.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b230.json';
const 二分下界 = 900;   // 批次 229 实测 920 仍封顶，所以下界只能再往下取；这里只当作「待夹的区间下沿」
const 二分上界 = 1092;   // 已知封顶（批次 229：`文本 3` 在 `1092` 封顶）
const 步数 = 6;

const 文本1 = { 名: '文本1', id: 'node_3bfb9r79qe', 词: ['文本 1', '文本', '1'] };
const 文本3 = { 名: '文本3', id: 'node_5gftn3dnt1', 词: ['文本 3', '文本', '3'] };

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b230', 步数, 二分下界, 二分上界, 二分: [], 对照: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
const 当前缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
});

/** 一个臂：新开一页 → 记 z₀ → 搜索定位目标 → 等取景 → 记三采。 */
async function 臂(w, 靶) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const z0 = await 当前缩放(p);
    if (!(await 清单(p)).includes(靶.id)) return { w, 靶: 靶.名, 无效臂: '节点不在' };

    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) return { w, 靶: 靶.名, 无效臂: '找不到搜索钮' };
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!inp) return false;
      inp.focus(); inp.select();
      return true;
    });
    if (!有框) return { w, 靶: 靶.名, 无效臂: '找不到搜索输入框' };

    let 用的词 = null;
    for (const 词 of 靶.词) {
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 读 = await p.evaluate((nid) => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        const 行 = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        return { 回读: inp ? inp.value : null, 有行: !!行 };
      }, 靶.id.replace(/^node_/, ''));
      if (读.有行 && 读.回读 === 词) {
        const 点 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return null;
          const r = e.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
        }, 靶.id.replace(/^node_/, ''));
        if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(4600); 用的词 = 词; break; }
      }
    }
    if (!用的词) return { w, 靶: 靶.名, 无效臂: '候选词都没命中那一行' };

    const 采 = async () => p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const r = n ? n.getBoundingClientRect() : null;
      return {
        中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
        屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
        off: n ? [n.offsetWidth, n.offsetHeight] : null,
        vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
      };
    }, 靶.id);

    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采()); await p.waitForTimeout(450); }
    const 末 = 三采[2];
    return {
      w, 靶: 靶.名, z0, 用的词,
      scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, off: 末.off, 中心: 末.中心,
      页内一致: [...new Set(三采.map((x) => x.vp && x.vp[2]))].length === 1,
      分支: 末.中心 && 末.中心[1] === 360 ? '居中50' : '斜坡',
      封顶: 末.vp ? Math.abs(末.vp[2] - 0.5) < 1e-9 : null,
    };
  } catch (e) {
    return { w, 靶: 靶.名, 无效臂: '异常 ' + e.message };
  } finally {
    try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
  }
}

const 打印 = (r) => (r.无效臂
  ? `  ${r.靶} w=${r.w} ⛔ ${r.无效臂}`
  : `  ${r.靶} w=${r.w} z0=${r.z0} → s=${r.scale} 屏上=${JSON.stringify(r.屏上)} 中心Y=${r.中心 ? r.中心[1] : null} 分支=${r.分支} ${r.封顶 ? '封顶' : '带子内'}`);

try {
  // ---- 阶段一：二分 `文本 1` 的封顶边界 ----
  let lo = 二分下界, hi = 二分上界;
  log(`════ 二分「${文本1.名}」的封顶边界，区间 [${lo}, ${hi}]，共 ${步数} 步 ════`);
  for (let i = 1; i <= 步数; i++) {
    const mid = Math.round((lo + hi) / 2);
    const r = await 臂(mid, 文本1);
    out.二分.push({ 步: i, mid, ...r });
    log(打印(r));
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));   // 🔴 每步都落盘（批次 229 缺陷②的教训）
    if (r.无效臂) { hi = mid - 1; log(`  ⚠️ 无效臂，把上界压到 ${hi - 1}（当作已封顶会污染二分）`); continue; }
    if (r.封顶) hi = mid; else lo = mid;
    log(`  → 不变式更新：lo=${lo}（不封顶侧）hi=${hi}（封顶侧），区间宽度 ${hi - lo}`);
    if (hi - lo <= 1) break;
  }
  const 边界 = hi;
  // 🔴 批次 230 第一版的教训：二分的不变式要求**两端都已验证**。
  //    `lo` 从头到尾是「假设 900 就不封顶」，而实测 903 仍然封顶 ⇒ 这个假设**没成立**。
  //    所以这里只能说「测过的最小封顶宽度是 边界」，**不能**说「w* ≈ 边界」。
  const lo已验证 = out.二分.some((r) => !r.无效臂 && r.封顶 === false);
  // 📌 判据来自立规 112：二分的不变式两端都必须是**已验证**的事实。
  log(`【${文本1.名}】测过的最小封顶宽度 = ${边界}；下界 ${lo} ${lo已验证 ? '已验证（不封顶）' : '🔴 未验证（只是假设）'}`);
  log(`  ⇒ 只能写「${文本1.名} 在 [${边界}, ${二分上界}] 全部封顶 ⇒ 其边界 ≤ ${边界}」，**不能**写「w* ≈ ${边界}」`);

  // ---- 阶段二：对照臂 —— 在边界附近，对两个同族节点各测一次 ----
  for (const w of [边界 + 2, 边界 - 2, 1004]) {
    for (const 靶 of [文本1, 文本3]) {
      const r = await 臂(w, 靶);
      out.对照.push({ w, ...r });
      log(打印(r));
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }

  // ---- 判读：同族同尺寸、只差一个「是谁」，读数是否不同 ----
  const 按w = {};
  for (const r of out.对照) {
    if (r.无效臂) continue;
    (按W[r.w] = 按W[r.w] || {})[r.靶] = r;
  }
  const 差异 = Object.keys(按W).filter((w) => 按W[w]['文本1'] && 按W[w]['文本3']
    && (按W[w]['文本1'].封顶 !== 按W[w]['文本3'].封顶
        || Math.abs((按W[w]['文本1'].scale || 0) - (按W[w]['文本3'].scale || 0)) > 1e-9));
  out.结论 = {
    文本1最小封顶宽度: 边界,
    文本1下界已验证: lo已验证,
    文本3上界: 1004,
    对照点: Object.keys(按W).map(Number).sort((a, b) => a - b),
    出现差异的宽度: 差异.map(Number),
    同族同尺寸却不同: 差异.length > 0,
  };
  log('【结论】' + JSON.stringify(out.结论));
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
} catch (e) {
  out.出错 = e.message;
  log('🔴 ' + e.message);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
await b.close();