/**
 * 批次 229：**夹出剩下两个取景带起点** ⇒ 凑齐四个 `w*`。
 *
 * 🔴 先纠正一个**方向性错误**（本脚本的设计依据）：
 *   批次 225/226 扫过的区间里，`文本 3`（`1100`–`1300`）与 `图片 b22-upload`（`1195`–`1215`）
 *   的落点**全都是恰好 `0.5`** ⇒ 按乘法律 `落点 = min(0.5, z0 × N(w − w*))`，
 *   **封顶值意味着那个 w 在带的「上坡侧之外」**，也就是 **`w` 比 `w*` 大**。
 *   ⇒ 所以它们的带子起点在**更窄（更小 w）的一侧**，必须**往下扫**，不是往上扫。
 *   （前几批把它记成「带子在 `>1215` / `≲1081`」是方向写反了，本批一并订正。）
 *
 * 📌 本批两个靶子（都不新建、不上传、不删除任何东西）：
 *   ① `图片 node: b22-upload`（`node_gref4sw056`，`569×320`，`react-flow__node-image`）
 *   ② `文本 node: 文本 3`（`node_5gftn3dnt1`，`320×320`，`react-flow__node-text`）
 *
 * 两阶段（省臂数的关键）：
 *   **粗扫**：从 `1195` 往窄的方向步进 `6`，直到出现**落点 ≠ 0.5** 的臂为止（封顶被打破 ⇒ 已进带子）；
 *   **细扫**：在粗扫找到的位置附近 ±`7` 用步长 `1` 重扫 ⇒ 定出 `w*`（落点**恰好等于 z0** 的那一档）。
 *
 * 每个臂都记：`z0`（开页时的画布缩放，立规 106）、落点 `scale`、屏上尺寸、中心 X/Y、三采一致性。
 * 中心 Y 恰好 `360` ⇒ 「居中 50%」那一支；否则是斜坡分支（立规 104 / 108 的两个正交读量）。
 *
 * ⛔ 只读 + 只点搜索结果行（那是定位该节点的唯一路径）；不触发生成、不进入扣费页、
 *   不点「保存到主体库」、不分享、不下载、不新建、不删除。
 *
 * 用法：node scripts/jimeng-b229.mjs  （原始读数 /tmp/b229.json，日志 /tmp/b229.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b229b.json';
const 粗步 = 8;
const 细半径 = 5;
const 粗扫下限 = 920;
const 粗扫上限臂 = 30;

const 靶子 = [
  // 📌 只做图片节点，且**只扫第一批没覆盖的窄段**：
  //    第一轮（`/tmp/b229.log`）已确认 `1195`–`1111` 共 15 臂**全部封顶** ⇒ w*₍图片₎ < 1111。
  //    重复扫那一段是纯浪费（实测每臂约 2.5 分钟），所以直接从 `1104` 往下走。
  { 名: '图片b22', id: 'node_gref4sw056', 词: ['b22-upload', 'b22'], 起始宽: 1104 },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b229b', 粗步, 细半径, 粗扫下限, 结果: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
const 当前缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
});
const 搜索钮 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button, [role="button"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));

/** 单个臂：新开一页 → 记 z0 → 定位目标 → 记三采。 */
async function 臂(w, 靶) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const z0 = await 当前缩放(p);
    const 在 = (await 清单(p)).includes(靶.id);
    if (!在) return { w, 无效臂: '节点不在' };

    const 钮 = await 搜索钮(p);
    if (!钮) return { w, 无效臂: '找不到搜索钮' };
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!inp) return false;
      inp.focus(); inp.select();
      return true;
    });
    if (!有框) return { w, 无效臂: '找不到搜索输入框' };

    let 用的词 = null;
    for (const 词 of 靶.词) {
      // 📌 每个候选词之前重新全选：Backspace 只删一个字符，上一词更长就会残留 ⇒ 拼出错误的查询词。
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 回读 = await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        return inp ? inp.value : null;
      });
      const 点 = await 结果行点(p, 靶.id);
      if (点 && 回读 === 词) {
        await p.mouse.click(点[0], 点[1]);
        await p.waitForTimeout(4600);
        用的词 = 词;
        break;
      }
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(300);
    }
    if (!用的词) return { w, 无效臂: '候选词都没命中那一行' };

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
    const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
    return {
      w, z0, 用的词,
      scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, off: 末.off, 中心: 末.中心,
      页内一致: ss.length === 1,
      分支: 末.中心 && 末.中心[1] === 360 ? '居中50' : '斜坡',
      封顶: 末.vp ? Math.abs(末.vp[2] - 0.5) < 1e-9 : null,
    };
  } catch (e) {
    return { w, 无效臂: '异常 ' + e.message };
  } finally {
    try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
  }
}

