#!/usr/bin/env node
/**
 * 「只弹 toast 的处理器」普查（AST 版, Batch 357）
 *
 * 第三类交互谎言。前两类的形状:
 *   - 静默丢弃输入（batch 350）: 控件收下输入, 不绑定 onChange;
 *   - 假可点按钮（batch 344/355/356）: 控件能点, 但没有 handler。
 * 这一类是**最难发现的中间态**: 有 handler、点了有反应、屏幕上确实出了东西
 * （一条绿色 ✓「已xxx」toast），但**底层状态一点没变**。
 * 用户看到的是「操作成功」，重开面板/刷新页面才发现什么都没发生。
 *
 * 为什么用 AST 而不是正则:
 * batch 349 的正则版死状态普查暴露过 5 类误报（多行签名被当字段、解构读取
 * 漏掉、相邻接口被扫进来……），教训是「先验证测量方法本身」。这里同理。
 *
 * 本工具**不判定**「是否说谎」—— 它只把「哪些 handler 的函数体里只出现了
 * showToast」这件事如实列出来。判定必须逐个人工核实（见
 * docs/research/liblib-frameos-batch357-2026-10-01/README.md）。
 *
 * 用法:
 *   node scripts/toast_lie_census.mjs [扫描根目录 ...]
 *   node scripts/toast_lie_census.mjs                        # 默认 frameos 全部
 *   node scripts/toast_lie_census.mjs --json                 # 机器可读
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const argv = process.argv.slice(2);
const asJson = argv.includes("--json");
const roots = argv.filter((a) => !a.startsWith("--"));
const SCAN_ROOTS = roots.length
  ? roots.map((r) => resolve(ROOT, r))
  : [join(ROOT, "src/components/frameos"), join(ROOT, "src/app/frameos")];

/** 不算「有实质动作」的调用 —— 它们只负责副作用包装/事件收尾 */
const INCIDENTAL = new Set([
  "showToast",
  "stopPropagation",
  "preventDefault",
  "console",
  "log",
  "warn",
  "error",
  "alert",
  "confirm",
  "prompt",
  "requestAnimationFrame",
  "setTimeout",
  "setInterval",
  "clearTimeout",
  "clearInterval",
  "toast",
  "emitToast",
  "pushToast",
]);

const HANDLER_PROPS = new Set([
  "onClick",
  "onDoubleClick",
  "onChange",
  "onInput",
  "onKeyDown",
  "onKeyUp",
  "onPointerDown",
  "onPointerUp",
  "onMouseDown",
  "onMouseUp",
  "onSubmit",
  "onBlur",
  "onFocus",
]);

function walk(dir, out = []) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    const st = statSync(p);
    if (st.isDirectory()) {
      if (e !== "node_modules" && !e.startsWith(".")) walk(p, out);
    } else if (/\.tsx?$/.test(e)) out.push(p);
  }
  return out;
}

/** 递归收集函数体里**被调用的**标识符名（只看 call expression 的 callee 标识符） */
function calledNames(node, out = new Set()) {
  const visit = (n) => {
    if (ts.isCallExpression(n)) {
      const callee = n.expression;
      if (ts.isIdentifier(callee)) out.add(callee.text);
      else if (ts.isPropertyAccessExpression(callee)) {
        // obj.method() -> 记 method, 方便人工看
        out.add(callee.name.text);
      }
    }
    n.forEachChild(visit);
  };
  // 注意: 从 **node 自己** 起步, 不是 node.forEachChild。
  // 紧凑箭头函数 `() => showToast(...)` 的 body 是**表达式**而非块,
  // 从 forEachChild 起步会正好跳过顶层那个 CallExpression 自己 ——
  // 第一版就是这么把 FrameosGroupCanvas 的三个菜单项全漏掉的
  // (而 page.tsx 的 handler 都是块体 `{ ...; showToast(...) }`, 侥幸命中,
  //  让一个「扫不全」的工具看起来像是「没问题」)。
  visit(node);
  return out;
}

