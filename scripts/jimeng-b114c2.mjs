// 批次 114 · c2 轮（**只读**，不点任何东西）。
//
// c 轮卡在：`node_a9cs17rk60`（自身有资源的音频节点）上**没有 `generation-prompt-editor`**
// ⇒ 打不了 `@`，也就读不到二级子菜单 ⇒ **「宿主自身是否额外被排除」判不了**。
//
// 这一轮把这个理由**钉成读数**（不是推理）：
//   ① 有资源的节点：到底有没有 `node-toolbar` / 生成面板 / 任何工具条？
//   ② 空节点（对照）：有。
//   ⇒ 两种状态**互斥** ⇒ 产品里造不出「自身有资源 且 能打开生成面板」的宿主
//   ⇒ 「宿主自身是否额外被排除」在产品里**不可判定**，按三态记「无法验证」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const WITH_RES = 'node_a9cs17rk60';   // 本批自建：上传 wav 得到的**有资源**音频节点
const EMPTY_A = 'node_fnarb6091q';     // 本批自建：空音频节点
const EMPTY_V = 'node_57qe0pz31m';     // 本批自建：空视频节点

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c2' };
const save = () => writeFileSync(new URL('./_tmp-b114c2.json', import.meta.url), JSON.stringify(out, null, 1));

// 面板/工具条存在性：**不依赖选中态**，直接问「这个节点的 DOM 里有没有」
const probe = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const rect = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const inNode = (sel) => Array.from(n.querySelectorAll(sel)).map((e) => ({ sel, rect: rect(e) }));
  const anyInDoc = (sel) => document.querySelectorAll(sel).length;
  return {
    id: i,
    selected: n.classList.contains('selected'),
    title: ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').replace(/\s+/g, ' ').trim(),
    cls: (n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/)?.[1] || null,
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110),
    // 节点**内部**有没有面板/工具条
    inNodeToolbars: inNode('[data-testid="node-toolbar"]'),
    inNodeEditor: inNode('[data-testid="generation-prompt-editor"]'),
    inNodeFeatureHost: inNode('[data-testid="node-toolbar-feature-host"]'),
    inNodeCtxToolbar: inNode('[data-testid="selection-context-toolbar"]'),
    allTids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    // 整页有几套（别的节点的也算）
    docCounts: {
      nodeToolbar: anyInDoc('[data-testid="node-toolbar"]'),
      featureHost: anyInDoc('[data-testid="node-toolbar-feature-host"]'),
      genPromptEditor: anyInDoc('[data-testid="generation-prompt-editor"]'),
      selectionCtx: anyInDoc('[data-testid="selection-context-toolbar"]'),
      audioGenerationForm: anyInDoc('form[data-testid="audio-generation-form"],[data-testid="audio-generation-form"]'),
    },
  };
}, id);

out.probes = {};
for (const [tag, id] of [['有资源音频', WITH_RES], ['空音频（对照）', EMPTY_A], ['空视频（对照）', EMPTY_V]]) {
  out.probes[tag] = await probe(id);
  log(`\n=== ${tag} ${id} ===`);
  log(JSON.stringify(out.probes[tag], null, 1));
  save();
}

// 追加：整页那两个 `node-toolbar` 里**逐字**是什么（面板在，但没有提示词框 —— 那它是什么面板？）
out.toolbars = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
  const r = e.getBoundingClientRect();
  return { rect: [r.x, r.y, r.width, r.height].map(Math.round),
    text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220),
    btns: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label')).filter(Boolean).slice(0, 20),
    hasGenPromptEditor: !!e.querySelector('[data-testid="generation-prompt-editor"]'),
    forms: Array.from(e.querySelectorAll('form')).map((f) => f.getAttribute('data-testid') || f.getAttribute('aria-label') || '(无名 form)'),
    inputs: Array.from(e.querySelectorAll('input,textarea,[contenteditable]')).map((f) => f.getAttribute('data-testid') || f.getAttribute('aria-label') || f.tagName) };
}));
log('\n=== 整页 node-toolbar 逐字 ===');
out.toolbars.forEach((t, i) => log(`  #${i} ${JSON.stringify(t, null, 1)}`));
save();

out.conclusion = {
  withRes_hasToolbar: out.probes['有资源音频'].inNodeToolbars.length > 0,
  empty_hasToolbar: out.probes['空音频（对照）'].inNodeToolbars.length > 0,
  withRes_hasGenPromptEditor: out.probes['有资源音频'].inNodeEditor.length > 0,
  toolbarsWithEditor: out.toolbars.filter((t) => t.hasGenPromptEditor).length,
  toolbarsTotal: out.toolbars.length,
};
log('\n=== 结论输入 ===', JSON.stringify(out.conclusion, null, 1));
save();
log('\nDONE c2');
process.exit(0);
