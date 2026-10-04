import fs from 'node:fs';
const j = JSON.parse(fs.readFileSync('scripts/_tmp-b151.json', 'utf8'));

// 🔴 批次 151 脚本里的 `两态差异` 比的是**量_静息态[0]** 与 **量_选中态[0]** ——
//    同一个**节点下标 0**，而它两遍都是**非选中**（选中的是下标 2）。
//    ⇒ 「选中态独有元素 = []」「共有但两态尺寸变 = []」两条结论是**无效的**。
//    这里离线按**同下标**重算，不再连浏览器。
const out = [];
for (const q of j.族) {
  const A = q.量_选中态, B = q.量_静息态;
  if (!A || !B) continue;
  const 每节点 = [];
  for (let k = 0; k < A.length; k++) {
    const a = A[k], b = B[k];
    if (!a || !b || !a.元素 || !b.元素) { 每节点.push({ 下标: k, __err: 'no-elements' }); continue; }
    const ka = Object.keys(a.元素), kb = Object.keys(b.元素);
    const 只在A = ka.filter((x) => !kb.includes(x));           // A 是「建完」态
    const 只在B = kb.filter((x) => !ka.includes(x));
    const 变 = ka.filter((x) => kb.includes(x) && JSON.stringify(a.元素[x].屏上) !== JSON.stringify(b.元素[x].屏上))
      .map((x) => ({ 元素: x, A屏上: a.元素[x].屏上, B屏上: b.元素[x].屏上, Acss: a.元素[x].css, Bcss: b.元素[x].css }));
    每节点.push({
      下标: k, A选中: a.选中, B选中: b.选中,
      A节点屏上: a.节点屏上, B节点屏上: b.节点屏上,
      只在A, 只在B, 变,
    });
  }
  out.push({ 族: q.族, 缩放: q.缩放建后, 实测scale: q.实测scale,
    建完后选中数: q.建完后选中数, 清零后选中数: q.清零后选中数, 每节点 });
}

console.log('=== 修正后：按**同一下标**比对「建完」与「清零后」两遍 ===');
for (const q of out) {
  console.log('\n【' + q.族 + '】' + q.缩放 + ' 实测 ' + q.实测scale + ' | 建完后选中数 ' + q.建完后选中数 + ' → 清零后 ' + q.清零后选中数);
  for (const n of q.每节点) {
    console.log('  下标' + n.下标 + ' A选中=' + n.A选中 + ' B选中=' + n.B选中 +
      ' | 只在建完态出现: ' + JSON.stringify(n.只在A) + ' | 只在清零后出现: ' + JSON.stringify(n.只在B));
    for (const c of (n.变 || [])) console.log('      变 ' + c.元素 + ' 建完 ' + JSON.stringify(c.A屏上) + ' → 清零后 ' + JSON.stringify(c.B屏上));
  }
}

console.log('\n=== Q4 换算：屏上 ÷ (css × 实测scale) = 补偿系数 k ===');
for (const d of (j.缩放档?.档 || [])) {
  const s = d.实测scale;
  console.log('\n实测 ' + s + '（aria ' + d.aria + '）| 1/s = ' + (1 / s).toFixed(4));
  for (const b of (d.三节点是否全同 || [])) {
    const 屏 = b.屏上 && b.屏上[0]; const css = b.css && b.css[0];
    if (!屏 || !css) { console.log('   ', b.元素, '缺读数'); continue; }
    const w = parseFloat(屏[0]), h = parseFloat(屏[1]);
    const cw = parseFloat(css[0]), ch = parseFloat(css[1]);
    const kw = w / (cw * s), kh = h / (ch * s);
    console.log('   ' + b.元素.padEnd(30) + ' css ' + String(css).padEnd(18) + ' 屏上 ' + String(屏).padEnd(18) +
      ' k_宽=' + kw.toFixed(4) + ' k_高=' + kh.toFixed(4));
  }
}

console.log('\n=== Q3：flow-node-title 的 innerText 与宽度 ===');
for (const q of out) {
  const B = q.每节点;
  void B;
}
for (const q of j.族) {
  const t = (q.量_静息态 || []).map((m) => {
    const e = m.元素 && m.元素['flow-node-title'];
    return e ? { 文字: e.文字, 屏上: e.屏上, css: e.css, 字体: e.字体, 行高: e.行高 } : null;
  });
  console.log('【' + q.族 + '】缩放 ' + q.缩放建后 + '  ' + JSON.stringify(t));
}
