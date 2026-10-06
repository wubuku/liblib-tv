/**
 * 批次 265：把「缺订正标记」这个指标**修成可信的** —— 上一批它报了 `88` 处，九成是误报。
 *
 * 📌 起意（批次 264 的遗留）：审计报「命中处 ±3 行内没有订正标记」`88` 处，
 *   但逐条看下来**绝大多数本来就是已经订正过的行**（写着 `~~删除线~~`、「不成立」、
 *   「已关闭」、「作废」…）。
 *   🔴 根因：**判定器的标记词表太窄** —— `/订正|推翻|已被批次/` 只认 `3` 个词，
 *   而手册**实际在用**的订正措辞远不止这 `3` 个。
 *   ⚠️ **一个九成是噪声的指标比没有指标更糟：它训练你忽略它**（立规 142 的实践）。
 *
 * 📌 **词表是量出来的，不是猜的**（在 `docs/user-manual/jimeng-canvas` 下逐词计数）：
 *   `订正 1876`｜`推翻 1278`｜`🔴 6074`｜`⚠️ 3180`｜`❌ 1080`｜`~~ 1011`｜
 *   `不成立 464`｜`已被批次 243`｜`作废 175`｜`未复现 100`｜`已关闭 85`｜`已删除 50`｜`已过时 12`
 *   ⇒ 分成**强标记**（几乎必然是订正）与**弱标记**（`🔴`/`⚠️`/`❌` 单独出现时
 *     只是警告，**不能**算订正，但单独报出来）。
 *
 * 📌 **阳性对照是硬要求**（立规 132：报了「零」要能被证伪）：
 *   本脚本**在内存里**造两条同一 pattern 的行 ——
 *   ① 无任何标记 ⇒ **必须**被判成「缺标记」；
 *   ② 带 `~~` 与「不成立」 ⇒ **必须**被判成「已订正」；
 *   两条都判对 ⇒ 判定器才算被验证过。**全程不写手册。**
 *
 * 📌 只报的**可行动**清单 = **内容页**（`10-tasks/`、`20-reference`、`30-concepts`、
 *   `90-troubleshooting`、`00-quickstart`）里**既无强标记也无弱标记**的命中。
 *   日志页（`AUDIT`/`PROGRESS`/`SOURCE_OBSERVATIONS`）的命中**大多是订正记录本身**，
 *   单独计数、**不混进**可行动清单。
 *
 * 🔴 纪律：**只读**，不写手册、不改台账。
 *
 * 用法：node scripts/jimeng-b265.mjs      （读数落盘 /tmp/b265.json）
 */
import fs from 'node:fs';
import path from 'node:path';

const 手册根 = path.resolve('docs/user-manual/jimeng-canvas');
const 台账 = JSON.parse(fs.readFileSync('scripts/jimeng-refuted-claims.json', 'utf8'));
const OUT = process.env.B265_OUT || '/tmp/b265.json';

const log = (...a) => console.log(a.join(' '));

// 📌 词表按实测频次分组，**每一档都写清楚为什么在这一档**
const 强标记 = ['订正', '推翻', '已被批次', '不成立', '作废', '未复现', '已删除', '已过时', '已关闭', '~~'];
const 弱标记 = ['🔴', '⚠️', '❌'];

const 判标记 = (文本) => ({
  强: 强标记.filter((w) => 文本.includes(w)),
  弱: 弱标记.filter((w) => 文本.includes(w)),
});

const 内容页前缀 = ['10-tasks/', '20-reference.md', '30-concepts.md', '90-troubleshooting.md', '00-quickstart.md'];
const 日志页名 = ['AUDIT.md', 'PROGRESS.md', 'SOURCE_OBSERVATIONS.md'];
const 归类 = (f) => (内容页前缀.some((p) => f.startsWith(p) ? true : f === p) ? '内容页'
  : 日志页名.includes(f) ? '日志页' : '其它');

const 走 = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
  const p = path.join(dir, d.name);
  if (d.isDirectory()) return d.name === 'node_modules' ? [] : 走(p);
  return d.name.endsWith('.md') ? [p] : [];
});
const 文件 = 走(手册根).map((f) => ({ 名: path.relative(手册根, f), 行: fs.readFileSync(f, 'utf8').split('\n') }));

const 是表格行 = (行) => { const t = 行.trim(); return t.startsWith('|') && t.endsWith('|') && t.length > 1; };

