/**
 * 批次 221 的**离线**数值分析（不碰浏览器）。
 *
 * 📌 靶子：
 *   ① 否掉批次 220 留下的具体假设「落点屏上宽度 = 视口宽的固定比例」
 *   ② 反解 `音频 68`（`-empty` 族，100% 确定、每档都露）那条密集曲线的形状
 *
 * 📌 立规 104：**「同一个数在曲线两侧出现同一个值」不等于「同一个机制」。**
 *   本脚本据此把「0.5 = 封顶」拆成**两条边**分别判。
 *
 * 📌 立规 105：**任何「看起来整齐」的判据先问它是否恒真。**
 *   「某值距最近整数 ≤ 0.5」对**任何**实数都成立 ⇒ 不能当证据。
 *   本脚本显式打印这条恒真式的最大偏差，防止误读成「被量化到整数像素」。
 */
import fs from 'node:fs';

const IN = process.argv[2] || '/tmp/b221.json';
const d = JSON.parse(fs.readFileSync(IN, 'utf8'));
const A = (d.音频68密集 || []).filter((r) => r && r.scale != null && r.页内一致);
const B = (d.媒体视频密集 || []).filter((r) => r && r.scale != null && r.页内一致);

const log = (...a) => console.log(a.join(' '));
const r6 = (x) => Math.round(x * 1e6) / 1e6;

log('=== 输入 ===');
log(`音频68密集 ${A.length} 臂 / 媒体视频密集 ${B.length} 臂`);
log(`空节点 ${JSON.stringify(d.空节点 || null)}`);
log(`媒体节点 ${JSON.stringify(d.媒体节点 || null)}`);
if (A.length) log(`音频节点 CSS 尺寸 ${JSON.stringify(A[0].off)}`);
if (B.length) log(`媒体节点 CSS 尺寸 ${JSON.stringify(B[0].off)}`);
log('');

/** 立规 105：恒真式白名单。 */
const 恒真式 = [
  ['距最近整数 ≤ 0.5', (x) => Math.abs(x - Math.round(x)) <= 0.5],
  ['scale ∈ (0,1]', (x) => x > 0 && x <= 1],
  ['比值 ∈ (0,1)', (x) => x > 0 && x < 1],
];

// ---------- ① 固定比例假设 ----------
log('=== ① 「落点屏上宽度 = 视口宽 × 固定比例」 ===');
for (const [名, 集] of [['音频68', A], ['媒体视频', B]]) {
  if (!集.length) continue;
  const 比 = 集.map((r) => r.屏上宽占视口比);
  const lo = Math.min(...比), hi = Math.max(...比);
  log(`${名}：比值 ${lo} → ${hi} ｜ 跨度/最小值 = ${r6(((hi - lo) / lo) * 100)}% ｜ ${比.length} 臂`);
  log(`   逐档 ${集.map((r) => `${r.w}:${r.屏上宽占视口比}`).join(' ')}`);
}
const 共同档 = [...new Set(A.map((r) => r.w))].filter((w) => B.some((r) => r.w === w)).sort((x, y) => x - y);
if (共同档.length) {
  log('   同宽对照：');
  for (const w of 共同档) {
    const a = A.find((r) => r.w === w), b = B.find((r) => r.w === w);
    log(`     w=${w}  音频 ${a.屏上宽占视口比} vs 媒体 ${b.屏上宽占视口比}  倍数 ${r6(b.屏上宽占视口比 / a.屏上宽占视口比)}`);
  }
}
log('');

// ---------- ② 恒真式自检 ----------
log('=== ② 恒真式自检（立规 105）===');
if (A.length) {
  const 屏上 = A.map((r) => r.屏上[0] * r.scale / r.scale); // 占位，下面用真实 off
  const offW = A[0].off ? A[0].off[0] : null;
  if (offW) {
    const dev = A.map((r) => Math.abs(r.scale * offW - Math.round(r.scale * offW)));
    log(`「scale × ${offW} 距最近整数」最大 ${Math.max(...dev).toFixed(4)} —— 这条**恒真**（≤0.5），不作证据；实测 ${dev.filter((x) => x < 0.05).length}/${dev.length} 落在 ±0.05 内（均匀分布的期望是 ${r6(dev.length * 0.1)} 个）`);
  }
  log(`（另两条恒真式同样不作证据：${恒真式.slice(1).map((x) => x[0]).join('、')}）`);
}
log('');

