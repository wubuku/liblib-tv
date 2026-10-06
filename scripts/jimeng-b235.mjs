/**
 * 批次 235：量 `导演台`（`external`）的**凹口起点 `w*`** —— 画布上**唯一还没量过 kind** 的族。
 *
 * 📌 为什么这一族最值得测：`w*` 到底是「由 kind 决定」还是「由别的什么决定」，一直悬着。
 *   已有的数据恰好构成一个**天然判别式**：
 *     · `音频 68`（`audio`  / `320×320` / `z=73` / 画布 x=1784.13）⇒ `w* = 1212`
 *     · `视频 1`（`video`  / `320×569` / `z=75` / 画布 x=865   ）⇒ `w* = 1212`
 *     · 新建视频（`video` / `569×320` / `z=153`）              ⇒ `w* = 1212`
 *     · `文本 3`（text / `320×320` / `z=3`）                   ⇒ `w* < 1004`
 *     · `图片 b22`（`image` / `569×320` / `z=10`）             ⇒ `w* < 920`
 *   ⇒ 上面这三个 `1212` 的**坐标、尺寸、长宽比、z-index 彼此全不同**，唯一的共同点是 **kind**；
 *     而 `导演台` 的 **`z=74` 正好夹在 `73` 与 `75` 中间** ⇒ **一次测量同时能分开两个假设**：
 *       · 落 `1212`  ⇒ 既不是 kind 单独决定的，也不是 z-index 单独决定的（得另找判据）
 *       · 不落 `1212` ⇒ `external` 与音视频族不同族（或 z-index 不是判据），需要再分辨
 *
 * 🔴 纪律（沿用立规 112 / 113 / 104）：
 *   · **粗扫只用来找包围区间**，找到第一个「未封顶」就停 —— 凹口下面本來是平的，
 *     往下扫是扫不到东西的（批次 229/230 那 56 臂就是这么白扫的）；
 *   · **二分的两端都必须是「已实测」**（一端读到封顶 `0.5`、一端读到 `<0.5`）才允许夹逼，
 *     否则如实停下，不硬夹；
 *   · **正交读量必带**：只记 `scale` 会把凹口**左右两侧**混成同一件事（两侧都是 `0.5`），
 *     所以每臂都记**节点中心 Y**；
 *   · `w*` 是「窗口宽度」这个**读者手边就有**的量，不是内部编号。
 *
 * ⛔ 只点搜索结果行定位节点；不新建、不上传、不删除、不触发生成。
 *
 * 用法：node scripts/jimeng-b235.mjs [recon|scan|bin]   （读数落盘 /tmp/b235.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b235.json';
const 靶 = { id: 'node_pxvkay973v', 名: '导演台', 词: ['导演台', '导演'] };
/**
 * 粗扫：自宽向窄，找到第一个「未封顶」就停。凹口约 19px 宽 ⇒ 步长先取 20px 量级。
 *
 * 📌 后 5 档（`900`–`740`）是**第二段**：第一段 `920`–`1235` 全部封顶，
 *   于是「凹口在 `920` 以下」与「这个族根本没有凹口」就分不开了 ——
 *   而这两句话对用户的含义完全不同，所以必须再往下压一段把负结论**框出边界**。
 *   ⚠️ 压到 `740` 为止；**不宣称「任何宽度都没有凹口」**，只宣称「`740`–`1235` 实测区间内全封顶」。
 */
const 粗扫档位 = [1235, 1215, 1200, 1180, 1160, 1140, 1120, 1100, 1080, 1060, 1040, 1020, 1000, 960, 920,
  900, 860, 820, 780, 740];
const 封顶 = 0.5;
const 封顶容差 = 1e-4;

const log = (...a) => console.log(a.join(' '));
const 阶段 = process.argv[2] || 'all';
const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : { 轮次: 'b235', 粗扫: [], 二分: [] };
const 存 = () => fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

/** 跑一臂：开页 → 搜索 → 点结果行 → 两次 Escape → 读数。 */
async function 一臂(p, w) {
  await p.setViewportSize({ width: w, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);

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

  const 短名 = 靶.id.replace(/^node_/, '');
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
    }, 短名);
    if (读.有行 && 读.回读 === 词) {
      点 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, 短名);
      if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); break; }
    }
  }
  if (!点) throw new Error('候选词都没命中那一行');
  await p.keyboard.press('Escape');
  await p.waitForTimeout(600);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(900);

  // 全部读数放最后（不截图，但要确认「没有弹层/没跳转」否则读数不可信）
  return await p.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const zbtn = document.querySelector('[data-testid="canvas-zoom-percent"]');
    const nr = n ? n.getBoundingClientRect() : null;
    return {
      scale: m ? Number(m[1]) : null,
      缩放按钮aria: zbtn ? zbtn.getAttribute('aria-label') : null,
      节点屏上: nr ? [Math.round(nr.width), Math.round(nr.height)] : null,
      节点中心: nr ? [Math.round(nr.x + nr.width / 2), Math.round(nr.y + nr.height / 2)] : null,
      状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      innerW: window.innerWidth,
      // 「没弹层、没跳转」的旁证：点完结果行后画布上不该多出 dialog / 抽屉
      有dialog: document.querySelectorAll('[role="dialog"]').length,
      URL没变: location.href.includes('/ai-canvas/'),
    };
  }, 靶.id);
}

