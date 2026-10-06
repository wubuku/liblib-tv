/**
 * 校验台账某一条的 pattern 在**全册**的命中数，以及每处 ±3 行内有没有订正标记。
 *
 * 📌 为什么要单独写这个脚本：批次 236 里我内联的一次性校验只报出 2 处命中，
 *   而 `grep` 明确看到 4 处 —— **一次性内联脚本本身成了不可信的东西**。
 *   校验器必须和被校验的对象一样，能被单独重跑。
 *
 * 用法：node scripts/jimeng-ledger-verify.mjs [条目下标，默认最后一条]
 */
import fs from 'node:fs';
import path from 'node:path';

const 手册根 = path.resolve('docs/user-manual/jimeng-canvas');
const 台账 = JSON.parse(fs.readFileSync('scripts/jimeng-refuted-claims.json', 'utf8'));
const 下标 = process.argv[2] !== undefined ? Number(process.argv[2]) : 台账.entries.length - 1;
const 条 = 台账.entries[下标];

const 走 = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
  const p = path.join(dir, d.name);
  if (d.isDirectory()) return d.name === 'node_modules' ? [] : 走(p);
  return d.name.endsWith('.md') ? [p] : [];
});

let 总命中 = 0;
let 合规 = 0;
let 原文命中 = 0;
let 自指命中 = 0;
for (const f of 走(手册根)) {
  const 行 = fs.readFileSync(f, 'utf8').split('\n');
  条.patterns.forEach((pat) => {
    let re;
    try { re = new RegExp(pat); } catch (e) { console.error(`⛔ pattern 不是合法正则：${pat}`); process.exit(2); }
    行.forEach((ln, i) => {
      if (!re.test(ln)) return;
      总命中 += 1;
      // 📌 批次 236 踩到并治本：一旦把 pattern **写进文档**（「台账 pattern 是 XXX」），
      //    那一行会**自己命中自己** ⇒ 原始命中数每被记录一次就多 1，数字永远对不上。
      //    ⇒ 把「讲这个 pattern 的行」单列为**自指命中**，`min_hits` 只管**原文命中**。
      const 自指 = /pattern|台账/.test(ln);
      if (自指) 自指命中 += 1; else 原文命中 += 1;
      const 邻 = 行.slice(Math.max(0, i - 3), Math.min(行.length, i + 4)).join('\n');
      const 有订正 = /订正|推翻|已被批次/.test(邻);
      if (有订正) 合规 += 1;
      console.log(`${有订正 ? '✅' : '🔴'} ${自指 ? '［自指］' : '［原文］'} ${path.relative(手册根, f)}:${i + 1}  pattern=${JSON.stringify(pat)}`);
    });
  });
}

const 声明 = typeof 条.min_hits === 'number' ? 条.min_hits : null;
console.log(`\n条目 ${下标 + 1}/${台账.entries.length}「${条.id}」`);
console.log(`  原文命中 ${原文命中} 处 ＋ 自指命中 ${自指命中} 处 ＝ 合计 ${总命中} 处；±3 行内有订正标记 ${合规} 处`);
if (声明 !== null) console.log(`  min_hits 声明 ${声明}（只对**原文命中**计数）⇒ ${原文命中 >= 声明 ? '✅ 够数' : '🔴 漏覆盖'}`);
process.exit(合规 === 总命中 && (声明 === null || 原文命中 >= 声明) ? 0 : 1);
