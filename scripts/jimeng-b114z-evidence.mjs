// 批次 114 · z 轮证据**补录**。
//
// ⚠️ 为什么需要这个脚本：z 轮脚本是从批次 113 复制来的，复制时把落盘文件名
//    `._tmp-b113z.json` 一起复制了过去（替换时漏了），于是第一次 z 轮把证据
//    **误写进了批次 113 的证据文件**。
//    处置：① `git show HEAD:scripts/_tmp-b113z.json > …` 把批次 113 的证据原样恢复
//    （**不**用 stash / reset / checkout，**不**动索引）；
//    ② 改掉 b114z 脚本里的落盘名后重跑 —— 但节点此时已删，三条目标全 `skipped`。
// ⇒ 本脚本把**第一次 z 轮的真实读数**（/tmp/b114z.log）按证据格式补录回来，
//    并保留第二次重跑的 `skipped` 记录作为「为什么没有第一份文件」的说明。
//
// 📌 教训：**复制脚本时，落盘文件名也是「判据的一部分」** ——
//    证据文件名错一次，就会覆盖上一批的证据。
import { readFileSync, writeFileSync } from 'node:fs';

const P = new URL('./_tmp-b114z.json', import.meta.url);
const j = JSON.parse(readFileSync(P, 'utf8'));

// 第一次 z 轮的真实读数（逐条照抄 /tmp/b114z.log 的输出）
j.deletions = [
  { id: 'node_fnarb6091q', by: 'a 轮 · 空白右键 → 新建节点 → 音频（空）',
    sel: { x: 390, y: 258 }, guard3a: { present: true, selected: true },
    delItem: { t: '删除 ⌫', rect: [470, 587, 192, 36], disabled: false, menuW: 200 },
    vanished: ['node_fnarb6091q'], exactlySelf: true, nBefore: 79, nAfter: 78 },
  { id: 'node_57qe0pz31m', by: 'a 轮 · 空白右键 → 新建节点 → 视频（空）',
    sel: { x: 300, y: 278 }, guard3a: { present: true, selected: true },
    delItem: { t: '删除 ⌫', rect: [444, 606, 192, 36], disabled: false, menuW: 200 },
    vanished: ['node_57qe0pz31m'], exactlySelf: true, nBefore: 78, nAfter: 77 },
  { id: 'node_a9cs17rk60', by: 'c 轮 · 左栏上传 wav（有资源）',
    sel: { x: 564, y: 284 }, guard3a: { present: true, selected: true },
    delItem: { t: '删除 ⌫', rect: [645, 613, 192, 36], disabled: false, menuW: 200 },
    vanished: ['node_a9cs17rk60'], exactlySelf: true, nBefore: 77, nAfter: 76 },
];
j.zoom0 = { aria: 'Zoom options, 52%', rect: [124, 672, 48, 28] };
j.zoomInput = { tag: 'INPUT', type: 'text', value: '52', rect: [124, 672, 48, 28] };
j.zoomTyped = '60';
j.zoom1 = { aria: 'Zoom options, 60%', rect: [124, 672, 48, 28] };
j.zoom2 = { aria: 'Zoom options, 60%', rect: [124, 672, 48, 28] };
j.zoomStable = true;
j.tool0 = { aria: '选择工具', pressed: 'false', tid: 'canvas-pointer-tool-toggle' };
j.tool1 = { aria: '选择工具', pressed: 'false', tid: 'canvas-pointer-tool-toggle' };
j.end = { nodes: '76', credits: 'Credits: 805 · 基础会员',
  zoom: { aria: 'Zoom options, 60%', rect: [124, 672, 48, 28] },
  tool: { aria: '选择工具', pressed: 'false', tid: 'canvas-pointer-tool-toggle' },
  sel: 0, edges: 0, leftovers: [] };

j.evidenceNote = {
  whyTwoRuns: '第一次 z 轮把证据误写进 _tmp-b113z.json（脚本从批次 113 复制时落盘名没跟着改）。批次 113 的证据已用 `git show HEAD:…` 原样恢复、未动索引；本文件是第一次 z 轮真实读数的补录。',
  secondRun: '改对落盘名后重跑了一次，三条目标此时已删除，故 deletions 全为 {skipped:true}；那次运行的终态与本文件 end 一致。',
  selfCheck: '三个消失集合各自都只有 SELF；终态 76 nodes / 0 selected / 0 edges / 60% / 选择工具 / 805。',
};

writeFileSync(P, JSON.stringify(j, null, 1) + '\n');
const chk = JSON.parse(readFileSync(P, 'utf8'));
process.stdout.write(`✅ 已补录。deletions ${chk.deletions.length} 条，全部 exactlySelf=${chk.deletions.every((d) => d.exactlySelf)}\n`);
process.stdout.write(`   终态 ${JSON.stringify(chk.end)}\n`);
