// 批次 126 · 收窄第 51 条的 patterns。
// 起因：回填门把 pattern 当正则，且要求**每一处**命中 ±3 行内都有订正标记。
// 原来那个裸的 `一级页签` 命中了**资产库**面板的真·一级页签（资产 / 主体）——
// 那是另一个面板的正确记录，属于误报，必须收窄。
// 收窄原则：只保留**唯一指代本条被推翻主张**的措辞。
import { readFileSync, writeFileSync } from 'node:fs';

const f = new URL('./jimeng-refuted-claims.json', import.meta.url);
const j = JSON.parse(readFileSync(f, 'utf8'));
const e = j.entries.find((c) => c.id === 'generation-history-panel-has-no-primary-tabs');
if (!e) { console.error('找不到该条'); process.exit(1); }

e.patterns = [
  '一级页签两个',
  '一级页签两项',
  '生成历史两级页签',
  '面板分两层',
  '面板分两级',
];
e.pattern_note =
  '（批次 126 建条时留的坑：patterns 一开始写了裸的「一级页签」与「分两层」，' +
  '结果命中**资产库面板的真·一级页签**（`资产` / `主体`）和别的句式 —— ' +
  '那不是被推翻的结论，是另一个面板的正确记录。' +
  '⇒ 立规：**refuted-claims 的 pattern 必须唯一指代那条被推翻的主张**，' +
  '宁可写长一点、带上下文，也不要写「这类话里常出现的那个词」。）';

writeFileSync(f, JSON.stringify(j, null, 2) + '\n');
console.log('patterns 收窄为：', JSON.stringify(e.patterns, null, 1));