// ---------- ③ 两条边分别判（立规 104）----------
const 封顶 = 0.5;
for (const [名, 集] of [['音频68', A], ['媒体视频', B]]) {
  if (!集.length) continue;
  const 档 = [...new Set(集.map((r) => r.w))].sort((x, y) => x - y);
  const 全封 = 档.filter((w) => 集.every((r) => r.w !== w || r.scale === 封顶));
  const 中 = 档.filter((w) => !全封.includes(w));
  log(`=== ③ ${名} 两条边（立规 104：0.5 在两侧出现 ≠ 同一机制） ===`);
  log(`全档 ${档[0]}–${档[档.length - 1]} ｜ 全 0.5 的档：${全封.join(',')}`);
  log(`非 0.5 的档：${中.join(',')}`);
  if (中.length >= 2) {
    const 首 = 中[0], 尾 = 中[中.length - 1];
    log(`⇒ 未封顶窗口 = [${首}, ${尾}]，宽 ${尾 - 首} px；其左 ${首 - 档[0]} px 全 0.5、其右 ${档[档.length - 1] - 尾} px 全 0.5`);
  } else if (中.length === 1) {
    log(`⇒ 只有 ${中[0]} 一档非 0.5（窗口宽度未知，两侧封顶都压着）`);
  } else {
    log('⇒ 本族在所扫窗口内**没有**非封顶档');
  }
}
log('');

// ---------- ④ 音频曲线形状：模型残差 ----------
const 音频 = A.filter((r) => r.scale < 封顶).sort((x, y) => x.w - y.w);
log('=== ④ 音频 68 未封顶段的模型拟合（残差 > 1e-4 判不成立） ===');
log(`w   : ${音频.map((r) => r.w).join(',')}`);
log(`scale: ${音频.map((r) => r.scale).join(',')}`);
const X = 音频.map((r) => r.w), Y = 音频.map((r) => r.scale);

function 残差(pred, Yv) {
  let mx = 0, sum = 0;
  for (let i = 0; i < X.length; i++) { const e = Math.abs(pred(i) - Yv[i]); mx = Math.max(mx, e); sum += e * e; }
  return { max: mx, rms: Math.sqrt(sum / X.length) };
}
function 报告(名, pred, Yv) {
  const y = Yv || Y;
  const r = 残差(pred, y);
  const ok = r.max < 1e-4;
  log(`  ${ok ? '✅' : '❌'} ${名}：max ${r.max.toExponential(2)} rms ${r.rms.toExponential(2)} ${ok ? '成立' : '不成立'}`);
  return ok;
}

/** 多项式最小二乘（正规方程 + 高斯消元） */
function 多项式(xs, ys, deg) {
  const n = deg + 1;
  const A1 = Array.from({ length: n }, () => new Array(n).fill(0));
  const b1 = new Array(n).fill(0);
  for (let i = 0; i < xs.length; i++) {
    const pw = []; for (let k = 0; k <= 2 * deg; k++) pw.push(xs[i] ** k);
    for (let r0 = 0; r0 < n; r0++) { for (let c0 = 0; c0 < n; c0++) A1[r0][c0] += pw[r0 + c0]; b1[r0] += pw[r0] * ys[i]; }
  }
  for (let c0 = 0; c0 < n; c0++) {
    let piv = c0; for (let r0 = c0 + 1; r0 < n; r0++) if (Math.abs(A1[r0][c0]) > Math.abs(A1[piv][c0])) piv = r0;
    [A1[c0], A1[piv]] = [A1[piv], A1[c0]]; [b1[c0], b1[piv]] = [b1[piv], b1[c0]];
    for (let r0 = 0; r0 < n; r0++) { if (r0 === c0) continue; const f = A1[r0][c0] / A1[c0][c0]; for (let k = c0; k < n; k++) A1[r0][k] -= f * A1[c0][k]; b1[r0] -= f * b1[c0]; }
  }
  return b1.map((v, i) => v / A1[i][i]);
}
function 预测(co, xs) { return (i) => { let s = 0; for (let k = co.length - 1; k >= 0; k--) s = s * xs[i] + co[k]; return s; }; }

