// batch 802 普查器 —— 「把 nodes 写进 canvas 对象」的**全部**写点
//
// ★ 为什么用 AST 而不是正则：794 的教训是「needle 打在错误的行——prettier 把实参
//   换到下一行，同行匹配一处都没命中」；799/800 又各踩一次「同名锚点抓到接口声明
//   而不是实现」。canvasStore.ts 有 4500+ 行、50 处 `nodes:`，正则必然出错。
//
// ★ 普查器**不做语义判断**，只采集：写点在哪、属于哪个动作、那个动作里有没有
//   fit 调用、有没有碰 parentId / 坐标系换算。结论由汇编器行锚定。
//
// 用法：node scan802.mjs [输出路径]
//
// ★ 第二个参数是 802 验收器的 S1 需要的：**重跑到别处**，而不是把入库的那份
//   原地覆写。原先只有固定路径 ⟹ 「入库的 vs 重跑的」其实读的是同一个文件，
//   交叉核对是**空的**（假绿）。
import ts from "typescript";
import fs from "node:fs";
import path from "node:path";

const ROOT = "/Users/yangjiefeng/Documents/wubuku/liblib-tv";
const SRC = path.join(ROOT, "src/store/canvasStore.ts");
const OUT = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(
      ROOT, "docs/research/liblib-canvas-batch802-2026-10-01/raw/scan802.json");

const text = fs.readFileSync(SRC, "utf8");
const sf = ts.createSourceFile(SRC, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);

const lineOf = (node) =>
  sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;

/**
 * 沿 parent 链找**所属动作**。
 *
 * ★ 第一版取「最近的 PropertyAssignment」⟹ 35 个写点全被吸到嵌套的
 *   `canvases: state.canvases.map(...)` 那个 PropertyAssignment 上，
 *   真正的动作名反而丢了。
 *   动作的特征是「initializer 是**函数**」——`foo: (...) => {`。
 */
function ownerOf(node) {
  let cur = node.parent;
  while (cur) {
    if (ts.isMethodDeclaration(cur) && cur.name) {
      return { name: cur.name.text, line: lineOf(cur) };
    }
    if (ts.isPropertyAssignment(cur)) {
      const init = cur.initializer;
      const isFn = init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init));
      const name = cur.name;
      if (isFn && name && (ts.isIdentifier(name) || ts.isStringLiteral(name))) {
        return { name: name.text, line: lineOf(cur) };
      }
    }
    cur = cur.parent;
  }
  return { name: "(模块顶层)", line: 0 };
}

const writePoints = [];   // 把 nodes 写进对象的每一处
const fitCalls = [];      // fitStoryboardGroupsToChildren 的每一次调用
const parentWrites = [];  // 明确写 parentId / 删 parentId 的地方
const absHelpers = [];    // 坐标系换算相关的调用