// ============ 阳性对照：先证明判定器本身有效（全程不写手册） ============
const 对照 = (() => {
  const pat = '多选工具条里没有「Add tags」';           // 取一条真实 pattern 的字面片段
  const 邻1 = ['普通一行', '普通二行', pat, '普通四行'].join('\n');   // 无任何标记
  const 邻2 = ['普通一行', '普通二行', `~~${pat}~~ 🔴 不成立`, '普通四行'].join('\n');  // 带强标记
  const r1 = 判标记(邻1), r2 = 判标记(邻2);
  return {
    用例1_无标记: { 强: r1.强, 弱: r1.弱, 期望: '两档都空', 通过: r1.强.length === 0 && r1.弱.length === 0 },
    用例2_有标记: { 强: r2.强, 弱: r2.弱, 期望: '强标记非空', 通过: r2.强.length > 0 },
  };
})();

// ============ 全册重扫 ============
const out = { 轮次: 'b265', 词表: { 强标记, 弱标记 }, 阳性对照: 对照, 条目: [], 汇总: {} };
out.阳性对照通过 = 对照.用例1_无标记.通过 && 对照.用例2_有标记.通过;
log('=== 阳性对照（证明判定器本身有效）===');
log(`  用例1 无标记 → 强${JSON.stringify(对照.用例1_无标记.强)} 弱${JSON.stringify(对照.用例1_无标记.弱)} ${对照.用例1_无标记.通过 ? '✅' : '❌'}`);
log(`  用例2 有标记 → 强${JSON.stringify(对照.用例2_有标记.强)} 弱${JSON.stringify(对照.用例2_有标记.弱)} ${对照.用例2_有标记.通过 ? '✅' : '❌'}`);
if (!out.阳性对照通过) { log('🔴 判定器自检没过，后面结果不可用'); process.exit(4); }

台账.entries.forEach((条, idx) => {
  const 记 = { 下标: idx, id: 条.id, 命中: [] };
  for (const pat of 条.patterns) {
    let re; try { re = new RegExp(pat); } catch (e) { 记.非法正则 = pat; continue; }
    for (const f of 文件) {
      f.行.forEach((ln, i) => {
        if (!re.test(ln)) return;
        const 邻 = f.行.slice(Math.max(0, i - 3), i + 4).join('\n');
        const m = 判标记(邻);
        记.命中.push({
          文件: f.名, 行号: i + 1, 归类: 归类(f.名), 表格: 是表格行(ln),
          强: m.强, 弱: m.弱,
          档: m.强.length ? '已订正' : (m.弱.length ? '仅弱标记' : '无标记'),
          片段: ln.trim().slice(0, 95),
        });
      });
    }
  }
  记.命中数 = 记.命中.length;
  记.零命中 = 记.命中数 === 0;
  out.条目.push(记);
});

const 全部 = out.条目.flatMap((x) => x.命中.map((h) => ({ ...h, 下标: x.下标, id: x.id })));
out.汇总 = {
  条目数: out.条目.length,
  零命中条数: out.条目.filter((x) => x.零命中).length,
  命中总数: 全部.length,
  内容页命中: 全部.filter((h) => h.归类 === '内容页').length,
  日志页命中: 全部.filter((h) => h.归类 === '日志页').length,
  内容页无标记: 全部.filter((h) => h.归类 === '内容页' && h.档 === '无标记').length,
  内容页仅弱标记: 全部.filter((h) => h.归类 === '内容页' && h.档 === '仅弱标记').length,
  内容页已订正: 全部.filter((h) => h.归类 === '内容页' && h.档 === '已订正').length,
};

log('\n=== 总览（改用实测词表后）===');
log(JSON.stringify(out.汇总, null, 1));

const 可行动 = 全部.filter((h) => h.归类 === '内容页' && h.档 === '无标记');
log(`\n=== 🔴 可行动缺口：内容页里「无任何标记」的命中 ${可行动.length} 处 ===`);
for (const h of 可行动) {
  log(`  #${h.下标} ${h.id.slice(0, 42)}`);
  log(`     ${h.文件}:${h.行号}（${h.表格 ? '表格行' : '正文行'}）${h.片段}`);
}
const 仅弱 = 全部.filter((h) => h.归类 === '内容页' && h.档 === '仅弱标记');
if (仅弱.length) {
  log(`\n=== ⚠️ 内容页里「只有 🔴/⚠️/❌、没有强标记」的 ${仅弱.length} 处（需人工判读）===`);
  for (const h of 仅弱.slice(0, 12)) {
    log(`  #${h.下标} ${h.id.slice(0, 36)}｜${h.文件}:${h.行号}｜弱标记 ${JSON.stringify(h.弱)}`);
    log(`     ${h.片段}`);
  }
}
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);