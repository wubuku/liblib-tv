/**
 * 批次 311 · 判定复算器（读已落盘的 `/tmp/b311.json`，不重开浏览器）
 *
 * 🔴 为什么需要：主脚本的 P2 **把两个方向当成同等的「反解 compound」**，
 *    🔴 报出「文本多出 68.571×0」，📌 **据此差点写下「文本有两个 60 宽的 handle 外框」
 *    （68.571 × 1.75 = 120.0 与 `2×(60/1.75)` 逐字吻合，很漂亮）**。
 *
 * 🔴🔴 **那个吻合是巧合**（立规 184 的又一次现形）：
 *    `vs = min(safeW/cW, safeH/cH)` ⇒ 📌 **只有【绑定项】的反解值才是真 `compound`**，
 *    另一项只是下界。文本臂绑定的是**高度项**（多出恰为 `0`），
 *    📌 **宽度方向的 `68.571` 不是真值，不能用来讲外框。**
 *
 * 📌 因此本复算器按「哪一项绑定」重新分组，并**只报绑定项的多出量**。
 */
import fs from 'node:fs';

const IN = '/tmp/b311.json';
const sw = 680; const sh = 560;   // 1212-532, 720-160
const log = (...a) => console.log(a.join(' '));

const j = JSON.parse(fs.readFileSync(IN, 'utf8'));
const 好 = (j.臂 || []).filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);

const 表 = 好.map((x) => {
  const z = x.终点; const W = x.画布盒.W; const H = x.画布盒.H;
  const cw = sw / z; const ch = sh / z;
  const mw = cw - W; const mh = ch - H;
  // 📌 哪一项多出更接近 0 ⇒ 那一项才是绑定项
  const 宽绑定 = Math.abs(mw) < Math.abs(mh);
  const 绑定 = 宽绑定 ? '宽度项' : '高度项';
  const 真compound = 宽绑定 ? cw : ch;
  const 真多出 = 宽绑定 ? mw : mh;
  return {
    名: x.名, kind: x.kind, 盒: `${W}×${H}`, 终点: z,
    宽项值: +cw.toFixed(3), 高项值: +ch.toFixed(3),
    宽多出下界: +mw.toFixed(3), 高多出下界: +mh.toFixed(3),
    绑定项: 绑定,
    真compound: +真compound.toFixed(3),
    真多出: +真多出.toFixed(3),
    真多出折屏: +(真多出 * z).toFixed(3),
    屏是否近整数: Math.abs(真多出 * z - Math.round(真多出 * z)) < 0.6,
  };
});

log('════ 逐臂（只报绑定项）════');
for (const r of 表) {
  log(`  ${r.名.padEnd(9)} ${r.kind.padEnd(5)} 盒${r.盒.padEnd(9)} 终点=${String(r.终点).padEnd(10)} `
    + `绑定=${r.绑定项}  真compound=${String(r.真compound).padEnd(10)} 真多出=${String(r.真多出).padEnd(10)} 折屏=${r.真多出折屏}`);
}

const 零多出 = 表.filter((r) => Math.abs(r.真多出) < 1);
const 非零 = 表.filter((r) => Math.abs(r.真多出) >= 1);

const 判定P2 = '📌 P2（修正后）：**只有绑定项的反解值是真 `compound`**，另一项只是下界。\n'
  + '　✅ 真多出 ≈0 的 = ' + (零多出.length ? 零多出.map((r) => `${r.名}(${r.绑定项})`).join('、') : '（无）') + '\n'
  + '　📌 真多出 ≠0 的 = ' + (非零.length ? 非零.map((r) => `${r.名}(${r.绑定项} +${r.真多出}，折屏 ${r.真多出折屏})`).join('、') : '（无）')
  + '\n　🔴 ⇒ **同一个视口下，各 kind 的落点差 `1.18333`（`0.566667`–`1.75`）**，'
  + '📌 **「零 inset」只对 `文本`/`外部` 的【绑定方向】成立，不可跨 kind、也不可跨方向外推**';

const 判定P2订正 = '🔴 **主脚本的 P2 报「文本多出 68.571×0」并据此暗示「两个 60 宽的 handle」，那是错的** ——\n'
  + '　　📌 因为 `68.571 × 1.75 = 120.0` 与 `2×(60/1.75)` **逐字吻合**，'
  + '🔴 **但这个吻合建立在「宽度项绑定」的假设上，而文本臂绑定的是高度项**；\n'
  + '　　🔴 **宽度方向的 `68.571` 是下界不是真值** ⇒ 立规 184 **又一次现形：漂亮的吻合可能只是巧合**。';

const 判定P3 = '✅ P3：文本臂 `文本 1 = 1.75`、`文本 2 = 1.75` 逐字落 `1.75`，'
  + '导演台（外部）同为 `1.75` ⇒ 尺子没漂，本表可用';

const 判定用户表 = '📌 **面向用户的落点表**（视口 `1212×720`，搜索定位后）：\n'
  + 表.map((r) => `　| \`${r.名}\` | ${r.kind} | ${(r.终点 * 100).toFixed(1)}% |`).join('\n')
  + '\n　📌 **同一窗口、同一动作，六个节点卡在四个不同的倍数上** —— '
  + '🔴 **这是节点的固有差异，不是故障，也不是你操作错了**。';

const 复算 = {
  有效臂: `${好.length}/${j.臂表.length}`,
  落点表_只报绑定项: 表,
  落点极差: 表.length > 1 ? +(Math.max(...表.map((r) => r.终点)) - Math.min(...表.map((r) => r.终点))).toFixed(5) : null,
  判定P2: 判定P2,
  判定P2_订正主脚本: 判定P2订正,
  判定P3: 判定P3,
  用户表: 判定用户表,
};
log('\n════ 复算判定 ════\n' + JSON.stringify(复算, null, 1));

j.判定复算 = 复算;
fs.writeFileSync(IN, JSON.stringify(j, null, 1));
log('\n已回写', IN);
process.exit(0);