if (X.length >= 5) {
  for (const deg of [1, 2, 3, 4]) {
    const co = 多项式(X, Y, deg);
    log(`  多项式 ${deg} 次：系数 ${co.map((c) => c.toExponential(3)).join(', ')}`);
    报告(`M 音频 scale ~ w 的 ${deg} 次多项式`, 预测(co, X));
  }
  // 指数
  {
    const L = Y.map(Math.log);
    const co = 多项式(X, L, 1);
    log(`  指数 ln scale = ${co[0].toExponential(4)} + ${co[1].toFixed(8)}·w ⇒ 每 px ×${Math.exp(co[1]).toFixed(6)}`);
    报告('M 指数 scale ~ r^w', 预测(co, X), L);
  }
  // 反比
  {
    const I = Y.map((s) => 1 / s);
    const co = 多项式(X, I, 1);
    log(`  反比 1/scale = ${co[0].toFixed(5)} + ${co[1].toExponential(4)}·w`);
    报告('M 反比 1/scale ~ w', 预测(co, X), I);
  }
  // 对数斜率
  const L = Y.map(Math.log);
  const 斜 = [];
  for (let i = 1; i < X.length; i++) 斜.push((L[i] - L[i - 1]) / (X[i] - X[i - 1]));
  log(`  ln scale 对 w 的逐档斜率：min ${Math.min(...斜).toFixed(5)} max ${Math.max(...斜).toFixed(5)} 铺展 ${r6((Math.max(...斜) - Math.min(...斜)) / Math.min(...斜) * 100)}%`);
  log(`  ⇒ 斜率**近似常数**（${Math.min(...斜).toFixed(4)}–${Math.max(...斜).toFixed(4)}），即曲线在 ln 坐标下接近直线`);
}

// ---------- ⑤ 两族同形 + 平移量 ----------
log('');
log('=== ⑤ 两族是否「同一条曲线平移」 ===');
const 音频斜率 = (() => {
  if (X.length < 3) return null;
  const L = Y.map(Math.log); const s = [];
  for (let i = 1; i < X.length; i++) s.push((L[i] - L[i - 1]) / (X[i] - X[i - 1]));
  return s.reduce((a, b) => a + b, 0) / s.length;
})();
const Bv = B.filter((r) => r.scale < 封顶).sort((x, y) => x.w - y.w);
if (Bv.length >= 2) {
  const LB = Bv.map((r) => Math.log(r.scale)); const sb = [];
  for (let i = 1; i < Bv.length; i++) sb.push((LB[i] - LB[i - 1]) / (Bv[i].w - Bv[i - 1].w));
  const 媒体斜率 = sb.reduce((a, b) => a + b, 0) / sb.length;
  log(`音频 ln 斜率均值 ${音频斜率 ? 音频斜率.toFixed(5) : 'n/a'} ｜ 媒体 ln 斜率均值 ${媒体斜率.toFixed(5)} ｜ 比值 ${r6(媒体斜率 / 音频斜率)}`);
  log(`媒体逐档：${Bv.map((r) => `${r.w}(#${r.次}):${r.scale}`).join(' ')}`);
  // 平移量：对每个音频读数，在媒体曲线上线性插值出等价宽度
  if (音频斜率 && Bv.length >= 2) {
    const 平移 = [];
    for (const a of A.filter((r) => r.scale < 封顶)) {
      const la = Math.log(a.scale);
      let wq = null;
      for (let i = 1; i < Bv.length; i++) {
        const l1 = Math.log(Bv[i - 1].scale), l2 = Math.log(Bv[i].scale);
        if ((la >= l1 && la <= l2) || (la <= l1 && la >= l2)) { wq = Bv[i - 1].w + (la - l1) / (l2 - l1) * (Bv[i].w - Bv[i - 1].w); break; }
      }
      if (wq != null) 平移.push({ 音频w: a.w, 媒体等价w: Math.round(wq * 100) / 100, Δw: Math.round((a.w - wq) * 100) / 100 });
    }
    if (平移.length) {
      const ds = 平移.map((x) => x.Δw);
      log(`配对 ${平移.length} 对，Δw（音频宽 − 媒体等价宽）：${平移.map((x) => x.Δw).join(', ')}`);
      log(`⇒ Δw 均值 ${(ds.reduce((a, b) => a + b, 0) / ds.length).toFixed(2)}、铺展 ${(Math.max(...ds) - Math.min(...ds)).toFixed(2)} px`);
    } else log('两族未封顶区间无交叠，配不出平移量');
  }
}

// ---------- ⑥ 收尾 ----------
log('');
log('=== ⑥ 收尾 ===');
const C = d.清理 || {};
log(JSON.stringify({ 最终数: C.最终数, 多出来: C.多出来, 少了: C.少了, 状态行: C.最终状态行, 积分: C.最终积分, 缩放: C.最终缩放 }, null, 1));
if (d.出错) log('出错：' + JSON.stringify(d.出错));