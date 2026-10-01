#!/usr/bin/env node
/**
 * 死状态普查（AST 版, Batch 352）: 统计某个 store 每个状态字段的**外部读取点**。
 *
 * 为什么改用 AST 而不是正则:
 * Batch 349 的 Python 版用正则解析, 先后暴露了 **5 类误报**, 每一类都让人
 * 差点把「活字段」当成死状态:
 *   1. 多行函数签名的**参数**被当成字段（jimengStore 的 applyTrim）;
 *   2. **解构**读取被漏掉（`const { groupNames } = useJimengStore.getState()`，
 *      而且 hook 真名是 useJimengStore, 文件名是 jimengStore,
 *      `\bjimengStore\b` 永远匹配不到）;
 *   3. 多行 action 的**首行** `foo: (` 长得像字段（canvasStore 的
 *      addNodeAtFlowCenter / selectElements / routeReactFlowChanges）;
 *   4. 多行**解构**里字段单独占一行, 该行没有 hook 名（canvasStore 的
 *      removedCanvases / historyByCanvas）;
 *   5. 用「第一个 `\n}`」切接口 body 太天真, 把**邻近的其它接口**也扫进来了
 *      （canvasStore 的 cohortId / attachedAssetIds / skippedAssetIds）。
 *
 * 「测量方法本身要先验证」—— 这次直接用 TypeScript 自己的 AST, 5 类误报一次性归零。
 *
 * 用法:
 *   node scripts/deadstate_census.mjs [store相对路径] [接口名]
 *   node scripts/deadstate_census.mjs                              # frameosStore/FrameosCanvasState
 *   node scripts/deadstate_census.mjs src/store/canvasStore.ts CanvasState
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const storeRel = process.argv[2] ?? "src/store/frameosStore.ts";
const ifaceName = process.argv[3] ?? inferIfaceName(storeRel);

function inferIfaceName(rel) {
  // frameosStore.ts -> FrameosCanvasState? 猜不出来, 交给调用方; 这里只做兜底
  const base = rel.split("/").pop().replace(".ts", "");
  return { frameosStore: "FrameosCanvasState", jimengStore: "JimengCanvasState",
           canvasStore: "CanvasState", uiStore: "UIState" }[base] ?? "";
}

function walk(dir, out = []) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    const st = statSync(p);
    if (st.isDirectory()) { if (e !== "node_modules" && e[0] !== ".") walk(p, out); }
    else if (/\.(ts|tsx)$/.test(e)) out.push(p);
  }
  return out;
}

/** 1) 从 store 文件里抽出接口的**数据字段**(排除函数类型的成员) */
function extractDataFields(absPath, iface) {
  const text = readFileSync(absPath, "utf8");
  const sf = ts.createSourceFile(absPath, text, ts.ScriptTarget.Latest, true);
  let decl = null;
  sf.forEachChild((n) => {
    if (ts.isInterfaceDeclaration(n) && n.name.text === iface) decl = n;
  });
  if (!decl) throw new Error(`找不到 interface ${iface} 于 ${absPath}`);

  const fields = [];
  for (const m of decl.members) {
    if (!ts.isPropertySignature(m) || !m.name) continue;
    // 排除 action: 带调用签名的成员（`() => void` / `(id: string) => string`）
    if (m.type && ts.isFunctionTypeNode(m.type)) continue;
    if (ts.isFunctionTypeNode(m.type)) continue;
    const name = m.name.getText(sf);
    fields.push(name);
  }
  return fields;
}

/** 2) 在其它源文件里找这个字段的读取点(两种真实读取形态) */
function findReads(files, field, storeBasename) {
  const prop = [];   // 层 A: 状态对象上的属性访问  s.field
  const destr = [];  // 层 B: 从 store 解构出来的绑定
  const storeKey = storeBasename.toLowerCase();

  for (const f of files) {
    if (f.endsWith(storeRel)) continue;
    const text = readFileSync(f, "utf8");
    const sf = ts.createSourceFile(f, text, ts.ScriptTarget.Latest, true);
    const rel = relative(ROOT, f);

    const visit = (node) => {
      // 层 A: propertyAccessExpression 里的属性名
      if (ts.isPropertyAccessExpression(node) && node.name.text === field) {
        prop.push(`${rel}:${sf.getLineAndCharacterOfPosition(node.getStart()).line + 1}`);
      }
      // 层 B: 解构绑定 —— 变量声明的 initializer 提到了 store
      if (ts.isVariableDeclaration(node) && node.initializer) {
        const initText = node.initializer.getText(sf).toLowerCase();
        const names = node.name;
        const bound = [];
        const collect = (id) => {
          if (ts.isIdentifier(id)) bound.push(id.text);
          else if (ts.isObjectBindingPattern(id) || ts.isArrayBindingPattern(id))
            for (const el of id.elements) if (ts.isBindingElement(el)) collect(el.name);
        };
        collect(names);
        if (bound.includes(field) && initText.includes(storeKey)) {
          destr.push(`${rel}:${sf.getLineAndCharacterOfPosition(node.getStart()).line + 1}`);
        }
      }
      ts.forEachChild(node, visit);
    };
    sf.forEachChild(visit);
  }
  return { prop, destr };
}

// ── 主流程 ──
const storeAbs = join(ROOT, storeRel);
const storeBase = storeRel.split("/").pop().replace(".ts", "");
const fields = extractDataFields(storeAbs, ifaceName);
console.log(`# ${storeRel} :: ${ifaceName} 状态数据字段: ${fields.length} 个\n`);

const files = walk(join(ROOT, "src"));
const rows = fields.map((name) => {
  const { prop, destr } = findReads(files, name, storeBase);
  return { name, a: prop.length, b: destr.length, prop, destr };
});
rows.sort((x, y) => (x.a + x.b) - (y.a + y.b));

console.log("| 字段 | A:属性访问 | B:解构 | 样例 |");
console.log("|---|---|---|---|");
for (const r of rows) {
  const sample = (r.prop[0] ?? r.destr[0] ?? "").replace(/\|/g, "\\|");
  const tag = r.a + r.b === 0 ? "**两层都 0**" : sample;
  console.log(`| \`${r.name}\` | ${r.a} | ${r.b} | ${tag} |`);
}

const dead = rows.filter((r) => r.a === 0 && r.b === 0).map((r) => r.name);
const onlyDestr = rows.filter((r) => r.a === 0 && r.b > 0).map((r) => r.name);

console.log("\n# 死状态候选(属性访问与解构两层都为 0):");
console.log(dead.length ? dead.join(", ") : "(无)");
if (onlyDestr.length) {
  console.log(`\n# 只被解构读取(层 A 为 0、层 B > 0 —— 活着, 别当死状态): ${onlyDestr.join(", ")}`);
}
