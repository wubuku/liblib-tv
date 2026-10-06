/**
 * 批次 233：画布上有**三个**文本节点（`文本 1` z=0 空、`文本 2` z=2 空、`文本 3` z=3 有内容），
 * 而旧记录里「`文本 3` 的凹口起点是 `1202`」与批次 225 实测的
 * 「`文本 3` 在 `1100`–`1300` 共 `51` 臂落点**全部**恰好 `0.5`」**直接矛盾**。
 *
 * 🔴 批次 232 刚刚抓到过同类的错：批次 216/223 记的「媒体视频 `w* ≈ 1202`」
 *   其实很可能是把 **`文本 3` 那一档 `1202: 0.260267`、中心 `Y≈390`** 的读数安到了视频节点头上。
 *   ⇒ 同一个 `1202` 现在被两个节点同时认领，**至少有一处归属是错的**。
 *   ⇒ 本批不再猜「哪个节点该是 `1202`」，而是**三个文本节点各测一遍 `1202`**，
 *      让读数自己指出答案是谁。
 *
 * 📌 判读（写死，避免事后找说法）：
 *   · 某一个文本节点在 `1202` 落点 `< 0.5`（凹口内）⇒ **旧记录的归属搞错了，
 *     那个节点才是 `1202` 的真正主人**；其余两个在 `1202` 封顶
 *   · 三个全在 `1202` 封顶 ⇒ **`1202` 那批读数来自一个已被删除的节点**（本批无法复验）
 *   · 再对「命中的那个」补测 `1215`，确认它沿曲线上升（批次 216/223 记的 `1202→1219` 单调递增）
 *
 * ⛔ 纯只读 + 只点搜索结果行定位；不新建、不上传、不删除任何节点。
 *
 * 用法：node scripts/jimeng-b233.mjs  （原始读数 /tmp/b233.json，日志 /tmp/b233.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b233.json';
const 文本 = [
  { 名: '文本1', id: 'node_3bfb9r79qe', 词: ['文本 1', '文本', '1'] },
  { 名: '文本2', id: 'node_aw29cp094x', 词: ['文本 2', '文本', '2'] },
  { 名: '文本3', id: 'node_5gftn3dnt1', 词: ['文本 3', '文本', '3'] },
];
const 首轮档 = [1202];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b233', 文本, 臂: [], 补测: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));

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
  : `  ${r.靶} w=${r.w} z0=${r.z0} → s=${r.scale} 屏上=${JSON.stringify(r.屏上)} 中心Y=${r.中心 ? r.中心[1] : null} 分支=${r.分支} ${r.封顶 ? '封顶' : '凹口内'}`);

try {
  // ---- 首轮：三个文本节点各测 1202 ----
  for (const w of 首轮档) {
    log(`════ 首轮 w=${w} ════`);
    for (const 靶 of 文本) {
      const r = await 臂(w, 靶);
      out.臂.push(r);
      log(打印(r));
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }

  // ---- 判读 ----
  const 有效 = out.臂.filter((r) => !r.无效臂);
  const 凹口内 = 有效.filter((r) => r.封顶 === false);
  out.结论 = {
    有效臂: 有效.length,
    凹口内的节点: 凹口内.map((r) => ({ 靶: r.靶, w: r.w, scale: r.scale, 中心Y: r.中心 ? r.中心[1] : null })),
    判读: 凹口内.length
      ? `旧记录的归属搞错了 —— ${凹口内.map((r) => r.靶).join('、')} 才是 1202 的真正主人`
      : '三个文本节点在 1202 全部封顶 ⇒ 那批 1202 读数来自一个已被删除的节点，本批无法复验',
  };
  log('【首轮结论】' + JSON.stringify(out.结论));

  // ---- 补测：对命中的节点测 1210 / 1215 / 1219，确认是否沿曲线上升 ----
  for (const 靶 of 凹口内) {
    const 原 = 文本.find((t) => t.名 === 靶.靶);
    log(`════ 补测「${靶.靶}」════`);
    for (const w of [1210, 1215, 1219]) {
      const r = await 臂(w, 原);
      out.补测.push(r);
      log(打印(r));
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }
  const 补有效 = out.补测.filter((r) => !r.无效臂);
  if (补有效.length) {
    const 同一节点 = [...new Set(补有效.map((r) => r.靶))];
    const 单调 = 同一节点.length === 1
      && 补有效.every((r, i, arr) => i === 0 || r.scale > arr[i - 1].scale)
      && 凹口内[0].scale < 补有效[0].scale;
    out.结论.补测 = { 节点: 同一节点, 读数: 补有效.map((r) => ({ w: r.w, s: r.scale })), 沿曲线上升: 单调 };
    log('【补测结论】' + JSON.stringify(out.结论.补测));
  }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
} catch (e) {
  out.出错 = e.message;
  log('🔴 ' + e.message);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
await b.close();