function 记一臂(w, 读) {
  const 封顶了 = 读.scale !== null && Math.abs(读.scale - 封顶) < 封顶容差;
  log(`【w=${w}】落点 ${读.scale} ⇒ ${封顶了 ? '封顶 0.5' : '未封顶'}｜ 按钮 ${读.缩放按钮aria} ｜ 中心 ${JSON.stringify(读.节点中心)} ｜ ${读.状态行 || ''}`);
  if (读.有dialog > 0) log(`   ⚠️ 页面上有 ${读.有dialog} 个 dialog，读数可能被遮挡`);
  if (!读.URL没变) log('   ⚠️ URL 已离开画布页');
  return { w, ...读, 封顶了 };
}

// ---------------------------------------------------------------- 阶段 0：侦察（只读）
if (阶段 === 'recon' || 阶段 === 'all') {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    out.侦察 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 有节点: false };
      const cs = getComputedStyle(n);
      const t = n.querySelector('.react-flow__node');
      return {
        有节点: true,
        class名: n.className,
        尺寸: [cs.width, cs.height],
        zIndex: n.style.zIndex,
        画布坐标: [parseFloat(n.style.left), parseFloat(n.style.top)],
        选中数: (document.body.innerText.match(/(\d+) selected/) || [])[1] || null,
      };
    }, 靶.id);
    log('侦察 ' + JSON.stringify(out.侦察));

    // 只读确认它在搜索索引里（**不点结果行**）
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
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
        const 行数 = document.querySelectorAll('[data-testid="canvas-search-result-node_"]').length;
        return { 回读: inp ? inp.value : null, 有行: !!e, 行数, 行文本: e ? e.innerText.replace(/\n/g, ' | ') : null };
      }, 靶.id.replace(/^node_/, ''));
      log(`索引检查 词「${词}」→ ${JSON.stringify(读)}`);
      if (读.有行) { out.侦察.命中词 = 词; break; }
    }
    await p.keyboard.press('Escape');
    await p.waitForTimeout(500);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(800);
  } catch (e) {
    out.侦察 = { 错误: e.message };
    log('🔴 侦察失败：' + e.message);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  存();
}

// ---------------------------------------------------------------- 阶段 1：粗扫（找到第一个未封顶就停）
if (阶段 === 'scan' || 阶段 === 'all') {
  for (const w of 粗扫档位) {
    if (out.粗扫.some((r) => r.w === w)) continue;
    const p = await ctx.newPage();
    try {
      out.粗扫.push(记一臂(w, await 一臂(p, w)));
    } catch (e) {
      out.粗扫.push({ w, 错误: e.message });
      log(`🔴 w=${w} ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
    }
    存();
    if (out.粗扫[out.粗扫.length - 1].封顶了 === false) { log('⇒ 找到第一个未封顶，粗扫到此为止（再往下是平的）'); break; }
  }
  存();
}

// ---------------------------------------------------------------- 阶段 2：二分（两端必须已实测）
if (阶段 === 'bin' || 阶段 === 'all') {
  const 好的 = out.粗扫.filter((r) => r.scale !== null);
  const 封顶档 = 好的.filter((r) => r.封顶了);
  const 未封顶档 = 好的.filter((r) => !r.封顶了);
  if (!封顶档.length || !未封顶档.length) {
    log('🔴 包围区间缺一端（如实停下，不硬夹）：' + JSON.stringify({ 封顶档: 封顶档.map((r) => r.w), 未封顶档: 未封顶档.map((r) => r.w) }));
  } else {
    let lo = Math.max(...未封顶档.map((r) => r.w));   // 已实测未封顶 ⇒ 真在凹口内
    let hi = Math.min(...封顶档.map((r) => r.w));     // 已实测封顶 ⇒ 真在凹口外
    log(`包围区间 [未封顶 ${lo}] .. [封顶 ${hi}]，两端均已实测 ⇒ 开始二分`);
    let 步 = 0;
    while (hi - lo > 1 && 步 < 6) {
      const mid = Math.floor((lo + hi) / 2);
      const p = await ctx.newPage();
      let r;
      try {
        r = 记一臂(mid, await 一臂(p, mid));
      } catch (e) {
        r = { w: mid, 错误: e.message };
        log(`🔴 w=${mid} ${e.message}`);
      } finally {
        try { await p.close(); } catch (e) { /* 忽略 */ }
      }
      out.二分.push(r);
      存();
      步 += 1;
      if (r.封顶了 === true) hi = mid; else if (r.封顶了 === false) lo = mid; else { log('该臂没读到落点，停下不夹逼'); break; }
    }
    out.结论 = { 凹口起点w星: lo, 下一档封顶于: hi, 步数: 步 };
    log('⇒ 结论 ' + JSON.stringify(out.结论));
  }
  存();
}

log('写入 ' + OUT);
await b.close();
