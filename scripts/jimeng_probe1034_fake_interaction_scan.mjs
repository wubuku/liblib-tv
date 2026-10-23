/**
 * 1032-④ 扫描器：把「假交互」候选扫成**事实**（本文件**不下判决**）。
 *
 * 为什么要分成「扫描」与「判决」两个文件：
 *   - 扫描（.mjs）用 TypeScript 编译器 API 看 AST ⇒ 它只报**静态可见的事实**；
 *   - 判决（.py）拿「承诺清单 + 已解释清单」这两份**真源**去比这些事实。
 * ⇒⇒ 事实与判决分开 ⇒ 门能被**注入式反证**（改事实 ⇒ 必须翻红）。
 *
 * ⚠️ 纪律：
 *   - 产物里不许出现随机量（时间戳 / 临时目录 / 耗时）；
 *   - 「静态看不出来」必须记成 UNKNOWN，不许记成 False；
 *   - 扫描范围要写出来（本扫描器只扫 src/components/jimeng/**）。
 */
import ts from '/Users/yangjiefeng/Documents/wubuku/liblib-tv/node_modules/typescript/lib/typescript.js';
import fs from 'fs';
import path from 'path';

const ROOT = '/Users/yangjiefeng/Documents/wubuku/liblib-tv';
const SRC = path.join(ROOT, 'src/components/jimeng');
/**
 * ⭐⭐⭐⭐⭐ Batch 1032-④-B：**事实范围补齐** —— store 也要被扫。
 *
 * 此前 `facts` 只覆盖 `src/components/jimeng` 下的 tsx 文件 ⇒ ⇒ 而登记册里
 * C02 的「目标形态」谓词指向 **`src/store/jimengStore.ts`**（新建项目要
 * 有真的 `createProject` 动作）⇒ ⇒ 那个文件**根本没有 facts**
 * ⇒ ⇒ 谓词恒为「不成立」⇒ ⇒ **门读不出「这一条已经兑现了」**
 * ⇒ ⇒ 而「读不出」与「没测到」长得一模一样 —— 这是最贵的一种失败。
 *
 * ⚠️ store **只进 facts**（供谓词查询），**不进 R1/R2 判定**：
 *   · R1（死按钮）判的是 JSX 可点元素 ⇒ store 里没有 JSX；
 *   · R2（只弹一句）扫的是 JSX 属性上的 handler ⇒ 同理。
 * ⇒ ⇒ 所以「现状集合」（死按钮 + toast-only）**不受影响** ⇒
 *   P2/P3 的口径不变（登记册与现状仍然逐条对账）。
 */
const EXTRA_FACT_FILES = [
  path.join(ROOT, 'src/store/jimengStore.ts'),
];
const OUT = process.env.JIMENG_1034_SCAN_OUT
  || path.join(ROOT, 'docs/research/jimeng-canvas/inputs/fake-interaction-scan-1034.json');

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.tsx')) out.push(p);
  }
  return out;
}

const files = walk(SRC).sort();

/** 字面量文本（含模板字面量的静态片段，不含插值）。 */
function litText(node) {
  if (!node) return '';
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isTemplateExpression(node)) {
    let s = node.head.text;
    for (const sp of node.templateSpans) s += sp.literal.text;
    return s;
  }
  return '';
}

/** 「声称已经完成」的措辞 —— 判据是**用户看到的那句话**，不是变量名。 */
const CLAIM_RE = /(已(经)?(执行|保存|同步|丢弃|创建|完成|导出|下载|上传|删除|复制|发布|添加|导入|移除|切换|生成|截帧|新建|处理)|成功|完成|已开始)/;

/** toast 调用？—— `pushToast(...)` / `mockMsg(...)` / `FEEDBACK.xxx(...)`。 */
function isToastCall(expr) {
  if (!expr || !ts.isCallExpression(expr)) return false;
  const t = expr.expression.getText();
  return /(^|[^A-Za-z0-9_$.])pushToast$/.test(t)
    || /(^|[^A-Za-z0-9_$.])mockMsg$/.test(t)
    || /^FEEDBACK\.[A-Za-z0-9_]+$/.test(t);
}

