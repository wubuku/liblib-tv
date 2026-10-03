// 批次 145 a 步（纯离线元审计，不开浏览器）：
// 逐条核对 SOURCE_OBSERVATIONS §4.49「全灭 testid」分诊表里的每个 testid，
// 看手册**别处**是否已经有它的契约记录 —— 有的话说明分诊表**没跟上**，属于漂移。
import fs from 'node:fs';
import path from 'node:path';

const DIR = '/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/jimeng-canvas';
const so = fs.readFileSync(path.join(DIR, 'SOURCE_OBSERVATIONS.md'), 'utf8').split('\n');

// 找分诊表所在行区间
const 起 = so.findIndex((L) => L.startsWith('| 全灭项 | 缺的前置状态 |'));
const 区 = so.slice(起, 起 + 14);

// 收集手册里所有 md（排除 SOURCE_OBSERVATIONS 自身，避免自证）
const 别处 = new Map();
const 走 = (d) => { for (const f of fs.readdirSync(d)) {
  if (f === 'node_modules' || f.startsWith('.')) continue;
  const q = path.join(d, f);
  if (fs.statSync(q).isDirectory()) { 走(q); continue; }
  if (!f.endsWith('.md')) continue;
  if (f === 'SOURCE_OBSERVATIONS.md') continue;
  const t = fs.readFileSync(q, 'utf8');
  别处.set(f, t);
} };
走(DIR);

const 名 = ['image-node-empty', 'audio-node-uploading', 'agent-skill-chip', 'workspace-project-info-dialog',
  'generation-form', 'generation-mention-panel', 'generation-mention-submenu',
  'generation-source-picker-chip', 'generation-source-picker-close',
  'canvas-source-picker-canvas-frame', 'text-editor-fullscreen-dialog',
  'text-editor-fullscreen-placeholder', 'text-editor-scroll-region', 'text-editor-toolbar',
  'selection-context-toolbar', 'canvas-agent-session-collapse'];

console.log('分诊表头行号', 起 + 1);
console.log('');
for (const n of 名) {
  const 命中 = [];
  for (const [f, t] of 别处) {
    const c = t.split('\n').filter((L) => L.includes(n)).length;
    if (c) 命中.push(f + '×' + c);
  }
  // 在 SOURCE_OBSERVATIONS 内部、但**不在**分诊表区段的出现处
  const soOther = so.map((L, i) => ({ L, i })).filter((o) => o.L.includes(n) && (o.i < 起 || o.i >= 起 + 14));
  const 分诊行 = so.slice(起, 起 + 14).find((L) => L.includes(n)) || '(不在分诊表)';
  console.log('■ ' + n);
  console.log('   别处手册命中: ' + (命中.length ? 命中.join(', ') : '❌ 无'));
  console.log('   SO 内其他处: ' + soOther.length + ' 行' + (soOther.length ? '（首个 L' + (soOther[0].i + 1) + '）' : ''));
  console.log('   分诊表现况: ' + 分诊行.replace(/\s+/g, ' ').slice(0, 150));
  console.log('');
}
