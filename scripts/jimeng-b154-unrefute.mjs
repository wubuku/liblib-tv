// 批次 154 —— 🔴 撤回并改正**我自己这次犯的「误订正」**
//
// 🔴 发生了什么：本批在 `prepare-generation.md:196` 给 `240×244` 加了「🔴 订正：这是视频族的读数，
//    不是通例」的订正块，并同步写进了 §4.77 / AUDIT / PROGRESS / manifest 的 `verified_locator`。
//    **那个订正是错的。** 三条反证：
//      ① 该行的祖先链逐字写着 `form{video-generation-form}` —— **这一节本来就是视频族语境**；
//      ② 同一文件 `:282` 就有横向对照表：`| **视频** | 240×244 | …（4 项）|`；
//      ③ 手册**早就**记了另外两族：`PROGRESS.md:702`、`AUDIT.md:1331`、
//         `SOURCE_OBSERVATIONS.md:10618` 逐字写着「图片 2 类 240×140、音频 3 类 240×192（无「视频」）」。
//    ⇒ 原行**从来没写错**，是我把「一个族里的读数」当成了「通例」又反过来指责它。
//
// 📌 这与 `AUDIT.md:4194`（批次 149 差点误订正「视频面板 testid 是 video-generation-form」）**完全同型**：
//    **要推翻一条结论前先确认它当初的适用范围。** 我上一批把这个教训写进了手册，自己下一批又犯了一次。
//    ⇒ 本批**把这个再犯也如实记进 AUDIT**，因为「立了规还犯」比「没立规」更值得记。
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 读 = (p) => fs.readFileSync(new URL(p, DIR), 'utf8');
const 存 = (p, s) => fs.writeFileSync(new URL(p, DIR), s);
let 失败 = 0;
const 改 = (路径, 锚, 新, 名) => {
  const s = 读(路径);
  const n = s.split(锚).length - 1;
  if (n !== 1) { console.log('❌ 锚点命中 ' + n + ' 次：' + 名); 失败++; return; }
  const t = s.replace(锚, 新);
  if (t === s || t.indexOf(锚) >= 0) { console.log('❌ replace 未生效或旧锚点仍在：' + 名); 失败++; return; }
  存(路径, t);
  console.log('✅ ' + 名);
};

// ---------- 1) prepare-generation.md：把「订正」改成「适用范围说明」 ----------
const 旧块 = `> 🆕 **2026-10-04 批次 154 订正：\`240×244\` / 4 个类别是「视频」节点的读数，不是通例。**
> 在**图片**节点上同一个面板实测 **\`240×140@168.8,363\`**、\`[role="listbox"]\` 的
> **子项只有 2 个**（\`主体\` / \`图片\`，没有视频与音频），
> 祖先链也换成了 \`div.generation-media-prompt-field < div.flex <
> form{**generation-form**}.generation-input-group < div.generation-input-panel-shell <
> div{node-toolbar-feature-host} < div{node-toolbar}\`。
> ⇒ 📌 **面板高度与类别数随节点族变**：类别数 = 该节点族能引用的资源类别数。
> 自动化断言「4 个 option」只在视频/音频节点上成立。详见 \`SOURCE_OBSERVATIONS\` §4.77。`;
const 新块 = `> 📌 **本节读数的适用范围**：上面这些是**视频**节点上的读数（祖先链逐字就是
> \`form{video-generation-form}\`）。**面板高度与类别数随节点族变**，横向对照见下方那张表：
> **视频 4 类 \`240×244\`**、**图片 2 类 \`240×140\`**、**音频 3 类 \`240×192\`（没有「视频」）**。
> ✅ **2026-10-04 批次 154 在图片节点上独立复现了「2 类 \`240×140\`」这一档**：
> \`240×140@168.8,363\`、\`[role="listbox"]\` 子项**只有 2 个**（\`主体\` / \`图片\`），
> 祖先链是 \`div.generation-media-prompt-field < div.flex <
> form{**generation-form**}.generation-input-group < div.generation-input-panel-shell <
> div{node-toolbar-feature-host} < div{node-toolbar}\`。详见 \`SOURCE_OBSERVATIONS\` §4.77.3。`;
改('10-tasks/prepare-generation.md', 旧块, 新块, 'prepare-generation:196 撤回误订正 → 改成适用范围说明');

// ---------- 2) §4.77.3 标题与「订正」段 ----------
改('SOURCE_OBSERVATIONS.md',
  '### 4.77.3 ✅ Q1 验成：`generation-mention-panel` —— 🔴 `240×244` / 4 项是**视频族**的读数',
  '### 4.77.3 ✅ Q1 验成：`generation-mention-panel`（图片族）+ 🔴 我自己差点误订正一条**本来就正确**的读数',
  '§4.77.3 标题');

