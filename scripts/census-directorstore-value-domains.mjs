// census-directorstore-value-domains：普查 directorStore 每条**叶路径**的写入点，
// 按「写入点上有没有取整」分类。
//
// 用法：
//   node scripts/census-directorstore-value-domains.mjs            普查 store 叶路径
//   node scripts/census-directorstore-value-domains.mjs --geometry 普查派生布局表达式
//
// `--geometry` 普查 `src/components/director/**` 里所有几何类 `style` 属性，
// 并**把标识符追到它的定义**（690/688 的纪律：690 那条 `timelineWidth` 就藏在
// const 后面，只扫 JSX 会漏掉整个像素族）。
import ts from "typescript";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..");
const SRC = path.resolve(HERE, "../src/store/directorStore.ts");
const OUT = process.argv.includes("--json")
  ? null
  : "/tmp/census-directorstore-value-domains.json";

// ---------------------------------------------------------------- geometry
if (process.argv.includes("--geometry")) {
  const GEO = /^(width|height|left|right|top|bottom|transform|minWidth|maxWidth|minHeight|maxHeight|flexBasis|gap|rowGap|columnGap|padding|paddingTop|paddingLeft|marginTop|marginLeft)$/;
  const rows = [];
  const dir = path.join(REPO, "src/components/director");
  for (const f of fs.readdirSync(dir).filter((x) => /\.tsx?$/.test(x)).sort()) {
    const text = fs.readFileSync(path.join(dir, f), "utf8");
    const sf = ts.createSourceFile(f, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const decls = new Map();
    (function c(nd) {
      if (ts.isVariableDeclaration(nd) && ts.isIdentifier(nd.name) && nd.initializer) {
        decls.set(nd.name.text, {
          text: nd.initializer.getText(sf).replace(/\s+/g, " "),
          line: sf.getLineAndCharacterOfPosition(nd.initializer.getStart(sf)).line + 1,
        });
      }
      ts.forEachChild(nd, c);
    })(sf);
    (function w(nd) {
      if (ts.isJsxAttribute(nd) && nd.name.text === "style" && nd.initializer &&
          ts.isJsxExpression(nd.initializer) && nd.initializer.expression &&
          ts.isObjectLiteralExpression(nd.initializer.expression)) {
        for (const p of nd.initializer.expression.properties) {
          if (!ts.isPropertyAssignment(p)) continue;
          const key = ts.isIdentifier(p.name) ? p.name.text
            : ts.isStringLiteral(p.name) ? p.name.text : null;
          if (!key || !GEO.test(key)) continue;
          const line = sf.getLineAndCharacterOfPosition(p.getStart(sf)).line + 1;
          const inline = p.initializer.getText(sf).replace(/\s+/g, " ");
          let via = null, defLine = null;
          if (ts.isIdentifier(p.initializer)) {
            const d = decls.get(p.initializer.text);
            if (d) { via = d.text; defLine = d.line; }
          } else {
            via = inline;
          }
          rows.push({ file: f, line, key, inline, derived: via, defLine });
        }
      }
      ts.forEachChild(nd, w);
    })(sf);
  }
  const isLiteral = (s) => /^[-0-9.]+$/.test(s);
  const isBare = (s) => /^[A-Za-z_$][A-Za-z0-9_.$]*$/.test(s);
  const forEach = rows.map((r) => {
    const t = r.derived || "";
    // 算术判定要**剥掉反引号**：百分比族整族都是模板串
    // （`${ratio * 100}%`），不剥就等于把整族排除在外。
    const body = t.replace(/^`|`$/g, "");
    const arithmetic = /[+*/]/.test(body);
    const nonIntegerConst = (t.match(/[-+]?\d*\.\d+/g) || [])
      .filter((x) => !Number.isInteger(Number(x)));
    const rounded = /Math\.round|Math\.floor|Math\.ceil/.test(t);
    let family = "plain";
    if (arithmetic && (t.startsWith("`") || /%/.test(t))) family = "percent";
    else if (arithmetic) family = "pixel";
    else if (rounded) family = "rounded";
    else if (isLiteral(t) || isBare(t)) family = "plain";
    return { ...r, arithmetic, nonIntegerConst, rounded, family };
  });
  const derived = forEach.filter((r) => r.derived && r.arithmetic);
  const byFamily = {};
  for (const r of derived) (byFamily[r.family] = byFamily[r.family] || []).push(r);
  const out = {
    geometryPropsTotal: rows.length,
    derivedTotal: derived.length,
    pixelFamily: (byFamily.pixel || []).map((r) => ({
      file: r.file, line: r.line, key: r.key, expr: r.derived,
      nonIntegerConst: r.nonIntegerConst,
    })),
    percentFamily: (byFamily.percent || []).map((r) => ({
      file: r.file, line: r.line, key: r.key, expr: r.derived,
      nonIntegerConst: r.nonIntegerConst, rounded: r.rounded,
    })),
  };
  console.log(`几何 style 属性 ${out.geometryPropsTotal} 条 · 派生表达式 ${out.derivedTotal} 条`);
  console.log(`  像素族 ${out.pixelFamily.length} 条`);
  for (const r of out.pixelFamily)
    console.log(`    ${r.file}:${r.line} ${r.key} = ${r.expr}` +
      (r.nonIntegerConst.length ? `   ⟵ 非整数常数 ${r.nonIntegerConst.join(",")}` : ""));
  console.log(`  百分比族 ${out.percentFamily.length} 条`);
  for (const r of out.percentFamily)
    console.log(`    ${r.file}:${r.line} ${r.key} = ${r.expr}` +
      (r.rounded ? "  [显式取整]" : "") +
      (r.nonIntegerConst.length ? `  ⟵ 非整数常数 ${r.nonIntegerConst.join(",")}` : ""));
  process.exit(0);
}

const text = fs.readFileSync(SRC, "utf8");
const file = ts.createSourceFile(
  "directorStore.ts", text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS
);

const ROUND = new Set(["round", "floor", "ceil", "trunc"]);
const nameOf = (p) =>
  ts.isIdentifier(p.name) || ts.isStringLiteral(p.name) ||
  ts.isNumericLiteral(p.name)
    ? p.name.text
    : null;
const unwrap = (nd) => {
  let n = nd;
  for (;;) {
    if (ts.isParenthesizedExpression(n)) n = n.expression;
    else if (
      ts.isAsExpression(n) || ts.isNonNullExpression(n) ||
      ts.isSatisfiesExpression(n) || ts.isTypeAssertionExpression(n)
    ) n = n.expression;
    else break;
  }
  return n;
};
const roundingIn = (node) => {
  let hit = null;
  (function w(nd) {
    if (
      ts.isCallExpression(nd) && ts.isPropertyAccessExpression(nd.expression)
    ) {
      const e = nd.expression;
      if (
        ts.isIdentifier(e.expression) && e.expression.text === "Math" &&
        ROUND.has(e.name.text)
      ) hit = e.name.text;
    }
    if (ts.isIdentifier(nd) && ROUND.has(nd.text)) hit = hit || nd.text;
    ts.forEachChild(nd, w);
  })(node);
  return hit;
};

// 定位 create<DirectorState>((set, get) => ({ ... }))
let implObj = null;
(function w(nd) {
  if (implObj) return;
  if (
    ts.isCallExpression(nd) &&
    ((ts.isPropertyAccessExpression(nd.expression) &&
      nd.expression.name.text === "create") ||
      (ts.isIdentifier(nd.expression) && nd.expression.text === "create"))
  ) {
    for (const a of nd.arguments) {
      const u = unwrap(a);
      if (!ts.isArrowFunction(u) && !ts.isFunctionExpression(u)) continue;
      const b = unwrap(u.body);
      if (ts.isObjectLiteralExpression(b)) { implObj = b; return; }
      if (ts.isBlock(u.body)) {
        (function wb(x) {
          if (implObj) return;
          if (
            ts.isReturnStatement(x) && x.expression &&
            ts.isObjectLiteralExpression(unwrap(x.expression))
          ) { implObj = unwrap(x.expression); return; }
          ts.forEachChild(x, wb);
        })(u.body);
      }
    }
  }
  ts.forEachChild(nd, w);
})(file);
if (!implObj) {
  console.error("census: 没能定位 store 实现对象");
  process.exit(1);
}

const setterNames = new Set();
for (const p of implObj.properties) {
  if (!ts.isPropertyAssignment(p)) continue;
  const nm = nameOf(p);
  if (nm && /^set[A-Z]\w*$/.test(nm)) setterNames.add(nm);
}

const calls = [];
(function w(nd) {
  if (
    ts.isCallExpression(nd) && ts.isIdentifier(nd.expression) &&
    nd.expression.text === "set"
  ) {
    const findOwner = (n) => {
      if (ts.isPropertyAssignment(n)) {
        const nm = nameOf(n);
        if (nm && setterNames.has(nm)) return nm;
      }
      return ts.forEachChild(n, findOwner) || null;
    };
    calls.push({ node: nd, owner: findOwner(nd) });
    return; // 不钻进 set(...) 内部
  }
  ts.forEachChild(nd, w);
})(file);

const writes = [];
const expand = (obj, prefix, owner, depth) => {
  if (depth > 6) return;
  for (const p of obj.properties) {
    if (ts.isPropertyAssignment(p)) {
      const f = nameOf(p);
      if (!f) continue;
      const path = prefix ? `${prefix}.${f}` : f;
      const v = unwrap(p.initializer);
      if (
        ts.isObjectLiteralExpression(v) && v.properties.length &&
        !ts.isAsExpression(p.initializer)
      ) {
        expand(v, path, owner, depth + 1);
      } else {
        const txt = p.initializer.getText(file).replace(/\s+/g, " ");
        writes.push({
          owner, path,
          line: file.getLineAndCharacterOfPosition(p.getStart(file)).line + 1,
          round: roundingIn(p.initializer),
          value: txt.length > 150 ? `${txt.slice(0, 150)}…` : txt,
        });
      }
    } else if (ts.isShorthandPropertyAssignment(p)) {
      writes.push({
        owner, path: prefix ? `${prefix}.${p.name.text}` : p.name.text,
        line: file.getLineAndCharacterOfPosition(p.getStart(file)).line + 1,
        round: null, value: p.name.text,
      });
    }
  }
};
for (const c of calls) {
  for (const a of c.node.arguments) {
    const u = unwrap(a);
    const collect = (expr) => {
      const e = unwrap(expr);
      if (ts.isObjectLiteralExpression(e)) expand(e, "", c.owner, 0);
    };
    if (ts.isObjectLiteralExpression(u)) collect(u);
    else if (ts.isArrowFunction(u) || ts.isFunctionExpression(u)) {
      if (!ts.isBlock(u.body)) collect(u.body);
      else (function wb(x) {
        if (ts.isReturnStatement(x) && x.expression) collect(x.expression);
        ts.forEachChild(x, wb);
      })(u.body);
    }
  }
}

const byPath = new Map();
for (const w of writes) {
  if (!byPath.has(w.path)) byPath.set(w.path, []);
  byPath.get(w.path).push(w);
}
const paths = [];
for (const [p, ws] of byPath) {
  if (p.startsWith("_") || p === "length") continue;
  const rounded = ws.filter((w) => w.round);
  paths.push({
    path: p,
    writers: [...new Set(ws.map((w) => w.owner))],
    writeCount: ws.length,
    allRounded: rounded.length === ws.length,
    anyRounded: rounded.length > 0,
    sites: ws.map((w) => ({
      owner: w.owner, line: w.line, round: w.round, value: w.value,
    })),
  });
}
paths.sort((a, b) => a.path.localeCompare(b.path));

const out = {
  source: path.relative(path.resolve(HERE, ".."), SRC),
  setters: [...setterNames].sort(),
  setCalls: calls.length,
  writeSites: writes.length,
  pathsTotal: paths.length,
  allRounded: paths.filter((p) => p.allRounded).map((p) => p.path),
  someRounded: paths.filter((p) => p.anyRounded && !p.allRounded).map((p) => p.path),
  noneRounded: paths.filter((p) => !p.anyRounded).map((p) => p.path),
  detail: paths,
};
if (OUT) fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(`setter 成员 ${out.setters.length} · set() 调用 ${out.setCalls}` +
  ` · 写入点 ${out.writeSites} · 叶路径 ${out.pathsTotal}`);
console.log(`全写入点都取整 ${out.allRounded.length} 条: ${out.allRounded.join(" ") || "—"}`);
console.log(`部分写入点取整 ${out.someRounded.length} 条: ${out.someRounded.join(" ") || "—"}`);
console.log(`无任何写入点取整 ${out.noneRounded.length} 条`);
if (OUT) console.log(`写入 ${OUT}`);
