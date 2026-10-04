// 批次 164 —— 用新立规 34 回头核：**每一处「未执行 / 未验证」是否早已被别的批次验过**
//
// 🔑 起因：批次 163 立规 34「给自己的新发现定级之前，先去手册里搜一遍那个名词」。
//    本批把它变成一道**机械门**：对每个候选条目，把它的**关键词**回灌到全册里搜，
//    找出「同一件事在别处已经被验过并结清」的条目 —— 那就是**没销账**，不是「做不了」。
//
// 🔴 判据（刻意收窄，避免误报）：
//   ① 候选行必须含「未执行 / 未验证 / 未测 / 仍未测 / 未执行·」之一；
//   ② 同册必须存在另一处，明确用**同一个关键词**把这件事记成**已验/已结清/实测**；
//   ③ 两处的**关键词重叠**必须够长（本轮阈值 4 字），避免「点了/用了」这种泛词撞车；
//   ④ 只**报候选**，不自动改文档 —— 改法要人来判断是不是同一件事。
import fs from 'node:fs';
import { globSync } from 'node:fs';

const 根 = 'docs/user-manual/jimeng-canvas/';
const 跳过 = new Set(['SOURCE_OBSERVATIONS.md', 'AUDIT.md', 'PROGRESS.md']);
const 文件 = fs.readdirSync(根).filter((f) => f.endsWith('.md') && !跳过.has(f))
  .map((f) => ({ 名: f, 全文: fs.readFileSync(根 + f, 'utf8'), 行: fs.readFileSync(根 + f, 'utf8').split('\n') }))
  .concat(fs.readdirSync(根 + '10-tasks').filter((f) => f.endsWith('.md'))
    .map((f) => ({ 名: '10-tasks/' + f, 全文: fs.readFileSync(根 + '10-tasks/' + f, 'utf8'), 行: fs.readFileSync(根 + '10-tasks/' + f, 'utf8').split('\n') })));
void globSync;

const 未销标记 = /未执行|未验证|未测|仍未测|本手册不执行/;
const 已销标记 = /已结清|结清|实测|已打开取证|批次 \d+ 补测|已完成/;

// 从一行里抽「像关键词的」片段：书名号/方括号/引号里的内容，或连续的 2–8 字中文名词块
const 抽词 = (行) => {
  const 词 = new Set();
  for (const m of 行.matchAll(/[「『《]([^」』》]{2,10})[」』》]/g)) 词.add(m[1]);
  for (const m of 行.matchAll(/\[\[?([^\]]{2,12})\]\]?/g)) 词.add(m[1]);
  for (const m of 行.matchAll(/[一-龥]{4,8}/g)) 词.add(m[0]);
  return [...词];
};

const rec = { 批次: '164a', 目的: '找出「同一件事别处已结清、这里却还写着未执行」的没销账条目' };
const 候选 = [];
for (const f of 文件) {
  f.行.forEach((行, i) => {
    if (!未销标记.test(行)) return;
    const 词 = 抽词(行).filter((w) => w.length >= 4 && !/未执行|未验证|未测|仍未测/.test(w));
    for (const w of 词) {
      for (const g of 文件) {
        if (g.名 === f.名) continue;
        if (!g.全文.includes(w)) continue;
        const 命中行 = g.行.map((l, k) => ({ l, k })).filter((z) => z.l.includes(w) && 已销标记.test(z.l));
        if (!命中行.length) continue;
        候选.push({ 文件: f.名, 行号: i + 1, 关键词: w,
          未销原文: 行.trim().slice(0, 90),
          别处已销: 命中行.slice(0, 2).map((z) => ({ 文件: g.名, 行号: z.k + 1, 原文: z.l.trim().slice(0, 90) })) });
        break;
      }
    }
  });
}

// 去重：同一 (文件, 行号) 只留一条
const 见过 = new Set();
rec.候选 = 候选.filter((z) => {
  const k = z.文件 + ':' + z.行号;
  if (见过.has(k)) return false; 见过.add(k); return true;
});
rec.统计 = { 候选条数: rec.候选.length, 文件数: new Set(rec.候选.map((z) => z.文件)).size };
console.log('=== 可能是「没销账」的条目 ===');
console.log(JSON.stringify(rec.统计));
for (const z of rec.候选) {
  console.log('\n' + z.文件 + ':' + z.行号 + '   关键词「' + z.关键词 + '」');
  console.log('   未销：' + z.未销原文);
  for (const a of z.别处已销) console.log('   已销：' + a.文件 + ':' + a.行号 + '  ' + a.原文);
}
fs.writeFileSync('scripts/_tmp-b164a.json', JSON.stringify(rec, null, 1));
console.log('\n⚠️ 这些只是**候选**：要逐条人工判断「是不是同一件事」，本脚本不改文档。');
