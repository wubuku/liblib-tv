// 即梦画布手册 · 跨层级一致性审计 v2
//
// v1 的盲口（本批修掉）：`fs.readdirSync(DIR).filter(f => f.endsWith('.md'))`
// **只扫顶层 .md** ⇒ 10-tasks/ 下的 **17 个任务页一篇都不扫**。
// 而任务页正是读者真正会读的那一层 —— 扫描器覆盖最薄的地方，恰好是错字最多、
// 最容易前后矛盾的地方。
//
// 修法：递归收集 .md（含 10-tasks/）。
// 并且**自证这不是我记错了**：v2 带一个 --selftest，把一条已知的坏句子
// 临时写进一个**任务页**，断言「v1 扫不到 / v2 扫得到」，再把文件还原。
// 没有阳性对照的「修好了」不算修好了（批次 58 的教训）。
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const DIR = 'docs/user-manual/jimeng-canvas';

// 1) 跨文件矛盾扫描：同一关键 token 在不同文件里的「否定/过期措辞」
const SUSPECT = [
  { id: 'hand-tool', label: '抓手工具前提（空白拖拽=平移）',
    patterns: [/空白[^。\n]{0,20}拖[^。\n]{0,20}(不是平移|不平移)/g, /平移请用[^。\n]{0,10}滚轮/g] },
  { id: 'cmdV', label: '⌘V 粘贴可用性',
    patterns: [/⌘V[^。\n]{0,30}(未生效|没有反应|不可用|暂无可靠手势)/g] },
  { id: 'delete-key', label: 'Delete vs Backspace',
    patterns: [/按\s*[`*]?Delete[`*]?\s*(键)?[^。\n]{0,20}删除/g] },
  { id: 'cmdA', label: '⌘A 全选',
    patterns: [/⌘A[^。\n]{0,25}(不存在|没反应|未生效)/g] },
  { id: 'edge-dom', label: '边是否有 DOM',
    patterns: [/无\s*`?\.react-flow__edge/gi, /无\s*\.react-flow__edge/gi] },
  { id: 'node-count-plural', label: '状态行复数写法',
    patterns: [/`1 nodes/g, /1 nodes, 0 edges/g] },
  { id: 'rightclick', label: '右键菜单可靠性',
    patterns: [/右键菜单[^。\n]{0,30}(不弹出|不可依赖)/g] },
  { id: 'tags-color-names', label: '标记色板色名逐字',
    patterns: [/青\/蓝\/紫\/橙\/黄/g] },
  { id: 'save-to-subject', label: '保存到主体库',
    patterns: [/可能多出[^。\n]{0,10}保存到主体库/g] },
  { id: 'text-style-menu', label: 'Text style 菜单项数',
    patterns: [/仅三项|只有三项/g] },
  { id: 'minimap-esc', label: '小地图 Esc 关闭',
    patterns: [/小地图[^。\n]{0,30}Esc[^。\n]{0,10}(可|能)关/g] },
  { id: 'back-to-node', label: '回到节点按钮',
    patterns: [/回到节点[^。\n]{0,30}(仅在需要时出现|出现条件未)/g] },
];

// v1 的收集方式（故意保留，用来演示盲口）；返回**全路径**，与 v2 可比
const collectV1 = (dir) => fs.readdirSync(dir).filter((f) => f.endsWith('.md')).map((f) => path.join(dir, f));
// v2：递归
const collectV2 = (dir) => {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...collectV2(p));
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
};
const read = (f) => fs.readFileSync(f, 'utf8');

function scan(files) {
  const hits = [];
  for (const { id, label, patterns } of SUSPECT) {
    for (const f of files) {
      const lines = read(f).split('\n');
      for (const re of patterns) {
        lines.forEach((L, i) => {
          re.lastIndex = 0;
          if (re.test(L)) hits.push({ id, label, file: f, line: i + 1, text: L.trim().slice(0, 120) });
        });
      }
    }
  }
  return hits;
}