/** 从 `jimengFeedback.ts` 抽出 `FEEDBACK.<名>` 的文案 ——
 *  ⇒⇒ 「声称完成」即使不写在调用点（写在文案表里）也能被认出来。 */
const FB_FILE = path.join(ROOT, 'src/components/jimeng/jimengFeedback.ts');
const feedbackText = new Map();
{
  const src = fs.readFileSync(FB_FILE, 'utf8');
  const sf = ts.createSourceFile(FB_FILE, src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const visit = (node) => {
    if (ts.isPropertyAssignment(node)) {
      const name = node.name.getText().replace(/^['"]|['"]$/g, '');
      const init = node.initializer;
      if (init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init))) {
        const body = init.body;
        const grab = (expr) => {
          if (!expr) return;
          if (ts.isCallExpression(expr) && expr.arguments.length) {
            feedbackText.set(name, litText(expr.arguments[0]));
          }
        };
        if (ts.isBlock(body)) {
          for (const st of body.statements) {
            if (ts.isReturnStatement(st)) grab(st.expression);
          }
        } else {
          grab(body);
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
}

/** 稳定键的序号计数器（定义必须在使用之前 —— 模块级代码顺序＝执行顺序）。 */
const labelOrdinals = new Map();

const EVENT_ATTRS = new Set([
  'onClick', 'onMouseDown', 'onMouseUp', 'onPointerDown', 'onPointerUp',
  'onKeyDown', 'onKeyUp', 'onDoubleClick', 'onSubmit', 'onTouchStart',
  'onContextMenu', 'onWheel', 'onDragStart',
]);

const facts = {};
const deadButtons = [];
const toastOnly = [];

for (const file of files) {
  const rel = path.relative(ROOT, file);
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const f = { tags: {}, identifiers: [], jsx_texts: [], string_literals: [], attrs: {}, calls: {} };
  const idents = new Set();

  const visit = (node, ancestors) => {
    const here = ancestors.concat([node]);
    if (ts.isIdentifier(node)) idents.add(node.text);
    if (ts.isJsxText(node)) {
      const t = node.text.trim();
      if (t) f.jsx_texts.push(t);
    }
    // ⚠️ **字符串字面量**（含模板字面量的静态片段）——
    //   读屏文案、aria-label、占位提示常写在表达式里 ⇒ 只收 JsxText 会漏掉它们。
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
      if (node.text) f.string_literals.push(node.text);
    } else if (ts.isTemplateExpression(node)) {
      let s = node.head.text;
      for (const sp of node.templateSpans) s += sp.literal.text;
      if (s.trim()) f.string_literals.push(s);
    }
    if (ts.isCallExpression(node)) {
      const callee = node.expression.getText();
      const args = node.arguments.map((a) => a.getText().slice(0, 160)).join(', ');
      if (!f.calls[callee]) f.calls[callee] = [];
      f.calls[callee].push(args);
    }
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = node.tagName.getText();
      f.tags[tag] = (f.tags[tag] || 0) + 1;
      const props = (node.attributes && node.attributes.properties) || [];
      for (const a of props) {
        if (a.kind !== ts.SyntaxKind.JsxAttribute) continue;
        const name = a.name.getText();
        const init = a.initializer;
        let v = '';
        if (init) {
          if (ts.isStringLiteral(init)) v = init.text;
          else if (ts.isJsxExpression(init) && init.expression) v = init.expression.getText().slice(0, 200);
        }
        if (!f.attrs[name]) f.attrs[name] = [];
        f.attrs[name].push(v);
      }
      if (tag === 'button' || tag === 'a') {
        const v = classifyClickable(node, here, sf, rel);
        if (v.verdict === 'DEAD_NO_HANDLER' || v.verdict === 'DEAD_EMPTY_INLINE') deadButtons.push(v);
      }
    }
    ts.forEachChild(node, (c) => visit(c, here));
  };
  visit(sf, []);
  f.identifiers = Array.from(idents).sort();
  f.string_literals = Array.from(new Set(f.string_literals)).sort();
  facts[rel] = f;
}

/** R1：可点元素的接线判定 —— 口径与 1032-① 同型（两个独立实现，门要比它们一致）。 */
function classifyClickable(node, here, sf, rel) {
  const tag = node.tagName.getText();
  let hasSpread = false, hasDisabled = false, typeAttr = '', emptyInline = false;
  const eventAttrs = [];
  const attrs = {};
  for (const a of node.attributes.properties) {
    if (ts.isJsxSpreadAttribute(a)) { hasSpread = true; continue; }
    const name = a.name.getText();
    const init = a.initializer;
    attrs[name] = !init ? '(bare)' : (init.getText().length > 90 ? init.getText().slice(0, 90) + '…' : init.getText());
    if (EVENT_ATTRS.has(name)) {
      eventAttrs.push(name);
      if (init && ts.isJsxExpression(init) && init.expression) {
        const ex = init.expression;
        if ((ts.isArrowFunction(ex) || ts.isFunctionExpression(ex))
            && ts.isBlock(ex.body) && ex.body.statements.length === 0) emptyInline = true;
      }
    }
    if (name === 'disabled') hasDisabled = true;
    if (name === 'type') {
      typeAttr = init && ts.isStringLiteral(init) ? init.text : (init ? 'expr' : '');
    }
  }
  let inForm = false, delegated = false, delegatedBy = '';
  for (const anc of here.slice(0, -1)) {
    const open = anc.openingElement;
    if (!open || !open.tagName) continue;
    const tag = open.tagName.getText();
    if (tag === 'form') inForm = true;
    if (!delegated && open.attributes && open.attributes.properties.some(
      (a) => !ts.isJsxSpreadAttribute(a) && a.name.getText() === 'onClick')) {
      delegated = true; delegatedBy = tag;
    }
  }
  const hasHref = Object.prototype.hasOwnProperty.call(attrs, 'href');
  let verdict;
  if (tag === 'a' && hasHref) verdict = 'WIRED_LINK';
  else if (hasSpread) verdict = 'UNKNOWN_SPREAD';
  else if (eventAttrs.length && emptyInline) verdict = 'DEAD_EMPTY_INLINE';
  else if (eventAttrs.length) verdict = 'WIRED';
  else if (delegated) verdict = 'WIRED_VIA_DELEGATION';
  else if (typeAttr === 'submit') verdict = 'FORM_SUBMIT';
  else if (inForm && typeAttr === '') verdict = 'FORM_SUBMIT_DEFAULT';
  else if (hasDisabled) verdict = 'DISABLED_NO_HANDLER';
  else verdict = 'DEAD_NO_HANDLER';
  const label = attrs['aria-label'] || attrs['data-testid'] || attrs['title'] || '';
  let ordinal = 0;
  if (tag === 'button') {
    const ok = rel + '|' + label;
    ordinal = labelOrdinals.get(ok) || 0;
    labelOrdinals.set(ok, ordinal + 1);
  }
  const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
  return {
    file: rel, line: line + 1, tag, verdict, label, disabled: hasDisabled,
    event_attrs: eventAttrs, delegated_by: delegatedBy, type: typeAttr,
    stable_key: rel + '#' + label + '#' + ordinal,
  };
}

/** R2：handler 的函数体**只有一句 toast** ⇒ 点了等于没点。
 *  ⚠️ 「只有一句」是硬条件：真动作后面跟一句反馈（`splitClip(...); pushToast(...)`）
 *    有两句 ⇒ 不算糊弄。
 *  ⚠️ 文案里「声称已经完成」的另算一族（claim），由判决层分开判。 */
function scanToastOnly(file) {
  const rel = path.relative(ROOT, file);
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const out = [];
  const ordinals = new Map();
  const visit = (node) => {
    if (ts.isJsxAttribute(node) && node.initializer) {
      const init = node.initializer;
      if (ts.isJsxExpression(init) && init.expression) {
        const fn = init.expression;
        if (ts.isArrowFunction(fn) || ts.isFunctionExpression(fn)) {
          const body = fn.body;
          let expr = null;
          if (ts.isBlock(body)) {
            if (body.statements.length === 1 && ts.isExpressionStatement(body.statements[0])) {
              expr = body.statements[0].expression;
            }
          } else {
            expr = body;
          }
          if (expr && isToastCall(expr)) {
            const msg = toastMessage(expr);
            const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
            const prop = node.name.getText();
            // 稳定键 = 文件 + 属性名 + 同文件同属性名的出现序号（行号是位置不是身份）
            const ok = rel + '|' + prop;
            const ord = ordinals.get(ok) || 0;
            ordinals.set(ok, ord + 1);
            out.push({
              file: rel, line: line + 1, prop,
              key: rel + '#' + prop + '#' + ord,
              message: msg, claim: CLAIM_RE.test(msg),
              callee: expr.expression.getText(),
            });
          }
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return out;
}

/** toast 调用里那句文案是什么（`FEEDBACK.foo()` 要回文案表里查）。 */
function toastMessage(expr) {
  if (!ts.isCallExpression(expr)) return '';
  for (const a of expr.arguments) {
    const direct = litText(a);
    if (direct) return direct;
    if (!ts.isCallExpression(a)) continue;
    const m = /^FEEDBACK\.([A-Za-z0-9_]+)$/.exec(a.expression.getText());
    if (m) {
      const w = feedbackText.get(m[1]);
      if (w) return w;
    }
    if (a.arguments.length) {
      const inner = litText(a.arguments[0]);
      if (inner) return inner;
    }
  }
  return '';
}

for (const file of files) {
  for (const t of scanToastOnly(file)) toastOnly.push(t);
}

/**
 * ⭐⭐⭐⭐⭐ Batch 1032-④-B：**补充事实文件**（store）。
 *
 * ⚠️ 这里**只**采 facts（标识符 / 字符串字面量 / 标签 / 调用），
 *   **不**跑 R1（死按钮）与 R2（只弹一句）⇒ ⇒ 「现状集合」的口径不变。
 * ⚠️ `.ts` 文件按 `ts.ScriptKind.TS` 解析（不是 TSX）⇒ 否则 store 里的
 *   JSX 无关内容会被误解析。
 */
for (const file of EXTRA_FACT_FILES) {
  if (!fs.existsSync(file)) continue;
  const rel = path.relative(ROOT, file);
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const f = { tags: {}, identifiers: [], jsx_texts: [], string_literals: [], attrs: {}, calls: {} };
  const idents = new Set();
  const visit = (node) => {
    if (ts.isIdentifier(node)) idents.add(node.text);
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
      if (node.text) f.string_literals.push(node.text);
    } else if (ts.isTemplateExpression(node)) {
      let s = node.head.text;
      for (const sp of node.templateSpans) s += sp.literal.text;
      if (s.trim()) f.string_literals.push(s);
    }
    if (ts.isCallExpression(node)) {
      const callee = node.expression.getText();
      const args = node.arguments.map((a) => a.getText().slice(0, 160)).join(', ');
      if (!f.calls[callee]) f.calls[callee] = [];
      f.calls[callee].push(args);
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  f.identifiers = Array.from(idents).sort();
  f.string_literals = Array.from(new Set(f.string_literals)).sort();
  facts[rel] = f;
}

let nButtons = 0;
for (const rel of Object.keys(facts)) {
  nButtons += (facts[rel].tags.button || 0) + (facts[rel].tags.a || 0);
}

const out = {
  generated_by: 'jimeng_probe1034_fake_interaction_scan.mjs',
  scan_scope: 'src/components/jimeng/**/*.tsx（R1/R2 判定）'
    + ' + src/store/jimengStore.ts（仅 facts）',
  n_files: files.length,
  n_fact_files: Object.keys(facts).length,
  n_buttons: nButtons,
  n_dead_buttons: deadButtons.length,
  n_toast_only: toastOnly.length,
  n_feedback_words: feedbackText.size,
  dead_buttons: deadButtons,
  toast_only_handlers: toastOnly,
  facts: facts,
};

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('files=%d buttons=%d dead=%d toast_only=%d feedback_words=%d',
  out.n_files, out.n_buttons, out.n_dead_buttons, out.n_toast_only, out.n_feedback_words);
for (const d of deadButtons) console.log('  DEAD %s:%d %s', d.file, d.line, d.label);
for (const t of toastOnly) console.log('  TOAST %s:%d %s | %s | claim=%s', t.file, t.line, t.prop, t.message, t.claim);
console.log('written', path.relative(ROOT, OUT));