const 打印 = (r) => (r.无效臂
  ? `  w=${r.w} ⛔ ${r.无效臂}`
  : `  w=${r.w} z0=${r.z0} → s=${r.scale} 屏上=${JSON.stringify(r.屏上)} 中心Y=${r.中心 ? r.中心[1] : null} 分支=${r.分支} ${r.封顶 ? '封顶' : '带子内'}`);

for (const 靶 of 靶子) {
  const 记 = { 靶, 粗: [], 细: [] };
  log(`\n════ ${靶.名}（${靶.id}）════`);

  // ---- 阶段一：粗扫（从 1195 往窄走，步长 6，找「落点 ≠ 0.5」的第一臂）----
  let 边界 = null;
  for (let i = 0, w = 靶.起始宽; i < 粗扫上限臂 && w >= 粗扫下限; i++, w -= 粗步) {
    const r = await 臂(w, 靶);
    记.粗.push(r);
    log(打印(r));
    if (!r.无效臂 && r.封顶 === false) { 边界 = w; break; }
  }
  if (边界 === null) {
    log(`  ⛔ 粗扫 ${记.粗.length} 臂都没打破封顶 ⇒ ${靶.名} 的带子不在本范围内`);
    out.结果[靶.名] = { ...记, 结论: '未找到' };
    // 🔴 这一支原来**漏了写文件**（只在找到边界那条路上写）⇒ 「没找到」这种结论会整批丢失。
    //    「没找到」本身就是结论，必须落盘。
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    log(`  ⛔ 已把「未找到」写进 ${OUT}`);
    continue;
  }
  // 🔴 细扫窗口**不能**照着「第一档不封顶」摆 —— 那是 w* + B，不是 w*。
  //   带宽 B = ln(0.5 / z0) / k（批次 222/225 的模型，k = 0.035289）
  //   ⇒ w* ≈ 边界 − B。本批第一版把窗口放在 边界±7，正好整段落在带子里、够不到 w*（设计缺陷，已修）。
  const z边 = (记.粗.find((r) => r.w === 边界) || {}).z0 || 0.260267;
  const B = Math.round(Math.log(0.5 / z边) / 0.035289);
  const 细中心 = 边界 - B;
  log(`  → 粗扫在 w=${边界} 打破封顶；按模型 B=ln(0.5/z0)/k=${B}px ⇒ w*≈${细中心}，细扫 ${细中心 - 细半径}–${细中心 + 细半径}`);

  // ---- 阶段二：细扫（w* 附近 ±细半径，步长 1）----
  for (let w = 细中心 - 细半径; w <= 细中心 + 细半径; w++) {
    const r = await 臂(w, 靶);
    记.细.push(r);
    log(打印(r));
  }

  // ---- 判 w*：细扫里「scale 恰好等于 z0」且「中心 Y 在斜坡分支」的那一档 ----
  const 有效 = 记.细.filter((r) => !r.无效臂);
  const w星 = 有效.find((r) => Math.abs(r.scale - r.z0) < 1e-6);
  const 带内 = 有效.filter((r) => r.scale !== 0.5);
  记.结论 = {
    w星: w星 ? w星.w : null,
    带内档数: 带内.length,
    带内范围: 带内.length ? [Math.min(...带内.map((r) => r.w)), Math.max(...带内.map((r) => r.w))] : null,
    首个未封顶: 带内.length ? Math.min(...带内.map((r) => r.w)) : null,
    有效臂: 有效.length,
    无效臂: 记.细.filter((r) => r.无效臂).length,
    一致性: 有效.every((r) => r.页内一致),
    分支集: [...new Set(有效.map((r) => r.分支))],
  };
  log(`【${靶.名} 结论】` + JSON.stringify(记.结论));
  out.结果[靶.名] = 记;
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('\n写入 ' + OUT);
await b.close();