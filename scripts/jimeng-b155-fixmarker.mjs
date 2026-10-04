// 批次 155 —— 回填门要求：命中行本身必须带订正标记。
// 🔴 上一版把整行换成了「导出时间线的状态（2026-10-04 批次 155 更新）：菜单层已验成 …」，
//    那行**没有**任何订正标记词（MARKER 认的是 推翻/订正/~~/已改为/口径/原写…）⇒ 门判红。
// ✅ 改成批次 153 定的形式：**原文加删除线 + 订正并进同一行**。
//    锚点同时含旧结论与订正标记词，行内自证。
import fs from 'node:fs';

const TL = new URL('../docs/user-manual/jimeng-canvas/10-tasks/timeline-node.md', import.meta.url);
const s = fs.readFileSync(TL, 'utf8');
const 锚 = '**导出时间线的状态（2026-10-04 批次 155 更新）**：**菜单层已验成**（`200×292`、四个导出目标 + 两个格式、\n空时间线上 MP4 禁用、`Esc` 一次可关），**最终导出仍未执行**（会产出对外文件）。';
const 新 = '**导出时间线的状态**：~~仍未实测：导出时间线（属对外产出动作，需单独授权）~~ 🔴 **2026-10-04 批次 155 订正**：**菜单层已验成**（`200×292`、四个导出目标 + 两个格式、\n空时间线上 MP4 禁用、`Esc` 一次可关），**最终导出仍未执行**（会产出对外文件）—— ⚠️ 但**理由已从「需单独授权」改为「本轮只验到菜单层」**，\n因为授权已解除，剩下的是「会产出对外文件」这条真实边界。';
const n = s.split(锚).length - 1;
console.log('锚点出现次数 =', n);
if (n !== 1) { console.log('⛔ 不是 1 次，不动'); process.exit(1); }
const t = s.replace(锚, 新);
if (t === s || t.indexOf(锚) >= 0) { console.log('⛔ 未生效或旧锚点仍在'); process.exit(1); }
fs.writeFileSync(TL, t);
console.log('✅ timeline-node.md 已改成「原文删除线 + 同行订正」');

// 同步改台账第 4 个 pattern
const F = new URL('./jimeng-refuted-claims.json', import.meta.url);
const raw = fs.readFileSync(F, 'utf8');
const j = JSON.parse(raw);
const e = j.entries[j.entries.length - 1];
const 旧p = e.patterns[3];
e.patterns[3] = '批次 155 订正\\*\\*：\\*\\*菜单层已验成';
const 后 = JSON.parse(JSON.stringify(j));
if (后.entries.length !== j.entries.length) { console.log('⛔ 条数变了'); process.exit(1); }
for (let i = 0; i < e.patterns.length; i++) {
  const ok = e.patterns[i] && e.patterns[i].length > 3;
  if (!ok) { console.log('⛔ pattern ' + i + ' 异常'); process.exit(1); }
}
fs.writeFileSync(F, JSON.stringify(j, null, 1) + '\n');
console.log('✅ 台账第 4 个 pattern：', 旧p, '→', j.entries[j.entries.length - 1].patterns[3]);
console.log('   条数 =', JSON.parse(fs.readFileSync(F, 'utf8')).entries.length);