/** 剥掉包裹层 */
function unwrap(node) {
  let n = node;
  while (n) {
    if (
      ts.isParenthesizedExpression(n) ||
      ts.isAsExpression(n) ||
      ts.isSatisfiesExpression?.(n) ||
      ts.isNonNullExpression(n) ||
      ts.isTypeAssertionExpression?.(n) ||
      // JSX 属性 `onClick={...}` 的 initializer 外层是 JsxExpression（那一对花括号）,
      // 不是 ParenthesizedExpression —— 漏掉它, 全部 JSX handler 都会被判成「非函数」
      ts.isJsxExpression(n)
    ) {
      n = n.expression;
    } else break;
  }
  return n;
}

/** handler 的函数体 —— 箭头函数取 body, 函数表达式取 body */
function handlerBody(fn) {
  const f = unwrap(fn);
  if (f && (ts.isArrowFunction(f) || ts.isFunctionExpression(f))) return f.body;
  return null;
}

function lineOf(sf, node) {
  return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
}

const findings = [];
const scannedFiles = [];

for (const root of SCAN_ROOTS) {
  if (!statSync(root).isDirectory()) continue;
  for (const abs of walk(root)) {
    scannedFiles.push(relative(ROOT, abs));
    const text = readFileSync(abs, "utf8");
    const sf = ts.createSourceFile(abs, text, ts.ScriptTarget.Latest, true);
    const rel = relative(ROOT, abs);

    const visit = (node) => {
      // 形态一: JSX 属性 onClick={...}
      // 形态二: 对象字面量属性 onClick: ... —— 上下文菜单项全走这条
      //   (openContextMenu({ items: [{ label, onClick: () => ... }] }))。
      //   第一版只认 JSX, 结果 FrameosGroupCanvas 的三个菜单项一个都没扫到 ——
      //   这正是 batch 349 教训「先验证测量方法本身」的又一次复现。
      let propName = null;
      let init = null;
      if (ts.isJsxAttribute(node) && HANDLER_PROPS.has(node.name.text)) {
        propName = node.name.text;
        init = node.initializer;
      } else if (
        ts.isPropertyAssignment(node) &&
        node.name &&
        ts.isIdentifier(node.name) &&
        HANDLER_PROPS.has(node.name.text)
      ) {
        propName = node.name.text;
        init = node.initializer;
      } else if (
        // 形态三: window.addEventListener("keydown", handler)
        //   frameos 画布的全部快捷键（⌘Z 撤销 / ⌘S 保存 / ⌘C 复制…）都走这条,
        //   既是「批量连线」这类真实用户入口, 也是最容易在普查里整片漏掉的一类。
        ts.isCallExpression(node) &&
        ts.isPropertyAccessExpression(node.expression) &&
        node.expression.name.text === "addEventListener"
      ) {
        propName = `addEventListener(${node.arguments[0]?.getText(sf) ?? "?"})`;
        init = node.arguments[1];
      }
      if (propName) {
        let resolvedBody = null;
        let resolvedName = propName;
        if (init && ts.isIdentifier(init)) {
          const decl = findScopedFnDecl(sf, init.text, node);
          if (decl) {
            resolvedBody = handlerBody(decl);
            resolvedName = `${init.text} (${propName} prop)`;
          }
        } else if (init) {
          resolvedBody = handlerBody(init);
        }
        if (resolvedBody) {
          const calls = calledNames(resolvedBody);
          const mentionsToast =
            [...calls].some((c) => /toast/i.test(c)) ||
            resolvedBody.getText(sf).includes("frameos-toast");
          if (mentionsToast) {
            const substantive = [...calls].filter((c) => !INCIDENTAL.has(c));
            const sites = analyzeToastSites(resolvedBody, sf);
            findings.push({
              file: rel,
              line: lineOf(sf, node),
              prop: resolvedName,
              substantiveCalls: substantive,
              sites,
              isToastOnly: substantive.length === 0,
              bodyPreview: oneLine(resolvedBody.getText(sf)),
            });
          }
        }
      }
      node.forEachChild(visit);
    };
    sf.forEachChild(visit);
  }
}