// ---------- 阳性对照自测：证明 v1 真的漏、v2 真的补上了 ----------
function selftest() {
  const victim = path.join(DIR, '10-tasks/_crosscheck-selftest.md');
  const marker = '> ⌘A 全选没反应，本页是阳性对照夹具。\n';
  if (fs.existsSync(victim)) { console.error('夹具已存在，先手动清理:', victim); process.exit(9); }
  const v1 = collectV1(DIR), v2 = collectV2(DIR);
  const beforeV1 = scan(v1).length, beforeV2 = scan(v2).length;
  fs.writeFileSync(victim, `# 自测夹具\n\n${marker}`);
  try {
    const afterV1 = scan(collectV1(DIR)).length, afterV2 = scan(collectV2(DIR)).length;
    const v1Caught = afterV1 > beforeV1, v2Caught = afterV2 > beforeV2;
    const pickedUp = scan(collectV2(DIR)).some((h) => h.file === victim);
    console.log(`阳性对照：往**任务页**里植入一条已知坏句子（「⌘A 全选没反应」）`);
    console.log(`  v1（只扫顶层）命中数 ${beforeV1} → ${afterV1}  ${v1Caught ? '🔴 扫到了' : '✅ 没扫到 —— 盲口是实的'}`);
    console.log(`  v2（递归）　  命中数 ${beforeV2} → ${afterV2}  ${v2Caught ? '✅ 扫到了 —— 盲口已补' : '🔴 没扫到！'}`);
    console.log(`  v2 命中里包含夹具文件本身：${pickedUp ? '✅' : '🔴'}`);
    const ok = !v1Caught && v2Caught && pickedUp;
    console.log(ok ? '✅ 自测通过：盲口确实存在，且 v2 确实补上了' : '❌ 自测不通过');
    return ok;
  } finally { fs.unlinkSync(victim); }
}

if (process.argv.includes('--selftest')) {
  process.exit(selftest() ? 0 : 1);
}

const v1Files = collectV1(DIR).map((f) => f);
const v2Files = collectV2(DIR);
const h1 = scan(v1Files), h2 = scan(v2Files);
const oldSet = new Set(h1.map((x) => `${x.id}|${x.file}|${x.line}`));
const fresh = h2.filter((x) => !oldSet.has(`${x.id}|${x.file}|${x.line}`));

console.log(`v1 覆盖 ${v1Files.length} 个文件 → ${h1.length} 处命中`);
console.log(`v2 覆盖 ${v2Files.length} 个文件 → ${h2.length} 处命中（新增 ${fresh.length} 处，全部来自 10-tasks/）\n`);
if (fresh.length) {
  console.log('=== 🔴 v1 漏掉、v2 新抓到的命中 ===');
  for (const x of fresh) console.log(`[${x.id}] ${x.label}\n    ${path.relative(DIR, x.file)}:${x.line}  ${x.text}`);
  console.log();
}
console.log('=== v2 全部命中（按文件） ===');
const byFile = {};
for (const x of h2) (byFile[x.file] ||= []).push(x);
for (const f of Object.keys(byFile).sort()) {
  console.log(`  ${path.relative(DIR, f).padEnd(28)} ${byFile[f].length} 处`);
}

console.log('\n=== 证据边界声明分布（未验证/未测/未执行/环境限制） ===');
for (const f of v2Files) {
  const n = (read(f).match(/未验证|未测|未执行|未重测|环境限制|仍待验证/g) || []).length;
  if (n) console.log(`  ${path.relative(DIR, f).padEnd(34)} ${n} 处`);
}

console.log('\n=== PROGRESS 缺口表中仍含「仍未/仅剩/未验证」的行 ===');
const prog = read(path.join(DIR, 'PROGRESS.md')).split('\n');
prog.forEach((L, i) => {
  if (/^\|/.test(L) && /仅剩|仍未验证|未验证|环境限制|⚠️/.test(L) && !/^\|---/.test(L)) {
    const cells = L.split('|');
    console.log(`  L${i + 1}  ${(cells[1] || '').trim()}  →  ${(cells[cells.length - 2] || '').trim().slice(0, 70)}`);
  }
});

console.log(`\n扫描完成：v1 ${h1.length} 处 / v2 ${h2.length} 处（v1 漏 ${fresh.length} 处）`);
console.log('说明：本脚本只报「可疑位置」，不做通过/失败判定。');
console.log('预期命中来源：(a) AUDIT.md 的勘误记录、(b) SOURCE_OBSERVATIONS.md 的历史观察');
console.log('（应带「已被推翻/补正」内联标记）、(c) 已内联标注订正的正文。');
console.log('若某条命中**没有**任何订正标记，且不在上述两类文件中，即为需要处理的真实不一致。');
