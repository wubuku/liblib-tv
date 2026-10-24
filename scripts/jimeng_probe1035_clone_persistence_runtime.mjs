/**
 * 批 1035：复刻「刷新即复位」与「离线弹窗可达性」的运行时实测。
 *
 * 为什么要有这道探针：
 *   手册 10-tasks/canvas-context.md 给的重命名「成功判据」是
 *   「顶栏标题文字变化 + 刷新后仍是新名」—— 那是源站的判据（源站画布在服务端）。
 *   复刻是本地 mock，刷新即复位；同一页还写着「内容跨刷新持久（实测）」，
 *   以及「发现离线编辑」对话框的处理方式，而复刻里那个弹窗界面上没有触发路径。
 *   => 照着手册做必然失败，而失败长得像「复刻坏了」。
 *
 * 本探针只报事实、不定性：
 *   「复刻刷新即复位」是实测事实、不是缺陷判决；
 *   缺陷在文档（手册正文没标主体），定性留给 1035 的判决器。
 *
 * 纪律：
 *   产物里不许出随机量/时间戳 => 每次跑必须逐字节相同；
 *   探针必须自证有牙：改完不刷新时读数确实变了，
 *   否则「刷新后没变」可能是探针根本没读到状态。
 */
import pw from "/Users/yangjiefeng/node_modules/playwright/index.js";
import { writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
// ⭐ 运行时读数放 `inputs/`（与其它 .mjs 运行时产物同例）
//   ⇒ 因为 1015 的「通道 B」只认 `scripts/jimeng_probe*.py`
//   ⇒ 而放在产物目录里会被判「unlinked」（没有对应的 .py 探针）而红
const OUT = resolve(
  ROOT,
  "docs/research/jimeng-canvas/inputs/clone-persistence-1035.json",
);
// 与 verify-jimeng-batch812.py 用同一个环境变量名 ⇒ 门禁清单里两个门共用一套配置
const BASE_URL = process.env.JIMENG_BASE_URL || "http://localhost:4317";
const URL_ = BASE_URL + "/jimeng/canvas/demo";
const PROBE_NAME = "探针改名";

const readState = (page) =>
  page.evaluate(() => {
    const s = window.__jimengStore?.getState?.();
    return s
      ? {
          name: s.project?.name ?? null,
          n_nodes: s.nodes?.length ?? null,
          n_offline_edits: (s.offlineEdits || []).length,
          offline_dialog_open: s.offlineDialogOpen === true,
          offline_mode: s.offlineMode === true,
          ls_keys: Object.keys(window.localStorage).sort(),
        }
      : null;
  });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext();
const page = await ctx.newPage();

await page.goto(URL_, { waitUntil: "networkidle" });
await page.waitForTimeout(1200);
const s0 = await readState(page);
const initial_name = s0?.name ?? null;
const initial_n_nodes = s0?.n_nodes ?? null;

// 1) 改三样：项目名 / 加一个节点
await page.evaluate((probeName) => {
  const s = window.__jimengStore.getState();
  s.renameProject(probeName);
  s.addNodeAt("text", { x: 111, y: 222 });
}, PROBE_NAME);
await page.waitForTimeout(500);
const s1 = await readState(page);

// 2) 刷新
await page.reload({ waitUntil: "networkidle" });
await page.waitForTimeout(1500);
const s2 = await readState(page);

// 3) 离线弹窗：界面上有没有触发路径
const ui_reach = await page.evaluate(() => {
  const in_dom = !!document.querySelector('[data-testid="jimeng-offline-dialog"]');
  const cands = Array.from(
    document.querySelectorAll(
      "button, [role=button], a[href], input, [role=switch], [role=checkbox]",
    ),
  )
    .map((el) => (el.getAttribute("aria-label") || el.textContent || "").trim())
    .filter((t) => /离线|同步|冲突|重新加载|重载|未保存/.test(t));
  return {
    in_dom,
    n_trigger_candidates: cands.length,
    candidates: cands.slice(0, 8),
  };
});

// 4) 离线弹窗：dev hook 能不能打开（测试用的可达路径）
const devhook = await page.evaluate(() => {
  const st = window.__jimengStore?.getState?.();
  if (!st) return { hook_present: false, dialog_opened: false };
  st.setOfflineDialog(true);
  // 必须**调用后重新取** store —— 上面那个 st 是调用前的快照（陈旧读）
  const after = window.__jimengStore.getState();
  return { hook_present: true, dialog_opened: after.offlineDialogOpen === true };
});
const dom_after_hook = await page.evaluate(
  () => !!document.querySelector('[data-testid="jimeng-offline-dialog"]'),
);

await browser.close();

const facts = {
  generated_by: "jimeng_probe1035_clone_persistence_runtime.mjs",
  what_this_probe_measures:
    "复刻在「刷新」与「离线弹窗」这两件事上的实测行为。只报事实、不定性；定性在 1035 的判决器里。",
  scan_scope:
    "只量复刻自己（本地 mock 运行时，Playwright 无头）。不是源站。",
  readings: {
    probe_can_read_change: {
      name_changed: s1?.name === PROBE_NAME,
      n_nodes_changed: (s1?.n_nodes ?? 0) === (initial_n_nodes ?? 0) + 1,
      ls_keys_after_mutation: s1?.ls_keys ?? [],
    },
    refresh_resets: {
      name_reset_to_initial: s2?.name === initial_name,
      n_nodes_reset_to_initial: s2?.n_nodes === initial_n_nodes,
      ls_keys_after_reload: s2?.ls_keys ?? [],
    },
    offline_dialog_ui: {
      in_dom_at_start: ui_reach.in_dom,
      n_trigger_candidates: ui_reach.n_trigger_candidates,
      candidates: ui_reach.candidates,
    },
    offline_dialog_devhook: {
      hook_present: devhook.hook_present,
      dialog_opened: devhook.dialog_opened,
      dialog_in_dom_after_hook: dom_after_hook,
    },
  },
  what_this_is_not:
    "这不是「复刻有没有 bug」的判决。复刻刷新即复位是本原型的设计取舍（mock 数据）；缺陷在手册正文没有标明哪些是源站行为、哪些在复刻上不同。",
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(facts, null, 2) + "\n");
console.log("PROBE_1035_CLONE_PERSISTENCE_DONE -> " + OUT);
console.log(
  "readings: " +
    JSON.stringify({
      name_changed: facts.readings.probe_can_read_change.name_changed,
      name_reset_to_initial: facts.readings.refresh_resets.name_reset_to_initial,
      n_nodes_reset_to_initial: facts.readings.refresh_resets.n_nodes_reset_to_initial,
      n_trigger_candidates: facts.readings.offline_dialog_ui.n_trigger_candidates,
      devhook_dialog_in_dom: facts.readings.offline_dialog_devhook.dialog_in_dom_after_hook,
    }),
);