/**
 * 按**作用域**解析标识符到函数定义。
 *
 * 不能「全文件按名字取第一个声明」—— page.tsx 里 `const handler` 出现了两次
 * (213 行 delete-edge / 223 行 keydown), 按名字取第一个会把 ⌘Z 撤销、⌘S 保存
 * 这些真实入口整段解析成另一个函数, 于是在普查里凭空消失。
 * 这里从**使用点**往上找最近的函数体, 在那个函数体里取同名且位置在前的声明。
 */
function findScopedFnDecl(sf, name, usage) {
  // 1) 沿使用点向上收集祖先里的函数体/块
  const scopes = [];
  let cur = usage.parent;
  while (cur) {
    if (
      ts.isFunctionDeclaration(cur) ||
      ts.isFunctionExpression(cur) ||
      ts.isArrowFunction(cur) ||
      ts.isBlock(cur) ||
      ts.isSourceFile(cur)
    ) {
      scopes.push(cur);
    }
    cur = cur.parent;
  }
  // 2) 由内到外, 在每个作用域里找同名声明; 取**位置在 usage 之前**的最近一个
  for (const scope of scopes) {
    let best = null;
    const visit = (n) => {
      if (
        ts.isVariableDeclaration(n) &&
        n.name &&
        ts.isIdentifier(n.name) &&
        n.name.text === name &&
        n.initializer &&
        n.getStart(sf) < usage.getStart(sf) &&
        (ts.isArrowFunction(unwrap(n.initializer)) ||
          ts.isFunctionExpression(unwrap(n.initializer)))
      ) {
        if (!best || n.getStart(sf) > best.getStart(sf)) best = n.initializer;
      } else if (ts.isFunctionDeclaration(n) && n.name?.text === name) {
        if (!best) best = n;
      }
      n.forEachChild(visit);
    };
    scope.forEachChild(visit);
    if (best) return best;
  }
  return null;
}

/**
 * 逐条 toast 判定 —— **这才是「谎报成功」的最小单位**。
 *
 * 一个大 handler 里可以有好几条 toast, 有的有真实动作、有的没有:
 * page.tsx 的 keydown handler 里, ⌘Z 调了 undo()、⌘S 什么都没调。
 * 只按 handler 整体判定会把前者算成「有实质动作」从而放过后者。
 *
 * 做法: 对每条 showToast, 上溯到**最近的块**(if 分支体 / 箭头函数体),
 * 只在这个窄范围内数其它调用。窄到足以区分同�� handler 里的不同分支,
 * 宽到足以容纳「这条 toast 配套的那几步操作」。
 */
