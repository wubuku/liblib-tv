// 批次 166-a —— 用 165 的副产品做一件以前做不到的事：
// **把手册里记录的每一个尺寸，拿去和源站 CSS 里的声明对账。**
//
// 🔑 为什么现在才做得了：批次 165 证明了「模态尺寸写死在 Tailwind 任意值类名里」，
//    且那份 CSS 可以在 Node 里 curl 下来静态搜。
//    ⇒ 「手册写的 548×688 是不是真的 548×688」不再需要开浏览器逐个量，
//    **可以一次性把全册的尺寸结论全查一遍** —— 这是纯静态的一轮。
//
// 📐 判据（刻意保守，只报候选）：
//   ① 从正文里抽出「**某个元素/testid 旁边出现的 N×M 屏上读数**」；
//   ② 在 CSS 里找「声明里同时含 N 与 M」的类名（宽度 Npx、高度 Mpx，或一条 min() 里都有）；
//   ③ 分三类：**对上**（CSS 里有对应声明）／**查无此值**（手册有读数但 CSS 里根本没有这两个数字，
//      ⇒ 要么量错了、要么那个尺寸不是写死的）／**只对上一半**。
//   ④ **只报候选、不改文档** —— 同页可能有两张表、同一尺寸可能出现在不同上下文。
import fs from 'node:fs';

const ROOT = 'docs/user-manual/jimeng-canvas/';
const CSS = '/tmp/jimeng-main.94b57a0e55.css';
const 跳过 = new Set(['SOURCE_OBSERVATIONS.md', 'AUDIT.md', 'PROGRESS.md', 'FINAL-REPORT.md', 'README.md']);

if (!fs.existsSync(CSS)) { console.error('⛔ 缺 CSS，先跑 node scripts/jimeng-b165f-inventory.mjs'); process.exit(2); }
const css = fs.readFileSync(CSS, 'utf8');
const 解转义 = (s) => s.replace(/\\2c\s?/g, ',').replace(/\\\]/g, ']').replace(/\\\(/g, '(').replace(/\\\)/g, ')').replace(/\\\//g, '/');

// ---- 建立「px 值 → 类名清单」索引（只看 width/height/max-*/min-* 的声明） ----
const 索引 = new Map();          // px 数字 → [{类名, 声明}]
for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  const 选择器 = m[1], 声明 = m[2];
  if (!/(?:^|[;{\s])(?:max-|min-)?(?:width|height)\s*:/.test(声明)) continue;
  const cls = 选择器.split(',').map((s) => s.trim()).filter((s) => /^\.[\w\\]/.test(s)).map((s) => '.' + 解转义(s.slice(1)));
  if (!cls.length) continue;
  for (const d of 声明.split(';')) {
    const [prop, ...v] = d.split(':');
    const p = (prop || '').trim();
    if (!/^(?:max-|min-)?(?:width|height)$/.test(p)) continue;
    const val = v.join(':').trim();
    for (const pm of val.matchAll(/(\d+)px/g)) {
      const n = parseInt(pm[1], 10);
      if (n < 20 || n > 4000) continue;
      if (!索引.has(n)) 索引.set(n, []);
      索引.get(n).push({ 类名: cls[0], 属性: p, 值: val });
    }
  }
}

// ---- 抽正文里的「N×M」读数及其上下文里的元素名 ----
const 读数 = [];
function 扫(名, 全文) {
  全文.split('\n').forEach((行, i) => {
    for (const m of 行.matchAll(/(\d{2,4})\s*×\s*(\d{2,4})/g)) {
      const w = parseInt(m[1], 10), h = parseInt(m[2], 10);
      // 上下文里找一个元素标识：testid / 反引号里的名字 / 行首的字段名
      const t = 行.match(/data-testid="([^"]+)"/);
      const b = 行.match(/`([^`]{2,60})`/);
      读数.push({ 文件: 名, 行号: i + 1, w, h, 逐字: 行.trim().slice(0, 130),
        元素: t ? 'testid=' + t[1] : (b ? '`' + b[1] + '`' : null) });
    }
  });
}
for (const f of fs.readdirSync(ROOT)) if (f.endsWith('.md') && !跳过.has(f)) 扫(f, fs.readFileSync(ROOT + f, 'utf8'));
for (const f of fs.readdirSync(ROOT + '10-tasks')) if (f.endsWith('.md')) 扫('10-tasks/' + f, fs.readFileSync(ROOT + '10-tasks/' + f, 'utf8'));

// ---- 对账 ----
const 结果 = [];
for (const r of 读数) {
  const hw = 索引.get(r.w), hh = 索引.get(r.h);
  // 「同一条声明里同时含 w 与 h」= 最强证据
  const 同条 = (hw || []).filter((a) => (hh || []).some((b) => b.类名 === a.类名 && b.值 === a.值));
  const 类 = 同条.length ? '同条声明' : (hw && hh ? '各有一条' : (hw || hh ? '只对上一半' : '两边都查无'));
  结果.push({ ...r, 判定: 类, 证据: (同条.length ? 同条 : (hw || hh || [])).slice(0, 2).map((z) => `${z.类名} → ${z.属性}: ${z.值}`) });
}

const 分组 = {};
for (const r of 结果) (分组[r.判定] ||= []).push(r);
const rec = { 批次: '166a', 目的: '全册尺寸读数 × 源站 CSS 声明 对账（纯静态，只报候选）',
  css字节: css.length, css内px值种类: 索引.size, 读数条数: 结果.length,
  统计: Object.fromEntries(Object.entries(分组).map(([k, v]) => [k, v.length])) };
console.log(JSON.stringify(rec.统计, null, 1));
for (const [k, arr] of Object.entries(分组)) {
  if (k === '同条声明' || k === '各有一条') continue;
  console.log('\n=== ' + k + '（' + arr.length + ' 条）===');
  for (const r of arr.slice(0, 40)) {
    console.log('  ' + r.文件 + ':' + r.行号 + '  ' + r.w + '×' + r.h + '  ' + (r.元素 || ''));
    console.log('     ' + r.逐字.slice(0, 110));
  }
}
console.log('\n=== 同条声明命中（示例 12 条，证明这条索引不是空的）===');
for (const r of (分组['同条声明'] || []).slice(0, 12)) console.log('  ' + r.文件 + ':' + r.行号 + '  ' + r.w + '×' + r.h + '  ⇒ ' + (r.证据[0] || ''));
fs.writeFileSync('scripts/_tmp-b166a.json', JSON.stringify({ 统计: rec.统计, 查无: 分组['两边都查无'] || [], 只一半: 分组['只对上一半'] || [], 同条条数: (分组['同条声明'] || []).length }, null, 1));
console.log('\n⚠️ 候选而已：「CSS 里没有这个数字」不等于手册写错（尺寸也可能来自内联样式或 JS 计算）。');
