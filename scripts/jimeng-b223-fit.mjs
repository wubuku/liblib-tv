/**
 * 批次 223 的**离线**分析（不碰浏览器）：判 `w*₍族₎` 是不是节点 CSS 宽度的函数。
 *
 * 📌 三个候选模型（批次 223 开工前用两个已知点闭式解出常数）：
 *   M-线性  ：`w* = 1212 − 10.21 × (CSS宽 − 320) / 249`  ⇒ 宽 1200 预测 `1175.9`
 *   M-倒数  ：`w* = a + b / CSS宽`，由 `320→1212`、`569→1201.79` 解出 `a=1188.66 b=7467.5`
 *             ⇒ 宽 1200 预测 `1194.9`
 *   M-无关  ：`w* = 1212`
 * 📌 三者对宽 `1200` 的预测相差最多 `36px`，远超带宽 `≈18.6px` ⇒ 可判。
 *
 * 📌 另判「高度参不参与」：`视频 1`（`320×569`）与 `音频 68`（`320×320`）**同宽不同高**
 *   ⇒ 若 `w*` 只看宽度，两者带子必须逐字同形（参考：音频在 `1212`–`1230` 的 19 个读数）。
 */
import fs from 'node:fs';

const IN = process.argv[2] || '/tmp/b223.json';
const d = JSON.parse(fs.readFileSync(IN, 'utf8'));
const log = (...a) => console.log(a.join(' '));
const r4 = (x) => Math.round(x * 1e4) / 1e4;

// 参考曲线（批次 221/222，z0 = 0.260267，CSS 320×320）
const 参考 = {};
{
  const A = JSON.parse(fs.readFileSync('/tmp/b222.json', 'utf8')).扫描;
  for (const r of A) 参考[r.w] = r.scale;
}
const 音频带 = Object.entries(参考).filter(([, s]) => s < 0.5).map(([w, s]) => [Number(w), s]);
log('=== 前置 ===');
log(`CSS 尺寸 ${JSON.stringify(d.步骤0_前置.CSS尺寸)}`);
log(`新页缩放 ${d.步骤0_前置.缩放标签}（实际 ${d.步骤0_前置.当前缩放}）｜ 基准节点 ${d.步骤0_前置.基线数}`);
log(`参考（音频 320×320，z0=0.260267）未封顶带 [${音频带[0][0]}, ${音频带[音频带.length - 1][0]}]，${音频带.length} 档`);
log('');

// 本批 z0 = 0.26，理论带宽比参考窄一点
const k = 0.035052;                       // 每像素对数率（批次 222 标定）
const 带宽 = (z0) => Math.log(0.5 / z0) / k;
const 本批带宽 = 带宽(0.26);
log(`📌 本批 z0 = 0.26（手输 26 的精确值）⇒ 理论带宽 ${本批带宽.toFixed(2)} px；参考 z0=0.260267 ⇒ ${带宽(0.260267).toFixed(2)} px（差 ${(带宽(0.260267) - 本批带宽).toFixed(3)} px，对「w* 在哪」无影响）`);
log('');

const 扫描 = d.扫描 || {};
for (const [标签, 集] of Object.entries(扫描)) {
  const 有效 = (集 || []).filter((r) => r && r.scale != null);
  const 无效 = (集 || []).filter((r) => r && r.scale == null);
  log(`=== ${标签} ===`);
  log(`有效臂 ${有效.length}／页内一致 ${有效.filter((r) => r.页内一致).length}／无效臂 ${无效.length}`);
  if (无效.length) log('  无效原因：' + JSON.stringify([...new Set(无效.map((r) => r.无效臂))]));
  const 档 = [...new Set(有效.map((r) => r.w))].sort((x, y) => x - y);
  const 露 = 有效.filter((r) => r.scale < 0.5);
  log(`  扫描范围 ${档[0]}–${档[档.length - 1]}｜ 非 0.5 档：${[...new Set(露.map((r) => r.w))].join(',') || '（一个都没有）'}`);
  if (露.length) {
    露.sort((x, y) => x.w - y.w);
    log(`  ⇒ 未封顶带 **[${露[0].w}, ${露[露.length - 1].w}]**，${露.length} 档（跨 ${露[露.length - 1].w - 露[0].w} px）｜ 理论带宽 ${本批带宽.toFixed(2)} px`);
    log(`  落点：${露.map((r) => `${r.w}:${r.scale}`).join(' ')}`);
    log(`  中心 Y：${[...new Set(露.map((r) => r.中心[1]))].sort((a, b) => a - b).join(', ')}`);
    // N = 落点 / z0 是否等于参考曲线的 N（对 w* 平移后）
    const z0 = 0.26;
    log('  平移量 Δw（相对音频族，同宽度对齐 N）：');
    const 平移 = [];
    for (const r of 露) {
      const lnN = Math.log(r.scale / z0);
      let 配 = null;
      for (let i = 1; i < 音频带.length; i++) {
        const l1 = Math.log(音频带[i - 1][1] / 0.260267), l2 = Math.log(音频带[i][1] / 0.260267);
        if ((lnN >= l1 && lnN <= l2) || (lnN <= l1 && lnN >= l2)) {
          配 = 音频带[i - 1][0] + (lnN - l1) / (l2 - l1) * (音频带[i][0] - 音频带[i - 1][0]);
          break;
        }
      }
      if (配 != null) 平移.push(r.w - 配);
    }
    if (平移.length) {
      const 均 = 平移.reduce((x, y) => x + y, 0) / 平移.length;
      log(`    ${平移.length} 对：${平移.map((x) => x.toFixed(2)).join(', ')} ⇒ 均值 Δw = ${均.toFixed(2)}、铺展 ${(Math.max(...平移) - Math.min(...平移)).toFixed(2)} px`);
      log(`    ⇒ 换算成参考 z0 下：w*₍本族₎ ≈ ${r4(1212 + 均)}`);
    } else log('    与音频带无交叠，配不出平移量');
  }
  log('');
}

// ---------- 三个模型对预测 ----------
const 预测 = { 'M-线性': 1175.9, 'M-倒数': 1194.9, 'M-无关': 1212 };
log('=== 候选模型对 CSS 宽 1200 的 w* 预测 ===');
for (const [k2, v] of Object.entries(预测)) log(`  ${k2}：${v}`);
const 结论 = Object.entries(扫描).map(([标签, 集]) => {
  const 露 = (集 || []).filter((r) => r && r.scale != null && r.scale < 0.5).sort((x, y) => x.w - y.w);
  return [标签, 露.length ? 露[0].w : null];
});
log('');
log('=== 判定表 ===');
log(`  实测带子起点：${结论.map(([a, b]) => `${a}=${b === null ? '扫描范围内全 0.5' : b}`).join('；')}`);
const 命中 = Object.entries(预测).filter(([, v]) => 结论.some(([, b]) => b != null && Math.abs(b - v) <= 本批带宽));
log(`  与实测相容的模型：${命中.length ? 命中.map(([a, v]) => `${a}(预测 ${v})`).join('、') : '（无 —— 说明三个模型都不对，或扫描范围没覆盖）'}`);

// ---------- 收尾 ----------
log('');
log('=== 收尾 ===');
log(JSON.stringify(d.清理 || null, null, 1));
if (d.出错) log('出错：' + JSON.stringify(d.出错));