function analyzeToastSites(body, sf) {
  const sites = [];
  const visit = (n) => {
    if (ts.isCallExpression(n) && /toast/i.test(n.expression.getText(sf))) {
      const first = n.arguments[0];
      const text =
        first && (ts.isStringLiteral(first) || ts.isNoSubstitutionTemplateLiteral(first))
          ? first.text
          : "<" + (first ? oneLine(first.getText(sf)).slice(0, 60) : "?") + ">";
      // 上溯到最近的块
      let scope = n.parent;
      while (
        scope &&
        !ts.isBlock(scope) &&
        !ts.isSourceFile(scope) &&
        !ts.isCaseClause(scope) &&
        !ts.isArrowFunction(scope)
      ) {
        scope = scope.parent;
      }
      // 「回调逃逸」: toast 常被抽成具名回调再调用 ——
      //   `const finish = () => showToast("已复制图片")` 外面才真正 writeText(url)。
      // 停在那个箭头函数上会把这种写法**构造性地**判成 TOAST-ONLY（page.tsx:486 就是）。
      // 所以: 若最近的作用域是某个变量声明的初始化箭头, 视作回调,
      // 合并**上一层块**里的调用一起作为「配套动作」。
      let widened = false;
      if (
        scope &&
        (ts.isArrowFunction(scope) || ts.isFunctionExpression(scope)) &&
        ts.isVariableDeclaration(scope.parent)
      ) {
        // `const finish = ...` 的父是 VariableDeclaration, 再上是 VariableDeclarationList
        // (即使只有一条声明 TS 也套一层), 再上才是所在块。
        let up = scope.parent;
        while (up && !ts.isBlock(up) && !ts.isSourceFile(up)) up = up.parent;
        if (up && ts.isBlock(up)) {
          scope = up;
          widened = true;
        }
      }
      const calls = scope ? calledNames(scope) : calledNames(n);
      const substantive = [...calls].filter((c) => !INCIDENTAL.has(c) && c !== "showToast");
      // 变体: showToast(msg, variant="info")。**谎报的判据是「只弹 toast 且声称成功」**,
      // 不是「只弹 toast」—— 一条 warning 说「暂不可用」是诚实的, 不是谎报。
      // 这个区分是 Batch 357 被 batch170 打回后补上的 (见 README「修法改过一次」)。
      const variantArg = n.arguments[1];
      const variant =
        variantArg && ts.isStringLiteral(variantArg) ? variantArg.text : "info";
      sites.push({
        line: scope ? lineOf(sf, scope) : lineOf(sf, n),
        text,
        variant,
        substantiveCalls: substantive,
        isToastOnly: substantive.length === 0,
        // 真正的谎报: 什么都没做, 却说「已成功」
        isSuccessClaim: substantive.length === 0 && variant === "success",
        widenedFromCallback: widened,
      });
    }
    n.forEachChild(visit);
  };
  visit(body);
  return sites;
}

function oneLine(s) {
  return s.replace(/\s+/g, " ").trim();
}

findings.sort((a, b) => (a.file === b.file ? a.line - b.line : a.file.localeCompare(b.file)));

// 基础设施排除: FrameosToast.tsx 里监听 "frameos-toast" 自定义事件的那条不是
// 用户手势, 它**就是** toast 通道本身 (别人 showToast 就是派发它)。
const INFRA = (f) => /FrameosToast\.tsx$/.test(f.file);
const realFindings = findings.filter((f) => !INFRA(f));

if (asJson) {
  console.log(
    JSON.stringify(
      {
        scanned: scannedFiles.length,
        infraExcluded: findings.length - realFindings.length,
        findings: realFindings,
      },
      null,
      2
    )
  );
} else {
  const allSites = realFindings.flatMap((f) => f.sites);
  const only = allSites.filter((s) => s.isToastOnly);
  const lies = allSites.filter((s) => s.isSuccessClaim);
  console.log(`扫描 ${scannedFiles.length} 个文件`);
  console.log(
    `  带 toast 的 handler: ${realFindings.length}` +
      `（另排除 toast 基础设施自身 ${findings.length - realFindings.length} 处）`
  );
  console.log(`  toast 语句总数: ${allSites.length}`);
  console.log(`  ├─ 周围没有任何实质调用: ${only.length}`);
  console.log(`  └─ 其中**声称成功**(= 谎报): ${lies.length}`);
  console.log("");
  for (const f of realFindings) {
    console.log(`${f.file}:${f.line}  [${f.prop}]`);
    for (const s of f.sites) {
      const tag = s.isSuccessClaim
        ? "LIE"
        : s.isToastOnly
        ? "toast-only"
        : "ok        ";
      console.log(
        `   ${tag} :${s.line}  [${s.variant}]  ` +
          JSON.stringify(s.text) +
          (s.substantiveCalls.length ? `  (${s.substantiveCalls.join(",")})` : "")
      );
    }
  }
}
