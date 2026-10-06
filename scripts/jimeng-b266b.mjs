/**
 * 批次 266b：把 266 那两个**没法解释**的读数钉死。
 *
 * 📌 266 的原始结果（4 个成功臂）：
 *   `H=720 → 0.5`（屏上 `160`）｜`H=400 → 0.5`（`160`）｜`H=300 → 0.4375`（`140`）｜
 *   `H=240 → 0.0872847`（`27.93`，**中心 Y = 61 而不是 120**）。
 *   ⇒ 前三条已经**推翻了「`0.5` 是字面常数」**，但第四条**自相矛盾**
 *   （批次 253 定的是中心 `Y = H/2`，`240/2 = 120`，实测 `61`）。
 *
 * 🔴 **266 自己的两个方法漏洞，本批先补上**：
 *   ① **没做多帧去重**，只读了一个值 ⇒ 撞上立规 76 逐字警告过的那件事
 *      （「判动画收敛没：看多帧去重后剩几个值，别只看最后一帧」）。
 *      `0.0872847` 这种**不整齐**的值极可能是**没收敛的中间帧**，
 *      而 `0.5` / `0.4375` 这类整齐值才像定值。
 *      ⇒ 本批每臂**连采 `6` 帧**、**逐字去重后逐帧落盘**，并标出「是否只剩一个值」。
 *   ② **没量「窗口高」和「画布窗格高」是不是同一个数** ⇒ 补读 `innerHeight`
 *      与 `.react-flow` 的实际盒子。
 *
 * 📌 **本批要判的三条律**（`H ≥ 400` 时三者都给出封顶 `0.5`，**分不开**）：
 *   `W = 320` 时 `H = 300` 三者**都**给 `140` ⇒ **必须换 `W` 才能分辨**。
 *   🔴 所以本批加测 **`时间线 2`（`W = 1200`）**：
 *     L1 `屏上 = min(0.5W, H − 160)`  ⇒ `H=300` 给 **`140`**
 *     L2 `屏上 = min(0.5W, H − 0.5W)`  ⇒ `H=300` 给 `−300` ⇒ 落到**应用下限 `0.08×1200 = 96`**
 *     L3 `屏上 = min(0.5W, H/2 − 10)`  ⇒ `H=300` 给 **`140`**
 *   ⇒ **`时间线 2` 在 `H=300` 读 `140` 就证 L1/L3、证伪 L2**（`W` 越大分得越开）。
 *
 * 📌 **只读**：不新建、不删除、不上传、不分享、不进扣费页、**绝不点生成**。
 *   两个节点都已存在（本会话只读它们）。每臂**开新页**（批次 260：resize 不重算）。
 *
 * 用法：node scripts/jimeng-b266b.mjs [节点键]      （落盘 /tmp/b266b-<键>.json）
 *       节点键：音频 | 时间线 | 两族
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 宽 = 1000;
const 高表 = [720, 500, 400, 360, 340, 320, 300, 280, 260, 240];
const 帧数 = 6, 帧间隔 = 400;

const 节点表 = {
  音频: { id: 'node_tadm1nyykc', 名: '音频 68', W: 320 },
  时间线: { id: 'node_d4tjtpnatq', 名: '时间线 2', W: 1200 },
};
const 键 = process.argv[2] || '两族';
const 要跑 = 键 === '两族' ? Object.keys(节点表) : [键];
if (!要跑.every((k) => 节点表[k])) { console.error(`未知节点键：${键}`); process.exit(2); }

const log = (...a) => console.log(a.join(' '));

/** 三条候选律（预测先算好并落盘，不允许看到实测再改） */
const 预测 = (h, W) => {
  const 封顶 = 0.5 * W, 应用地板 = 0.08 * W;
  const 夹 = (x) => Math.max(应用地板, Math.min(封顶, x));
  return {
    L1_屏上减160: +夹(h - 160).toFixed(4),
    L2_屏上减0_5W: +夹(h - 0.5 * W).toFixed(4),
    L3_半高减10: +夹(h / 2 - 10).toFixed(4),
    封顶屏上: +封顶.toFixed(4),
  };
};

