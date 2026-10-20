/**
 * 1032-① 静态探针：把「即梦克隆版」里每一个 <button> 的**事件接线状态**扫出来。
 *
 * ⭐⭐⭐⭐⭐ 这条探针的由来是 1032 的一次「反省」：
 *   三个只读审计者把 44 个组件、15171 行里的用户可感知元素分类过一遍，
 *   结论是「DEAD_WIRE（按钮压根没接事件）」「FAKE_SUCCESS（弹一句『已执行』但什么都没做）」
 *   「CONST_AS_STATE（写死的读数冒充状态）」占了将近一半。
 *   而其中 **DEAD_WIRE 是完全可机检的** —— 一个 <button> 若既没有事件属性、
 *   也不是 form 的 submit、也不带 spread（spread 会让静态不可判），
 *   那它在 DOM 里就是个**点不动的壳**。
 *
 * ⚠️⚠️⚠️ **它只覆盖「压根没接线」这一类。**
 *   「弹一句『已执行』但什么都没做」（FAKE_SUCCESS）、
 *   「写了读数但那个读数是常量」（CONST_AS_STATE）、
 *   「整个功能不存在」（如 <ReactFlow> 没有 onConnect ⇒ 连不出边）
 *   —— 这三类**静态不可判**，必须靠运行时探针。
 *   ⇒ **这份清单不是「糊弄清单」，是「糊弄清单的静态那部分」。**
 *
 * ⚠️ 纪律（照 REA 的）：
 *   - 只报**静态可见的事实**，不推断运行行为；
 *   - 「静态看不出来」必须显式记成 UNKNOWN，**不许记成 False**；
 *   - 产物里不许出现随机量（行号稳定、文件名稳定）；
 *   - 扫描范围要**写出来**（本探针只扫 src/components/jimeng/**，不扫别处）。
 */
import ts from '/Users/yangjiefeng/Documents/wubuku/liblib-tv/node_modules/typescript/lib/typescript.js';
import fs from 'fs';
import path from 'path';
import { writeFileSync } from 'fs';

const ROOT = '/Users/yangjiefeng/Documents/wubuku/liblib-tv';
const SRC = path.join(ROOT, 'src/components/jimeng');
// ⭐⭐ 产物放在 `inputs/` 子目录里：**1015 的通道 A 扫 `docs/research/jimeng-canvas/*.json`
//   （非递归）** ⇒ 「门的输入」若留在根目录，会被当成**无人认领的 golden** ⇒ P2 转红。
//   （同一手法 1031-③ 已在契约上用过：契约移到 `contracts/` 子目录。）
const OUT = process.env.JIMENG_WIRING_OUT
  || path.join(ROOT, 'docs/research/jimeng-canvas/inputs/interaction-wiring-1032.json');

const EVENT_ATTRS = new Set([
  'onClick', 'onMouseDown', 'onMouseUp', 'onPointerDown', 'onPointerUp',
  'onKeyDown', 'onKeyUp', 'onDoubleClick', 'onSubmit', 'onTouchStart',
  'onContextMenu', 'onWheel', 'onDragStart',
]);

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.tsx')) out.push(p);
  }
  return out;
}