改('SOURCE_OBSERVATIONS.md',
  `🔴 **订正**：手册两处记的面板是 **\`240×244\` / 4 个 \`role=option\`（主体 / 图片 / 视频 / 音频）**，
那是**视频**节点上的读数。在**图片**节点上它是 **\`240×140\` / 2 项**。
⇒ 📌 **面板高度与类别数随节点族变**，类别数 = 该节点族能引用的资源类别数。
自动化断言「4 个 option」只在视频/音频节点上成立。已就地订正 \`prepare-generation.md:196\`。`,
  `#### 🔴🔴 自身失误 4：**我差点把一条本来就正确的读数「订正」掉**

我第一反应是「手册记的 \`240×244\` / 4 项是错的，图片节点明明是 \`240×140\` / 2 项」，
于是给 \`prepare-generation.md:196\` 加了一个「🔴 订正」块。**这个订正是错的**，三条反证：

1. **那一行的祖先链逐字写着 \`form{video-generation-form}\`** —— 该节**本来就是视频族语境**；
2. **同一文件 \`:282\` 就有横向对照表**：\`| **视频** | 240×244 | 主体/图片/视频/音频（4 项） |\`；
3. 手册**早就**记了另外两族 —— \`PROGRESS.md:702\`、\`AUDIT.md:1331\`、
   \`SOURCE_OBSERVATIONS.md:10618\`（批次 113）逐字写着
   「**图片 2 类 \`240×140\`、音频 3 类 \`240×192\`（无「视频」）**」。

⇒ 原行**从来没写错**，是我把「一个族里的读数」当成了「通例」，又反过来指责它。
📌 这与 \`AUDIT.md:4194\`（批次 149 差点误订正「视频面板 testid 是 \`video-generation-form\`」）
**完全同型**：**要推翻一条结论前先确认它当初的适用范围。**
🔴 **上一批把这个教训写进了手册，本批又犯了一次** —— 「立了规还犯」比「没立规」更值得记，
所以这一条也如实进了 AUDIT。
✅ 已把误加的订正块**撤回**，改成「📌 本节读数的适用范围」并指向横向对照表。
本轮在**图片**节点上实测到的 \`240×140\` / 2 项 / 祖先链换成 \`form{generation-form}\`，
是对批次 113 那条横向规律的**独立复现**，不是订正。`,
  '§4.77.3「订正」段 → 自身失误 4');

// ---------- 3) AUDIT.md 那一行 ----------
改('AUDIT.md',
  '| ✅ **`generation-mention-panel` 的 `240×244` / 4 项是「视频族」的读数** | Minor（订正） | 图片节点上实测 `240×140@168.8,363`、`listbox` 子项**只有 2 个**（主体 / 图片），祖先链换成 `form{generation-form}` | 就地订正 `prepare-generation.md:196`。📌 **面板高度与类别数随节点族变**，类别数 = 该节点能引用的资源类别数 |',
  '| 🔴 **我自己差点误订正一条本来就正确的读数** | 🔴 **Major（自身 bug，同型第二次）** | 我给 `prepare-generation.md:196` 的 `240×244` 加了「🔴 订正：这是视频族的读数」—— **错**。反证三条：① 该行祖先链逐字就是 `form{video-generation-form}`，**本来就是视频族语境**；② 同文件 `:282` 就有横向对照表 `| **视频** | 240×244 | …（4 项）|`；③ 手册**早已**记了另外两族（`PROGRESS.md:702`、`AUDIT.md:1331`、`SOURCE_OBSERVATIONS.md:10618` 批次 113：「图片 2 类 240×140、音频 3 类 240×192」） | **已撤回**误加的订正块，改成「📌 本节读数的适用范围」并指向横向对照表。本轮在图片节点上实测 `240×140` / 2 项 / 祖先链换成 `form{generation-form}`，是对批次 113 的**独立复现**，不是订正。📌 **与本表 4194 行（批次 149）完全同型：要推翻一条结论前先确认它当初的适用范围。上一批把这个教训写进了手册，本批又犯了一次** |',
  'AUDIT 那一行 → 自身 bug');

// ---------- 4) PROGRESS.md 那一行 ----------
改('PROGRESS.md',
  '- **本批结论**：14 条断言全过；`generation-mention-panel` 🔴 **`240×244`/4 项是视频族**（图片族 `240×140`/2 项）；',
  '- **本批结论**：14 条断言全过；`generation-mention-panel` 在**图片**节点上实测 `240×140` / 2 项，**独立复现**批次 113 的横向规律（🔴 我一度把它当成对 `240×244` 的订正，**那是误订正、已撤回**，见 §4.77.3 自身失误 4）；',
  'PROGRESS 本批结论行');

// ---------- 5) manifest 54 的 verified_locator ----------
{
  const P = 'screenshots/manifest.yml';
  const s = 读(P);
  const 旧 = '⚠️ **本图顺带纠正一条被当成通例的读数**：手册记的面板是 240×244 / 4 个类别，那是**视频**节点；**图片**节点上它是 240×140 / 只有主体与图片两项 ⇒ 面板高度与类别数**随节点族变**，不能跨族套用。';
  const 新 = '📌 **本图读数的适用范围**：手册 `prepare-generation.md` 那节记的 240×244 / 4 个类别是**视频**节点的读数（该节祖先链逐字就是 form{video-generation-form}），**不是错记**；本图在**图片**节点上实测 240×140 / 只有主体与图片两项，是对批次 113 那条「面板高度与类别数随节点族变」横向规律的**独立复现**。';
  const n = s.split(旧).length - 1;
  if (n !== 1) { console.log('❌ manifest verified_locator 锚点命中 ' + n + ' 次'); 失败++; }
  else { const t = s.replace(旧, 新); if (t === s) { console.log('❌ manifest replace 未生效'); 失败++; } else { 存(P, t); console.log('✅ manifest 54 的 verified_locator 已改正'); } }
}

console.log(失败 ? '\n⛔ ' + 失败 + ' 处失败' : '\n✅ 误订正已全部撤回改正');
process.exit(失败 ? 1 : 0);