const out = { 轮次: 'b266b', 宽, 高表, 帧数, 帧间隔, 族: {}, 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const k of 要跑) {
  const 节点 = 节点表[k];
  const 族 = { 节点, 臂: [] };
  out.族[k] = 族;
  for (const 高 of 高表) {
    const p = await ctx.newPage();
    const 记 = { 高, 宽, W: 节点.W, ...预测(高, 节点.W) };
    try {
      await p.setViewportSize({ width: 宽, height: 高 });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(5000);

      const 钮 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]'))
          .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!钮) throw new Error('找不到搜索钮');
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1500);

      const 短名 = 节点.id.replace(/^node_/, '');
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(节点.名, { delay: 85 });
      await p.waitForTimeout(2200);

      const 行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return { 有行: false };
        const r = e.getBoundingClientRect();
        return { 有行: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 可见: r.width > 0 && r.height > 0, 在视口内: r.y >= 0 && r.bottom <= innerHeight };
      }, 短名);
      if (!行.有行 || !行.可见 || !行.在视口内) {
        记.不可达 = !行.有行 ? '搜不到那一行' : (!行.可见 ? '结果行零尺寸' : `结果行在视口外（y=${行.中心 && 行.中心[1]} > H=${高}）`);
        族.臂.push(记); log(`${k} H=${String(高).padStart(3)} ⚠️ ${记.不可达}`);
        await p.close(); continue;
      }
      await p.mouse.click(行.中心[0], 行.中心[1]);
      await p.waitForTimeout(5000);
      await p.keyboard.press('Escape'); await p.waitForTimeout(600);
      await p.keyboard.press('Escape'); await p.waitForTimeout(900);

      // 🔴 连采 6 帧（立规 76），逐字去重
      const 帧 = [];
      for (let i = 0; i < 帧数; i++) {
        帧.push(await p.evaluate((nid) => {
          const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
          const vp = document.querySelector('.react-flow__viewport');
          const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
          const nr = n ? n.getBoundingClientRect() : null;
          return {
            落点: m ? Number(m[1]) : null,
            中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
            屏上宽: nr ? +nr.width.toFixed(4) : null,
            innerH: window.innerHeight,
          };
        }, 节点.id));
        await p.waitForTimeout(帧间隔);
      }
      记.六帧 = 帧;
      const 去重 = [...new Set(帧.map((f) => f.落点))];
      记.去重后落点 = 去重;
      记.是否收敛 = 去重.length === 1;
      记.落点 = 去重.length === 1 ? 去重[0] : null;
      记.内高一致 = 帧.every((f) => f.innerH === 高);
      记.中心Y去重 = [...new Set(帧.map((f) => f.中心Y))];
      记.屏上宽去重 = [...new Set(帧.map((f) => f.屏上宽))];
      记.命中 = [];
      if (记.落点 !== null) {
        for (const [名, v] of [['L1', 记.L1_屏上减160], ['L2', 记.L2_屏上减0_5W], ['L3', 记.L3_半高减10]]) {
          const 预测落点 = +(v / 节点.W).toFixed(9);
          if (Math.abs(记.落点 - 预测落点) <= 1e-6) 记.命中.push(名);
        }
        if (Math.abs(记.落点 - 0.5) <= 1e-9) 记.命中.push('封顶0.5');
      }
      族.臂.push(记);
      log(`${k} H=${String(高).padStart(3)} 落点=${记.落点}（去重 ${去重.length} 个：${JSON.stringify(去重.slice(0, 4))}）中心Y=${JSON.stringify(记.中心Y去重)}（H/2=${高 / 2}）内高一致=${记.内高一致} ⇒ ${记.命中.join('/') || '无命中'}`);
    } catch (e) {
      记.错误 = e.message; 族.臂.push(记); log(`${k} H=${高} 🔴 ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
      fs.writeFileSync(`/tmp/b266b-${k}.json`, JSON.stringify(out, null, 1));
    }
  }
}

// 末态独立复查（立规 140）
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

out.汇总 = {};
for (const [k, 族] of Object.entries(out.族)) {
  const 成功 = 族.臂.filter((a) => a.落点 !== null && a.落点 !== undefined);
  out.汇总[k] = {
    臂: 族.臂.length, 成功: 成功.length,
    收敛臂: 成功.filter((a) => a.是否收敛).length,
    未收敛臂: 成功.filter((a) => !a.是否收敛).length,
    中心Y等于H除2: 成功.filter((a) => a.中心Y去重.length === 1 && a.中心Y去重[0] === a.高 / 2).length,
    内高与设定一致: 成功.filter((a) => a.内高一致).length,
    命中L1: 成功.filter((a) => a.命中.includes('L1')).length,
    命中L2: 成功.filter((a) => a.命中.includes('L2')).length,
    命中L3: 成功.filter((a) => a.命中.includes('L3')).length,
    命中封顶0_5: 成功.filter((a) => a.命中.includes('封顶0.5')).length,
  };
}
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync('/tmp/b266b-全部.json', JSON.stringify(out, null, 1));
log('写入 /tmp/b266b-全部.json');
process.exit(0);
