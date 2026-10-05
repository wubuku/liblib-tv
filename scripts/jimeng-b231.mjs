/**
 * 批次 231：建**一个自己的音频节点**，量它的取景带起点 `w*`，和 `音频 68`（`w* = 1212`）比。
 *
 * 🔴 为什么用音频节点、而不是继续量文本/图片：
 *   批次 229/230 已经把 `文本 3`（`≲1004`）、`图片 b22`（`≲920`）、`文本 1`（`≤903`）的带子
 *   全部推到 **`1004` 以下** —— 那些宽度**比任何正常窗口都窄**，而且越窄越难扫。
 *   音频/视频族的带子却落在 **`1202`–`1230`**，是**真实窗口区间** ⇒ 扫描可靠、结论可用。
 *   ⇒ 用同一个 kind（`audio`）、同一个 CSS 尺寸（`320×320`）做对照，
 *      **只差「它是哪个节点」**，这正是判「`w*` 是逐节点状态还是按族规则」最省事的一刀。
 *
 * 📌 判读（提前写死，避免事后找说法）：
 *   · 新节点的 `w*` **等于 `1212`** ⇒ `w*` 对整个 `audio` 族是**一条规则**（按族）
 *   · 新节点的 `w*` **不等于 `1212`** ⇒ `w*` **逐节点不同** ⇒ 结合它与 `音频 68` 的
 *     画布坐标 / `z-index` 差异，才能继续往「坐标」或「创建顺序」上收
 *   · **扫不出来（在 `[1195, 1235]` 内全封顶）** ⇒ 它的带子在这段之外
 *     ⇒ 只能写「≤ 某个已测值」，**不能**写「≈」（立规 112 的教训）
 *
 * 🔴 二分的不变式两端**都必须先各测一臂**（立规 112）：
 *   阶段 0 先测 `1235`（应封顶）与 `1195`（应不封顶，音频族带子是 `1212`–`1230`）；
 *   两端性质不符预期就**如实记录并停止二分**，不硬夹。
 *
 * 收尾：`Backspace` 删除自建节点（批次 228 实测 `Delete` 对已选中节点无效、`Backspace` 有效）。
 *
 * ⛔ 不触发生成、不进入扣费页、不点「保存到主体库」、不分享、不下载；
 *   只新建 / 删除**本会话自己创建**的那一个节点，不碰别人的节点。
 *
 * 用法：node scripts/jimeng-b231.mjs  （原始读数 /tmp/b231.json，日志 /tmp/b231.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b231.json';
const 参照 = { 名: '音频68', id: 'node_tadm1nyykc', 词: ['音频 68', '音频', '68'], 已知w星: 1212 };
const 区间 = { 下: 1195, 上: 1235 };
const 细半径 = 4;

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b231', 区间, 阶段0: [], 二分: [], 细扫: [], 新节点: null };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const z = /z-index:\s*(-?\d+)/.exec(n.style.cssText || '');
  return {
    id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: m ? [Number(m[1]), Number(m[2])] : null,
    z: z ? Number(z[1]) : null,
    css: [n.offsetWidth, n.offsetHeight],
  };
}));

async function 臂(w, 靶) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const z0 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    if (!(await 清单(p)).some((n) => n.id === 靶.id)) return { w, 靶: 靶.名, 无效臂: '节点不在' };

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
        vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
      };
    }, 靶.id);
    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采()); await p.waitForTimeout(450); }
    const 末 = 三采[2];
    return {
      w, 靶: 靶.名, z0, 用的词,
      scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, 中心: 末.中心,
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
  : `  ${r.靶} w=${r.w} z0=${r.z0} → s=${r.scale} 屏上=${JSON.stringify(r.屏上)} 中心Y=${r.中心 ? r.中心[1] : null} ${r.封顶 ? '封顶' : '带子内'}`);

let 自建 = null;
try {
  // ============ 步骤 1：建一个自己的音频节点 ============
  {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 建前 = (await 清单(p)).map((n) => n.id);
    const 入口 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '音频');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!入口) throw new Error('找不到「音频」入口');
    await p.mouse.click(入口[0] + Math.round(入口[2] / 2), 入口[1] + Math.round(入口[3] / 2));
    await p.waitForTimeout(4000);
    const 新增 = (await 清单(p)).filter((n) => !建前.includes(n.id));
    if (新增.length !== 1) throw new Error('新建节点数不是 1：' + 新增.length);
    自建 = { 名: '新音频', id: 新增[0].id, 词: [String(新增[0].aria).replace(/^.*?node:\s*/, ''), '音频', (String(新增[0].aria).match(/\d+/) || [''])[0]].filter(Boolean), 画布: 新增[0].画布, z: 新增[0].z, css: 新增[0].css };
    out.新节点 = 自建;
    log('【新建】' + JSON.stringify(自建));
    log(`【参照】${参照.名} ${参照.画布 || ''} 已知 w*=${参照.已知w星}`);
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }

  // ============ 步骤 2：阶段 0 —— 先各测一臂验证区间两端（立规 112） ============
  const 下臂 = await 臂(区间.下, 自建);
  const 上臂 = await 臂(区间.上, 自建);
  out.阶段0 = [下臂, 上臂];
  log('════ 阶段 0：验证区间两端 ════');
  log(打印(下臂));
  log(打印(上臂));
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

  const 下已验证不封顶 = !下臂.无效臂 && 下臂.封顶 === false;
  const 上已验证封顶 = !上臂.无效臂 && 上臂.封顶 === true;
  log(`  不变式：下界 ${区间.下} ${下已验证不封顶 ? '✅ 已验证不封顶' : '🔴 未验证/不封顶假设不成立'}；上界 ${区间.上} ${上已验证封顶 ? '✅ 已验证封顶' : '🔴 未验证/封顶假设不成立'}`);

  if (!下已验证不封顶 || !上已验证封顶) {
    out.结论 = { 能二分: false, 原因: '不变式两端未同时成立（立规 112），如实停在阶段 0，不硬夹', 下已验证不封顶, 上已验证封顶 };
    log('⛔ ' + JSON.stringify(out.结论));
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  } else {
    // ============ 步骤 3：二分（两端都已验证） ============
    let lo = 区间.下, hi = 区间.上;
    log('════ 阶段 1：二分（两端已验证）════');
    for (let i = 0; i < 6 && hi - lo > 1; i++) {
      const mid = Math.round((lo + hi) / 2);
      const r = await 臂(mid, 自建);
      out.二分.push({ mid, ...r });
      log(打印(r));
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
      if (r.无效臂) break;
      if (r.封顶) hi = mid; else lo = mid;
      log(`  → lo=${lo}（不封顶）hi=${hi}（封顶），宽度 ${hi - lo}`);
    }
    const 边界 = hi;
    log(`【二分收敛】封顶边界落在 (${lo}, ${hi}]`);

    // ============ 步骤 4：细扫（边界 ±细半径，步长 1）============
    log('════ 阶段 2：细扫 ════');
    for (let w = 边界 - 细半径; w <= 边界 + 细半径; w++) {
      const r = await 臂(w, 自建);
      out.细扫.push(r);
      log(打印(r));
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
    const 有效 = [...out.二分, ...out.细扫].filter((r) => !r.无效臂);
    const w星 = 有效.find((r) => Math.abs(r.scale - r.z0) < 1e-6);
    const 带内 = 有效.filter((r) => r.封顶 === false);
    out.结论 = {
      w星: w星 ? w星.w : null,
      带内档数: 带内.length,
      带内范围: 带内.length ? [Math.min(...带内.map((r) => r.w)), Math.max(...带内.map((r) => r.w))] : null,
      有效臂: 有效.length,
      一致性: 有效.every((r) => r.页内一致),
      参照w星: 参照.已知w星,
      与参照相同: w星 ? w星.w === 参照.已知w星 : null,
      判读: w星 ? (w星.w === 参照.已知w星
        ? '同 kind 同尺寸同 w* ⇒ w* 对 audio 族是一条按族规则'
        : '同 kind 同尺寸但 w* 不同 ⇒ w* 是逐节点状态') : '在 [1195, 1235] 内没量到 w*（只能写 ≤ 已测上界）',
    };
    log('【结论】' + JSON.stringify(out.结论));
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
} catch (e) {
  out.出错 = e.message;
  log('🔴 ' + e.message);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

// ============ 收尾：删掉自建节点（Backspace，批次 228 实测有效） ============
if (自建) {
  try {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 点 = await p.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      for (let dy = -r.height / 4; dy <= r.height / 4; dy += 6) {
        for (let dx = -r.width / 4; dx <= r.width / 4; dx += 6) {
          const x = Math.round(r.x + r.width / 2 + dx);
          const y = Math.round(r.y + r.height / 2 + dy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`) && !h.closest('[role="dialog"], button, a, input, textarea')) return [x, y];
        }
      }
      return null;
    }, 自建.id);
    if (点) {
      await p.mouse.click(点[0], 点[1]);
      await p.waitForTimeout(1200);
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(2600);
    }
    out.删除 = { id: 自建.id, 还在: (await 清单(p)).some((n) => n.id === 自建.id) };
    log('【删除】' + JSON.stringify(out.删除));
    out.收尾状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    log('【收尾】' + out.收尾状态行);
    try { await p.close(); } catch (e) { /* 忽略 */ }
  } catch (e) { log('🔴 收尾 ' + e.message); }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
await b.close();