const files = walk(SRC).sort();
const rows = [];
// ⭐⭐⭐⭐⭐ Batch 1032-②b-0: **稳定键的序号计数器** ——
//   key = `文件\0可访问名` ⇒ 跨文件天然不混；值 = 该名字在本文件里**按源码顺序**
//   第几次出现（对**全部**按钮计数，不只是死按钮）⇒ ⇒ 保证键在文件内唯一。
const labelOrdinals = new Map();

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

  // ⭐⭐⭐⭐⭐ **祖先事件委托**：React 的 onClick 会冒泡到祖先，
  //   所以一个自身没有 onClick 的 <button> 仍然可能是**可点的**
  //   （祖先容器带 onClick）。第一版没查这层 ⇒ **假阴性**：
  //   会把「真能点」判成「死按钮」。
  //   ⇒ 判据必须沿**祖先链**找带 onClick 的 JSX 元素。
  const visit = (node, ancestors) => {
    const here = ancestors.concat([node]);
    if (ts.isJsxElement(node)) {
      const open = node.openingElement;
      const tag = open.tagName.getText(sf);
      if (tag === 'button') {
        const attrs = {};
        let hasSpread = false;
        let hasDisabled = false;
        let typeAttr = '';
        let eventAttrs = [];
        for (const a of open.attributes.properties) {
          if (ts.isJsxSpreadAttribute(a)) { hasSpread = true; continue; }
          const name = a.name.getText(sf);
          if (EVENT_ATTRS.has(name)) eventAttrs.push(name);
          if (name === 'disabled') hasDisabled = true;
          if (name === 'type') {
            const v = a.initializer;
            typeAttr = v && ts.isStringLiteral(v) ? v.text : (v ? 'expr' : '');
          }
          const init = a.initializer;
          if (init) {
            const txt = init.getText(sf);
            attrs[name] = txt.length > 90 ? txt.slice(0, 90) + '…' : txt;
          } else {
            attrs[name] = '(bare)';
          }
        }
        // 内联空体：onClick={() => {}} / onClick={() => {/*…*/}}
        let emptyInline = false;
        for (const a of open.attributes.properties) {
          if (ts.isJsxSpreadAttribute(a)) continue;
          const name = a.name.getText(sf);
          if (!EVENT_ATTRS.has(name)) continue;
          const init = a.initializer;
          if (!init || !ts.isJsxExpression(init) || !init.expression) continue;
          const ex = init.expression;
          if ((ts.isArrowFunction(ex) || ts.isFunctionExpression(ex))
              && ts.isBlock(ex.body) && ex.body.statements.length === 0) {
            emptyInline = true;
          }
        }
        // 用来识别的稳定标签
        const aria = attrs['aria-label'] || '';
        const tid = attrs['data-testid'] || '';
        const title = attrs['title'] || '';
        // 祖先链上有没有带 onClick 的 JSX 元素？（表单的 onSubmit 不算 click 委托）
        // ⭐ 另一种**假阴性**：<button> 不写 type 时，HTML 默认 type="submit"；
        //   若它在某个 <form> 祖先里，点它会**提交表单** ⇒ 它是活的。
        let inForm = false;
        for (const anc of here.slice(0, -1)) {
          const aopen = anc.openingElement;
          if (aopen && aopen.tagName && aopen.tagName.getText(sf) === 'form') { inForm = true; break; }
        }
        let delegated = false;
        let delegatedBy = '';
        for (const anc of here.slice(0, -1)) {
          const aopen = anc.openingElement;
          if (!aopen || !aopen.attributes) continue;
          const hasClick = aopen.attributes.properties.some(
            (a) => !ts.isJsxSpreadAttribute(a) && a.name.getText(sf) === 'onClick');
          if (hasClick) { delegated = true; delegatedBy = aopen.tagName.getText(sf); break; }
        }
        let verdict;
        if (hasSpread) verdict = 'UNKNOWN_SPREAD';
        else if (eventAttrs.length && emptyInline) verdict = 'DEAD_EMPTY_INLINE';
        else if (eventAttrs.length) verdict = 'WIRED';
        else if (delegated) verdict = 'WIRED_VIA_DELEGATION';
        else if (typeAttr === 'submit') verdict = 'FORM_SUBMIT';
        else if (inForm && typeAttr === '') verdict = 'FORM_SUBMIT_DEFAULT';
        else if (hasDisabled) verdict = 'DISABLED_NO_HANDLER';
        else verdict = 'DEAD_NO_HANDLER';
        const { line } = sf.getLineAndCharacterOfPosition(node.pos);
        // ⭐⭐⭐⭐⭐ Batch 1032-②b-0: **稳定键** ——
        //   `line` 是**位置**，不是**身份**（1021/1030 已经为这件事栽过一次：
        //   在判据上方插一行代码，那个判据就「消失」了）。
        //   ⇒ 门与白名单若都按行号索引 ⇒ ⇒ 改一行代码 ⇒ ⇒ 全部标注错位
        //   ⇒ ⇒ ⇒ 每一处都被当成「新增糊弄」⇒ ⇒ ⇒ 修按钮的过程本身会一直误报。
        //   ⇒ 稳定键 = `文件#可访问名#同文件同名的出现序号`（序号按**源码顺序**，
        //   ⇒ 对**全部**按钮计数 ⇒ ⇒ 这样它在「同一个文件里」唯一）。
        const label = aria || tid || title || '';
        const ordinalKey = path.relative(ROOT, file) + '\u0000' + label;
        const ordinal = (labelOrdinals.get(ordinalKey) || 0);
        labelOrdinals.set(ordinalKey, ordinal + 1);
        rows.push({
          file: path.relative(ROOT, file),
          line: line + 1,
          verdict,
          event_attrs: eventAttrs,
          delegated_by: delegatedBy,
          type: typeAttr,
          disabled: hasDisabled,
          label,
          ordinal,
          stable_key: path.relative(ROOT, file) + '#' + label + '#' + ordinal,
        });
      }
    }
    ts.forEachChild(node, (c) => visit(c, here));
  };
  visit(sf, []);
}

rows.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line);

const counts = {};
for (const r of rows) counts[r.verdict] = (counts[r.verdict] || 0) + 1;

const out = {
  generated_by: 'jimeng_probe1032_interaction_wiring.mjs',
  scan_scope: 'src/components/jimeng/**/*.tsx',
  n_files: files.length,
  n_buttons: rows.length,
  counts,
  // ⚠️ 「dead」只指**没有事件接线**，不代表「这个功能在源站也不存在」
  //    （源站有没有这个功能，要用契约/取证对账，那是另一条判据的事）。
  dead_buttons: rows.filter(r => r.verdict === 'DEAD_NO_HANDLER' || r.verdict === 'DEAD_EMPTY_INLINE'),
  unknown_spread: rows.filter(r => r.verdict === 'UNKNOWN_SPREAD'),
  buttons: rows,
};
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('扫描文件 %d，<button> 共 %d 个', out.n_files, out.n_buttons);
console.log('分类:', JSON.stringify(counts));
console.log('死接线（无事件属性 / 空体内联）:', out.dead_buttons.length);
console.log('UNKNOWN(spread):', out.unknown_spread.length);
console.log('已落', path.relative(ROOT, OUT));