function visit(node) {
  // ① 写点：属性赋值 `nodes: <表达式>`
  if (ts.isPropertyAssignment(node)
      && ((ts.isIdentifier(node.name) && node.name.text === "nodes")
          || (ts.isStringLiteral(node.name) && node.name.text === "nodes"))) {
    const owner = ownerOf(node);
    const init = node.initializer;
    const isTypeDecl = init && (ts.isArrayLiteralExpression(init)
      && init.elements.length === 0 && /Node\[\]/.test(init.getText(sf) + " ")
      || (ts.isPropertyAccessExpression(init)
          && /getActiveCanvas\(\)\?\.nodes/.test(init.getText(sf))));
    writePoints.push({
      line: lineOf(node),
      owner: owner.name,
      ownerLine: owner.line,
      snippet: node.getText(sf).replace(/\s+/g, " ").slice(0, 120),
      target: init ? init.getText(sf).replace(/\s+/g, " ").slice(0, 80) : "",
      isTypeDeclOrReadback: Boolean(isTypeDecl),
    });
  }
  // ② fit 调用
  if (ts.isCallExpression(node)) {
    const callee = node.expression;
    if (ts.isIdentifier(callee) && callee.text === "fitStoryboardGroupsToChildren") {
      const owner = ownerOf(node);
      fitCalls.push({ line: lineOf(node), owner: owner.name, ownerLine: owner.line });
    }
    if (ts.isIdentifier(callee)
        && ["withoutParent", "getAbsoluteNodePosition", "withDescendantIds",
            "withoutStoredNodeSelection", "cloneSemanticNode"]
            .includes(callee.text)) {
      const owner = ownerOf(node);
      absHelpers.push({ fn: callee.text, line: lineOf(node), owner: owner.name });
    }
  }
  // ③ 显式写/删 parentId
  if (ts.isPropertyAssignment(node)
      && ts.isIdentifier(node.name) && node.name.text === "parentId") {
    parentWrites.push({ line: lineOf(node), owner: ownerOf(node).name,
                        op: "写" });
  }
  if (ts.isDeleteExpression(node)
      && node.expression && ts.isPropertyAccessExpression(node.expression)
      && node.expression.name.text === "parentId") {
    parentWrites.push({ line: lineOf(node), owner: ownerOf(node).name,
                        op: "删" });
  }
  ts.forEachChild(node, visit);
}
visit(sf);

// ── 按动作聚合：每个动作有没有 fit、有没有碰坐标系
const actions = new Map();
for (const w of writePoints) {
  if (w.isTypeDeclOrReadback || w.owner === "(模块顶层)") continue;
  if (!actions.has(w.owner)) {
    actions.set(w.owner, { name: w.owner, ownerLine: w.ownerLine, writes: [],
                           fitCalls: 0, parentWrites: 0, absHelpers: [] });
  }
  actions.get(w.owner).writes.push({ line: w.line, target: w.target });
}
for (const f of fitCalls) {
  if (!actions.has(f.owner)) continue;
  actions.get(f.owner).fitCalls += 1;
}
for (const p of parentWrites) {
  if (!actions.has(p.owner)) continue;
  actions.get(p.owner).parentWrites += 1;
}
for (const h of absHelpers) {
  if (!actions.has(h.owner)) continue;
  actions.get(h.owner).absHelpers.push(h.fn);
}

const list = Array.from(actions.values()).sort((a, b) => a.ownerLine - b.ownerLine);
for (const a of list) {
  a.writes.sort((x, y) => x.line - y.line);
  // ★ 这三个数全部由机器数出，不手写
  a.touchesGeometry = a.writes.length > 0;
  a.goesThroughFit = a.fitCalls > 0;
  a.risk = (a.writes.length > 0 && a.fitCalls === 0
            && (a.parentWrites > 0 || a.absHelpers.length > 0))
    ? "高：改了 nodes 但不经 fit，且碰了 parentId / 坐标系换算"
    : (a.writes.length > 0 && a.fitCalls === 0 ? "中：改了 nodes 但不经 fit" : "低");
}

const out = {
  batch: 802,
  source: "src/store/canvasStore.ts",
  totalWritePoints: writePoints.filter((w) => !w.isTypeDeclOrReadback).length,
  totalFitCalls: fitCalls.length,
  actions: list,
  fitCallSites: fitCalls,
  parentWriteSites: parentWrites,
};
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

// ── 人读表（行首不是裸数字，免得被 pre-commit 的批次号解析器误认）
const pad = (s, n) => String(s).padEnd(n);
console.log("写点合计 %d ｜ fit 调用合计 %d ｜ 动作数 %d",
  out.totalWritePoints, out.totalFitCalls, list.length);
console.log(pad("动作", 26) + pad("写点", 6) + pad("fit", 5)
  + pad("parent", 8) + "风险");
for (const a of list) {
  console.log(pad(a.name, 26) + pad(a.writes.length, 6) + pad(a.fitCalls, 5)
    + pad(a.parentWrites, 8) + a.risk);
}
console.log("wrote " + OUT);
