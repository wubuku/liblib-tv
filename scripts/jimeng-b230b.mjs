/**
 * 批次 230b：把**全画布 `76` 个节点的可读状态**一次性 dump 出来，
 * 拿去和**已知的五个 `w*`** 对照，看「决定带子位置的」是不是某个**能读出来的属性**。
 *
 * 🔴 为什么换这个方向（批次 230 第一版的教训）：
 *   第一版想用二分夹 `文本 1` 的封顶边界，结果区间 `[900, 1092]` 里有 `5` 臂全是封顶
 *   ⇒ **二分的不变式下界 `lo = 900` 从来没被验证过**（它是「假设 900 已经不封顶」），
 *   而收敛出来的「边界 ≈ 903」只是**测过的最小封顶宽度**，不是真边界
 *   ⇒ 打印出来的 `w*₍文本1₎ ≈ 903` 是**假结论**，本脚本只承认
 *   「`文本 1` 在 `903`–`996` 全部封顶 ⇒ 其边界 ≤ 903」。
 *
 * 📌 换方向的理由：批次 230 的 DOM 对照里出现了两个**真正可读**的逐节点差异 ——
 *   `文本 1`：`z-index: 0`、正文逐字是占位「双击编辑文本」（**空节点**）
 *   `文本 3`：`z-index: 3`、正文是「测试文字样例」（**有内容**）
 *   ⇒ 而批次 224/226 已经排除了 CSS 尺寸与 class 的 kind，
 *      **剩下的候选就是这类「类与几何都不是」的逐节点状态**。
 *   已知 `w*`：`音频 68 = 1212`、`视频 1 = 1212`、媒体视频 `≈1202`、
 *              `图片 b22 < 920`、`文本 3 ≲ 1004`、`文本 1 ≤ 903`
 *   ⇒ 只要把 `76` 个节点的 `z-index` / 空非空 / 画布坐标全拉出来，
 *      **一眼就能看出 `w*` 跟哪个属性相关**（或者跟哪个都不相关）。
 *
 * ⛔ 纯只读：不点任何东西，不新建、不上传、不删除。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b230b.json';
const 占位 = '双击编辑文本';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const out = {};

try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(5000);

  out.全部 = await page.evaluate((占位) => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    const z = /z-index:\s*(-?\d+)/.exec(n.style.cssText || '');
    const txt = (n.innerText || '').replace(/\s+/g, ' ').trim();
    const kind = /react-flow__node-(\w+)/.exec(n.className || '');
    return {
      aria: n.getAttribute('aria-label'),
      id: n.getAttribute('data-id'),
      kind: kind ? kind[1] : null,
      z: z ? Number(z[1]) : null,
      空: txt.includes(占位),
      文本长度: txt.length,
      css: [n.offsetWidth, n.offsetHeight],
      画布: m ? [Math.round(Number(m[1]) * 100) / 100, Math.round(Number(m[2]) * 100) / 100] : null,
      标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
    };
  }), 占位);

  const 已知 = {
    '音频 68': { w星: 1212 },
    '视频 1': { w星: 1212 },
    '媒体视频': { w星: '≈1202' },
    '图片 b22-upload': { w星: '<920' },
    '文本 3': { w星: '≲1004' },
    '文本 1': { w星: '≤903' },
  };
  out.已知w星 = 已知;
  out.对照 = [];
  for (const 键 of Object.keys(已知)) {
    const n = out.全部.find((x) => (x.aria || '').includes(键.replace('媒体视频', '媒体视频')) ||
      (键 === '媒体视频' ? /视频 node: 媒体/.test(x.aria || '') : (x.aria || '').includes(键)));
    out.对照.push({ 键, 已知: 已知[键], 实读: n || '没找到' });
  }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

  console.log('=== 已知 w* × 可读属性 ===');
  for (const c of out.对照) {
    if (c.实读 === '没找到') { console.log(`${c.键}：没找到`); continue; }
    const n = c.实读;
    console.log(`${c.键.padEnd(16)} w*=${String(c.已知.w星).padEnd(7)} z=${String(n.z).padEnd(4)} 空=${n.空 ? '是' : '否'} 文本长度=${String(n.文本长度).padEnd(4)} css=${JSON.stringify(n.css)} 画布=${JSON.stringify(n.画布)} kind=${n.kind}`);
  }

  console.log('\n=== 按 z-index 分组（看 w* 是否与 z 相关）===');
  const 按z = {};
  for (const n of out.全部) { (按z[n.z] = 按z[n.z] || []).push(n); }
  for (const z of Object.keys(按z).sort((a, b) => a - b)) {
    const 组 = 按z[z];
    const kinds = [...new Set(组.map((n) => n.kind))];
    const 空数 = 组.filter((n) => n.空).length;
    console.log(`  z=${z.padEnd(4)} 节点数=${String(组.length).padEnd(3)} kind=${JSON.stringify(kinds).padEnd(30)} 空节点=${空数}  样例=${组.slice(0, 2).map((n) => n.aria).join(' | ')}`);
  }

  console.log('\n=== 按「空/非空」分组 ===');
  for (const 空 of [true, false]) {
    const 组 = out.全部.filter((n) => n.空 === 空);
    console.log(`  ${空 ? '空节点' : '有内容'}：${组.length} 个，kind=${JSON.stringify([...new Set(组.map((n) => n.kind))])}`);
    console.log(`    ${组.slice(0, 8).map((n) => `${n.aria}(z=${n.z})`).join('  ')}`);
  }

  console.log('\n=== z-index 的取值分布 ===');
  const 计数 = {};
  for (const n of out.全部) 计数[n.z] = (计数[n.z] || 0) + 1;
  console.log('  ' + Object.entries(计数).sort((a, b) => Number(a[0]) - Number(b[0])).map(([z, c]) => `z=${z}: ${c} 个`).join('  '));
} catch (e) { out.出错 = e.message; console.log('🔴 ' + e.message); fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); }

try { await page.keyboard.press('Escape'); await page.waitForTimeout(400); } catch (e) { /* 忽略 */ }
console.log('写入 ' + OUT);
try { await page.close(); } catch (e) { /* 忽略 */ }
await b.close();
