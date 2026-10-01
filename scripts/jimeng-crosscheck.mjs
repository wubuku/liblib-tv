// 即梦画布手册 · 跨层级一致性审计
// 目的：单一指标题推进时，每个批次只改一处，很容易留下「同一事实在台账/正文/
// 参考页/排障页说了不同的话」。本脚本按关键 token 扫描全目录的可疑表述，
// 供每批收尾与最终交付前复跑。命中不等于错误——历史观察与勘误记录属预期命中，
// 判读标准见 AUDIT.md「交叉一致性审计」。
import fs from 'node:fs';
import path from 'node:path';

const DIR = 'docs/user-manual/jimeng-canvas';
const files = fs.readdirSync(DIR).filter((f) => f.endsWith('.md'));
const read = (f) => fs.readFileSync(path.join(DIR, f), 'utf8');

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

let findings = 0;
for (const { id, label, patterns } of SUSPECT) {
  for (const f of files) {
    const lines = read(f).split('\n');
    for (const re of patterns) {
      lines.forEach((L, i) => {
        re.lastIndex = 0;
        if (re.test(L)) { console.log(`[${id}] ${label}\n    ${f}:${i + 1}  ${L.trim().slice(0, 120)}`); findings++; }
      });
    }
  }
}

// 2) 所有「未验证 / 未测 / 未执行」声明的分布
console.log('\n=== 证据边界声明分布（未验证/未测/未执行/环境限制） ===');
for (const f of files) {
  const s = read(f);
  const n = (s.match(/未验证|未测|未执行|未重测|环境限制|仍待验证/g) || []).length;
  if (n) console.log(`  ${f.padEnd(34)} ${n} 处`);
}

// 3) 缺口表里还标着未关闭的行
console.log('\n=== PROGRESS 缺口表中仍含「仍未/仅剩/未验证」的行 ===');
const prog = read('PROGRESS.md').split('\n');
prog.forEach((L, i) => {
  if (/^\|/.test(L) && /仅剩|仍未验证|未验证|环境限制|⚠️/.test(L) && !/^\|---/.test(L)) {
    const cells = L.split('|');
    const first = (cells[1] || '').trim();
    const last = (cells[cells.length - 2] || '').trim();
    console.log(`  L${i + 1}  ${first}  →  ${last.slice(0, 70)}`);
  }
});

console.log(`\n扫描完成：可疑命中 ${findings} 处`);
// 说明：本脚本只报「可疑位置」，不做通过/失败判定。
// 预期命中来源：(a) AUDIT.md 的勘误记录、(b) SOURCE_OBSERVATIONS.md 的历史观察
// （应带「已被推翻/补正」内联标记）、(c) 已内联标注订正的正文。
// 若某条命中**没有**任何订正标记，且不在上述两类文件中，即为需要处理的真实不一致。
