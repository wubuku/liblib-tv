/**
 * 批次 264 · **审计台账自己**：有没有「因为 pattern 够不着而假通过」的条目。
 *
 * 📌 起意（立规 126 / 132 的应用）：批次 250 留过一条没关掉的悬念 ——
 *   「pattern **跨不过表格竖线**的覆盖缺口」。
 *   🔴 如果某条台账的 pattern **够不到它本该覆盖的那处原文**
 *   （典型：原文在**表格单元格里**，而 pattern 写成了含 `|` 的整行片段），
 *   那么这条 entry 的「`N` 处命中、`min_hits` 够数」就是**在一个更小的集合上算的**
 *   ⇒ **门会绿，而绿得没有意义**。
 *
 * 📌 本脚本**不复用** `jimeng-ledger-verify.mjs` 的判定逻辑，而是**独立重算**一遍
 *   （立规：校验器和被校验对象一样，要能被单独重跑；否则它自己成了不可信的东西），
 *   并且回答三个问题：
 *   ① 每条 pattern 在全册的**命中行**分别落在**表格行**还是普通正文行？
 *   ② 命中的**总行数**与该条 `min_hits` 差多少？有没有 **`0` 命中**的条目？
 *   ③ 有没有 pattern 里**含 `|`**（而 `|` 在正则里是元字符 ⇒ 会变成「或」）的条目？
 *      —— 这是「跨不过竖线」那个缺口的**真正可查形态**。
 *
 * 📌 判据（先写死）：
 *   · **`0` 命中**的条目 ⇒ **最可疑**，必须逐条人工看；
 *   · pattern **含 `|`** 且不是有意为之 ⇒ 会静默改变匹配范围，**必须报出来**；
 *   · 命中行**全在表格里**的条目 ⇒ 回填门在表格场景下的有效性**未经检验**，列出来。
 *
 * 🔴 纪律：**只读**，不改台账、不改手册；本批只产出读数。
 *
 * 用法：node scripts/jimeng-b264.mjs      （读数落盘 /tmp/b264.json）
 */
import fs from 'node:fs';
import path from 'node:path';

const 手册根 = path.resolve('docs/user-manual/jimeng-canvas');
const 台账 = JSON.parse(fs.readFileSync('scripts/jimeng-refuted-claims.json', 'utf8'));
const OUT = process.env.B264_OUT || '/tmp/b264.json';

const log = (...a) => console.log(a.join(' '));

const 走 = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
  const p = path.join(dir, d.name);
  if (d.isDirectory()) return d.name === 'node_modules' ? [] : 走(p);
  return d.name.endsWith('.md') ? [p] : [];
});

const 文件 = 走(手册根).map((f) => ({ 名: path.relative(手册根, f), 行: fs.readFileSync(f, 'utf8').split('\n') }));

/** 📌 一行是不是 markdown 表格行：首尾有 `|` 且有分隔行在上方 nearby 不必查，只看首尾 */
const 是表格行 = (行) => {
  const t = 行.trim();
  return t.startsWith('|') && t.endsWith('|') && t.length > 1;
};

const out = { 轮次: 'b264', 条目数: 台账.entries.length, 文件数: 文件.length, 条目: [], 汇总: {} };

台账.entries.forEach((条, idx) => {
  const 记 = { 下标: idx, id: 条.id, min_hits: 条.min_hits ?? null, pattern: 条.patterns, 命中: [], 含竖线: [], 零命中: false };
  for (const pat of 条.patterns) {
    let re;
    try { re = new RegExp(pat); } catch (e) { 记.非法正则 = pat; continue; }
    // 📌 「含竖线」——`| `在正则里是**或**，不是字面竖线 ⇒ 静默改变匹配范围
    if (pat.includes('|')) 记.含竖线.push(pat);
    for (const f of 文件) {
      f.行.forEach((ln, i) => {
        if (!re.test(ln)) return;
        记.命中.push({
          文件: f.名, 行号: i + 1,
          表格: 是表格行(ln),
          有订正标记: /订正|推翻|已被批次/.test(
            f.行.slice(Math.max(0, i - 3), i + 4).join('\n')),
          片段: ln.trim().slice(0, 90),
        });
      });
    }
  }
  记.命中数 = 记.命中.length;
  记.表格命中数 = 记.命中.filter((h) => h.表格).length;
  记.缺订正 = 记.命中.filter((h) => !h.有订正标记).length;
  记.零命中 = 记.命中数 === 0;
  // 📌 原始命中 = 总命中 − 「在介绍这个 pattern 的行」（自指）。这里做个粗略近似：
  //   含「台账 pattern」「pattern 是」「pattern="这类措辞的行视为自指候选。
  记.自指候选 = 记.命中.filter((h) => /台账 ?pattern|pattern ?是|pattern="/.test(h.片段)).length;
  out.条目.push(记);
});

const 零 = out.条目.filter((x) => x.零命中);
const 含竖线 = out.条目.filter((x) => x.含竖线.length > 0);
const 全表格 = out.条目.filter((x) => x.命中数 > 0 && x.表格命中数 === x.命中数);
const 缺订正 = out.条目.filter((x) => x.缺订正 > 0);

out.汇总 = {
  条目数: out.条目.length,
  零命中条数: 零.length,
  含竖线条数: 含竖线.length,
  命中全在表格的条数: 全表格.length,
  存在缺订正标记的条数: 缺订正.length,
};

log('=== 总览 ===');
log(JSON.stringify(out.汇总, null, 1));

if (零.length) {
  log(`\n=== 🔴 零命中的条目（${零.length} 条）—— 最可疑，必须逐条人工看 ===`);
  for (const x of 零) log(`  #${x.下标} ${x.id}｜pattern=${JSON.stringify(x.pattern)}`);
}
if (含竖线.length) {
  log(`\n=== 🔴 pattern 里含 \`|\` 的条目（${含竖线.length} 条）—— 会静默变成「或」 ===`);
  for (const x of 含竖线) log(`  #${x.下标} ${x.id}｜pattern=${JSON.stringify(x.含竖线)}`);
}
if (全表格.length) {
  log(`\n=== ⚠️ 命中全部落在表格行的条目（${全表格.length} 条）—— 表格场景的回填有效性未经检验 ===`);
  for (const x of 全表格) {
    log(`  #${x.下标} ${x.id}｜命中 ${x.命中数} 处，例：${x.命中[0].文件}:${x.命中[0].行号}`);
  }
}
if (缺订正.length) {
  log(`\n=== ⚠️ 存在「命中处 ±3 行内没有订正标记」的条目（${缺订正.length} 条）===`);
  for (const x of 缺订正) {
    log(`  #${x.下标} ${x.id}｜命中 ${x.命中数}、其中 ${x.缺订正} 处缺标记`);
    for (const h of x.命中.filter((y) => !y.有订正标记).slice(0, 3)) {
      log(`      ${h.文件}:${h.行号}（${h.表格 ? '表格行' : '正文行'}） ${h.片段}`);
    }
  }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}（覆盖 ${out.条目.length} 条 × ${文件.length} 个手册文件）`);
// 只读脚本，不关浏览器也不需要浏览器
process.exit(0);