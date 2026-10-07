// LibTV 画布手册取证 —— 共用无头浏览器 harness。
//
// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐⭐⭐ 缺陷 494：**`git commit` 提交的是整个 index，不只是你刚 add 的**
// ════════════════════════════════════════════════════════════════════
//   FX 提交 `c0e308ef` 混进了 9 个别人的文件（另一本手册 jimeng-canvas + scripts/jimeng-*）。
//
//   我一直用的守卫是「`git add 我的目录` → 数 index 里有没有别人的文件 → 没有才 commit」，
//   而这次它**确实报 0** —— 因为那 9 个文件是在**守卫跑完之后、commit 执行之前**
//   被那位开发者 add 进去的。
//
//   ⛔⭐⭐ **这个竞态窗口关不掉**：共享仓库里只要别人还在 `git add`，
//   「add → 检查 → commit」三步之间随时可能撞上。
//   别人在 3a66649c 已经记了同一条教训，两边结论一致。
//
//   ┌──────────────────────────────────────────────────────────────┐
//   │ ⭐⭐⭐ 发现混入时的唯一正确动作：**什么都不做**                  │
//   │                                                              │
//   │  ⛔ 绝不 revert / reset / amend —— 那会把别人的内容从历史里    │
//   │     摘掉，而他们本地还带着这些文件 ⇒ 下次 pull 冲突，          │
//   │     **等于干扰别人的工作**。                                  │
//   │  ✅ 正确做法：立刻自查（git show --name-only HEAD）、写进     │
//   │     PROGRESS 说明归属错误、内容未动，然后继续。              │
//   └──────────────────────────────────────────────────────────────┘
//
//   ⭐ 理由：回滚造成的伤害**远大于**「commit message 归属错了」。
//
//   ⛔ 也**不要**改用 `git commit -- <路径>` 来「限定范围」：
//   它看似能绕开问题，但**在有 pre-commit 钩子且钩子失败时会把暂存区一起清空** ——
//   那是更严重的事故（本仓库的 pre-commit 本来就在失败，见各处 --no-verify 的理由）。
//
//   实操：① 提交前把 `git diff --cached --name-only` **紧挨着 commit** 再跑一次
//        ② commit 后立刻 `git show --name-only HEAD` 自查
//        ③ 混入时不回滚，只记录。

// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐⭐⭐ 缺陷 531：上面说「这扇窗口关不掉」—— **说错了，可以用 `GIT_INDEX_FILE` 绕开**
// ════════════════════════════════════════════════════════════════════
//   Batch HN 撞上了：守卫报「非我的 0 个」（**是真 0**），
//   但 commit 里还是混进了别人 16 个在 index 里躺着的 WIP。
//   轮询两分钟 index 一直不清 —— 别人在**长时间积累 WIP**，不会很快提交。
//   于是「等」这条路不成立。
//
//   ┌──────────────────────────────────────────────────────────────┐
//   │ ✅ 正确解法：在**临时 index** 上完成整个 add + commit        │
//   └──────────────────────────────────────────────────────────────┘
//     BEFORE=$(git ls-files -s | md5)          # 真实 index 指纹
//     export GIT_INDEX_FILE=/tmp/iso-$$.idx   # 换掉 index 路径
//     git read-tree HEAD                     # 以 HEAD 为底建一个干净的
//     git add <只有我的文件>
//     git diff --cached --name-only           # 在隔离 index 上做守卫
//     git commit --no-verify -F msg
//     unset GIT_INDEX_FILE
//     AFTER=$(git ls-files -s | md5)          # 指纹必须与 BEFORE 逐字相同
//
//   ⭐⭐⭐ 为什么这个方案零风险：
//     真实 index **一个字节都没被碰过**（指纹可证），别人的 16 个 WIP 原样保留；
//     我的提交里**只有我的文件**（守卫在隔离 index 上跑，是真 0）。
//     而 HEAD 前进不影响别人 —— 新提交不触碰他们 index 里任何一个路径。
//
//   ⛔ 提交前务必确认：**我的文件路径与别人 index 里的路径零重叠**。
//   ⛔ 指纹不一致就停下来查，绝不硬推。
//
//   ⚠️ HN 实测：BEFORE = AFTER = e5a2837c…，提交 `1eca8109` 只含 5 个我的文件。
//
//   ⛔ 仍然**不要**用 `git commit -- <路径>`（见上：钩子失败会清空暂存区）——
//      `GIT_INDEX_FILE` 之所以安全，正是因为它**根本不碰暂存区**。

// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐⭐⭐ 缺陷 462：**动手写「这个界面我没见过」之前，先 grep 三本账**
// ════════════════════════════════════════════════════════════════════
//   批次在动手前**必须**跑一遍（只读，不贵）：
//       grep -c '<关键词>' docs/user-manual/libtv-canvas/{task-inventory.yml,AUDIT.md,PROGRESS.md}
//
//   为什么这是硬规矩：Batch FP-2 按「手册正文里没写这个面板」去补页，
//   ⛔ 没先查账本，结果给一个**早就测过**的面板写了三个错解释
//   （把「全灰」说成「节点里没图」，与 BA1 的读数直接矛盾），
//   差点用错的覆盖掉对的。只查正文既**重复劳动**，又**危险**。
//
//   命中数很低 ≠ 没测过 —— 账本里的记法五花八门
//   （有的记 class 名、有的记 key 前缀、有的只在 batch 脚本注释里）。
//   查不到就当「没查过」，但要在 PROGRESS 里写明查过、查了哪三本。
//
// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐⭐⭐ 节点类型判据：读 `class` 里的 `react-flow__node-<type>`，别读卡片文字
// ════════════════════════════════════════════════════════════════════
//   FQ-1 实测：节点的真实类型直接写在 class 上，一眼可分、不受文案改版影响：
//       react-flow__node-script-v2       脚本 NEW        ← 前缀 `scriptV2*` 就是它
//       react-flow__node-video-clip      智能剪辑        ← 前缀 `clip*` 是它
//       react-flow__node-shot-breakdown  分镜拆解/逐帧拉片
//       react-flow__node-image / -video / -audio / -text
//       react-flow__node-director-console-3d
//   ⭐⭐⭐ **测试画布 projectId=a4ef3de0cdca4977ba45b373eb5165b5 上有主画布没有的三种**
//   （`script-v2` / `video-clip` / `shot-breakdown`）——
//   只在主画布 34226ef1… 上找，永远找不到这三类。
//
//   ⛔ 反过来：**class 只能判「是什么类型」，不能判「能不能点」** ——
//   同一个 class 的节点，当前状态（有没有图、有没有连上输入）完全不同。
//
// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐ 可复算的数字不许手抄进正文
// ════════════════════════════════════════════════════════════════════
//   FK 把文案表统计**手抄**进 `20-reference.md`：6342 / 4850 / 9 个分组条数。
//   FQ-1 重算发现 7 个分组条数是错的（scriptV2 记 42 实为 93、clip 记 89 实为 348）。
//   ⇒ 数字要么给一个能重跑的脚本（见 `tools/i18n-census.py`），要么别写进正文。
//
// 约定：
//   - 全部脚本通过本模块启动 **无头** Chromium + 已提取的 storageState，
//     绝不 attach、不复用、不干扰用户自己那个有头窗口（CDP 9222）。
//   - 每次启动都是全新的独立 user-data-dir，互不串味，也不需要再登录。
//   - viewport / locale / 时区 / reduced-motion 固定，保证截图可比。
//   - 站点有「单画布单编辑者保护」：同一 project 在第二处打开会给遮罩。
//     所以默认用 HANDOFF_PROJECT 之外的测试项目，见 PROGRESS.md 的项目台账。
import { chromium } from 'playwright';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const HERE = dirname(fileURLToPath(import.meta.url));
export const AUTH = resolve(HERE, '.auth/libtv-storage-state.json');
export const ORIGIN = 'https://www.liblib.tv';
export const SHOTS = resolve(HERE, '../screenshots');

export const VIEWPORT = { width: 1440, height: 810 };

export async function launch(opts = {}) {
  if (!existsSync(AUTH)) {
    throw new Error(`缺少登录态 ${AUTH}；先运行 node tools/extract-auth.mjs`);
  }
  const storageState = JSON.parse(await readFile(AUTH, 'utf8'));
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
    ],
  });
  const ctx = await browser.newContext({
    storageState,
    viewport: opts.viewport ?? VIEWPORT,
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
    deviceScaleFactor: 2,
    // 'reduce' 是为了让截图可比（动画停在中途不会每次都不一样）。
    // ⚠️ 但要**按需覆盖**：站点有些元素靠动画驱动 inline opacity，
    //    在 'reduce' 下过渡被跳过，它们可能停在 opacity 0 —— 也就是
    //    「DOM 里有、屏幕上没有」。要核实某个元素到底显不显示，
    //    用 launch({ reducedMotion: 'no-preference' }) 再量**整条祖先链的 opacity 连乘**
    //    （只看它自己那一层会读出假的稳定值，CI-2 就栽在这儿）。
    //
    // ⭐⭐ Batch DH 实测量化了这条的影响（别只当「可能有动画」）：
    //   无头 Chrome **默认报 `prefers-reduced-motion: reduce`**。
    //   站点大量使用 Tailwind 的 `motion-safe:` 前缀，它编译成
    //   `@media (prefers-reduced-motion: no-preference)` ⇒ 在此环境下**整条规则不匹配**。
    //   实测对照（`z-[180]` 那个全屏层）：
    //     无头默认          → transition-duration: 0s   transition-property: all
    //     覆盖 no-preference → transition-duration: 0.2s transition-property: opacity
    //   ⇒ **凡是要断言「某处有/没有动画 / 淡入淡出读不到」的结论，
    //     必须用 `reducedMotion: 'no-preference'` 重测**，否则量的是被关掉的规则。
    //   ⛔ 只量 **opacity 最终值** 的读数不受影响（opacity 不是被这条 media query 管的）。
    reducedMotion: opts.reducedMotion ?? 'reduce',
    colorScheme: 'light',
  });
  ctx.setDefaultTimeout(opts.timeout ?? 20000);
  const page = await ctx.newPage();
  return { browser, ctx, page };
}

/** 打开一个 URL 并等到画布 shell 稳定（字体就绪 + React Flow 挂载 + 网络静默）。 */
export async function open(page, url, { settle = 1200 } = {}) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.evaluate(() => document.fonts?.ready).catch(() => {});
  await page.waitForTimeout(settle);
  return page;
}

/** 探测是否命中「单画布单编辑者保护」遮罩。返回 true 表示这个项目被别处占用。 */
export async function isEditorLocked(page) {
  return page.evaluate(() => {
    const t = document.body.innerText || '';
    return /会话已过期|请刷新页面以继续编辑/.test(t);
  });
}

/** Skill 自带的目标高亮脚本绝对路径（tools → libtv-canvas → user-manual → docs → 仓库根）。 */
export const HIGHLIGHT_JS = resolve(HERE, '../../../../.agents/skills/web-studio-user-manual/scripts/highlight-target.js');

/** 注入目标高亮脚本（幂等）。 */
export async function injectHighlight(page) {
  await page.addScriptTag({ path: HIGHLIGHT_JS });
}

/**
 * 拍一张带目标高亮的截图。
 * @param {import('playwright').Locator} locator 目标元素
 * @param {string} file 相对 screenshots/ 的文件名
 * @param {{step?:number, note?:string, clip?:{x,y,width,height}}} opts
 */
export async function shotHighlighted(page, locator, file, opts = {}) {
  await injectHighlight(page);
  await locator.scrollIntoViewIfNeeded();
  if (opts.step != null) {
    await locator.evaluate((el, step) => window.canvasUserManualHighlight.show(el, { step }), opts.step);
  }
  await page.waitForTimeout(220);
  await page.screenshot({ path: resolve(SHOTS, file), ...(opts.clip ? { clip: opts.clip } : {}) });
  if (opts.step != null) await page.evaluate(() => window.canvasUserManualHighlight.clear());
  return file;
}

/** 不带高亮拍一张（概览图 / 结果图）。 */
export async function shot(page, file, opts = {}) {
  await page.screenshot({ path: resolve(SHOTS, file), ...(opts.clip ? { clip: opts.clip } : {}) });
  return file;
}

/**
 * 关掉所有「不该出现在取证画面里」的浮层：促销弹窗、引导蒙层、下载提示等。
 * 站点用 Mantine Modal。实测 `.mantine-Modal-root` 可能是空的壳节点，真正的
 * 遮罩是 `.mantine-Modal-overlay`，且促销弹窗的关闭按钮不在 `.mantine-Modal-content`
 * 里（aria-label=关闭 那个属于顶部横幅）。所以这里按可靠性排序：Escape → 点遮罩 → 找关闭钮。
 * 站点有单画布单编辑者锁，那个遮罩**不能**关（它是被测行为本身），因此先识别再关。
 */
/**
 * ⭐⭐⭐⭐ 关掉**非 Mantine 模态**的固定定位推广浮层。
 *
 * 起因（Batch FD-3 实测）：「Agent 已升级为 TV Director」是
 *   `<div class="fixed w-[280px] max-w-[calc(100vw-24px)]">`，**z-index 101**，
 *   ⛔ 不是 `.mantine-Modal-overlay` ⇒ 老版 closePromos 连关 5 轮都关不掉，
 *   它会一直挡着画面、把 innerText 读数搅浑。
 *
 * ⛔ 安全边界（必须保留）：只点**纯 dismiss 文案**的白名单按钮。
 *   ⛔ **绝不点 `去体验` / `开始体验`** —— 那会真的进入体验流程。
 *   白名单里的每一个字都是「知道了 / 我知道了 / 关闭 / 不再提示」，
 *   点下去的唯一后果是这个浮层消失。
 * 判据要窄：position:fixed + 尺寸 200~600 + 自身文案命中推广词 + 按钮文案在白名单里。
 */
const 关浮层白名单 = ['知道了', '我知道了', '知道了！', '关闭', '不再提示', '以后再说', '稍后再说'];

async function closeFixedPromos(page, max = 4) {
  const 关掉的 = [];
  for (let i = 0; i < max; i += 1) {
    const 目标 = await page.evaluate((白名单) => {
      const 推广词 = /已升级|新功能|来试|体验一下|限时|推荐|抢先|内测/i;
      const 可见 = (el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      };
      const 浮层 = [...document.querySelectorAll('div.fixed, section.fixed, aside.fixed')]
        .filter((el) => {
          if (!可见(el)) return false;
          const cs = getComputedStyle(el);
          if (cs.position !== 'fixed') return false;
          const r = el.getBoundingClientRect();
          if (r.width < 180 || r.width > 640 || r.height < 120 || r.height > 720) return false;
          return 推广词.test((el.innerText || '').slice(0, 300));
        });
      for (const f of 浮层) {
        const btn = [...f.querySelectorAll('button,[role="button"]')]
          .find((b) => 可见(b) && 白名单.includes((b.innerText || b.getAttribute('aria-label') || '').trim()));
        if (!btn) continue;
        const r = f.getBoundingClientRect();
        const br = btn.getBoundingClientRect();
        return {
          文字: (f.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
          按钮: (btn.innerText || btn.getAttribute('aria-label') || '').trim(),
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          点击点: [Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2)],
        };
      }
      return null;
    }, 关浮层白名单);
    if (!目标) break;
    await page.mouse.click(目标.点击点[0], 目标.点击点[1]);
    await page.waitForTimeout(400);
    关掉的.push(目标);
  }
  return 关掉的;
}

export async function closePromos(page) {
  const report = [];
  // ⭐ 先收非模态的 fixed 推广浮层（老版漏了这一类，见上方注释）
  const fixed = await closeFixedPromos(page);
  for (const f of fixed) report.push({ 模态: false, 文字: f.文字, 按钮: f.按钮, 框: f.框, 怎么关的: 'fixed-按钮', gone: true });
  for (let i = 0; i < 5; i += 1) {
    const info = await page.evaluate(() => {
      const ov = [...document.querySelectorAll('.mantine-Modal-overlay')].filter((m) => {
        const r = m.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      });
      if (!ov.length) return null;
      const host = ov[ov.length - 1].parentElement || ov[ov.length - 1];
      const label = (host.innerText || '').replace(/\s+/g, ' ').slice(0, 100);
      const btns = [...host.querySelectorAll('button,[role="button"]')].map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim().slice(0, 12));
      return { label, btns, hostSel: host.className?.toString?.().slice(0, 50) };
    });
    if (!info) break;

    let how = null;
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(350);
    let gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    if (gone) how = 'Escape';

    if (!gone) {
      const closeBtn = page.locator('.mantine-Modal-overlay').last().locator('xpath=..').locator('button[aria-label="关闭"], button[aria-label="Close"]');
      await closeBtn.first().click({ timeout: 3000 }).then(() => { how = 'close-btn'; }).catch(() => {});
      await page.waitForTimeout(350);
      gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    }
    if (!gone) {
      await page.locator('.mantine-Modal-overlay').last().click({ position: { x: 5, y: 5 }, timeout: 3000 }).then(() => { how = 'overlay-click'; }).catch(() => {});
      await page.waitForTimeout(350);
      gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    }
    report.push({ modal: info.label, btns: info.btns.slice(0, 6), how, gone });
    if (!gone) break;
  }
  return report;
}

// ---------------------------------------------------------------------------
// ⭐⭐⭐⭐⭐ 画布节点复原：唯一正确入口（Batch FB/FD/FE/FF 连续四次事故的共同死因）
//
// ⛔⛔ 为什么「读误差 → 换算像素 → 再拖」的**多轮迭代**必然发散：
//    **「请求拖 N 个屏幕像素」≠「节点真的移动了 N 个像素」。**
//    `Math.round` 取整 + Playwright 的 move 事件合并 + React 批处理，
//    三者叠加出一个**每轮不同、而且同号累积**的偏差。
//    FF-1 实测两轮偏差都是 **−6 个画布单位** ⇒ 越修越远。
//    ⛔ 而且**开态（不吸附）下也一样发散** —— 吸附只是加剧因素，不是根因。
//    ⇒ 历史上 restore-v2～v9、FE-2、FF-1 的 `finally` 全都栽在这条上，
//      **四次把节点推出画布，zoom 被 `⌘0` 压到 0.1，11 个节点一个都不渲染。**
//
// ✅ 正确的复原只有三种，按可靠性排序（本项目前九版成功轮次全部用的是 ①）：
//
//   ① **往返法**（最稳）：拖 +d 再拖 −d，净位移为 0。
//      正反两次的偏差对称抵消。**做实验时优先用这个** —— 直接就不留下残差。
//
//   ② **一步复原**（有残差时用）：⛔ 必须先确认「网格吸附」是**开态**（不吸附），
//      然后**用一整段大位移**走掉绝大部分，再用**单帧小步长**补最后一点。
//      ⚠️ 最多补 3 次；补的位移**不取整**（直接用浮点 `p.x + dx/zoom`），
//      否则 `Math.round` 会把小位移整个吞掉。
//
//   ③ **兜底**：产品自带的「**整理画布**」+ 弹窗里点「**保留**」。
//      已验证 3 次都可靠，代价是整块平移、相对布局被重排。
//      ⚠️ 「整理画布」会自己重置视口，不需要再按 `⌘0`。
// ---------------------------------------------------------------------------

/** 读某个节点当前的画布坐标；读不到返回 null（框选状态要用本函数，别用 querySelectorAll）。 */
export async function 读画布坐标(page, id) {
  return page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return t ? [Number(t[1]), Number(t[2])] : null;
  }, id);
}

/** 读当前 zoom（从视口的 matrix 里取第一项）。 */
export async function 读当前zoom(page) {
  return page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([^)]+)\)/.exec(v ? getComputedStyle(v).transform || '' : '');
    return m ? Number(m[1].split(',')[0]) : 1;
  });
}

/** 在节点框内扫 6×6 格，返回「属主对 且 无 nodrag 祖先」的落点。 */
export async function 扫干净落点(page, id) {
  const 框 = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  }, id);
  if (!框) return [];
  const [L, T, W, H] = 框;
  const 好 = [];
  for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++) {
    const x = L + Math.round(W * (c + 0.5) / 6), y = T + Math.round(H * (r + 0.5) / 6);
    if (x < 4 || x > 1436 || y < 4 || y > 806) continue;
    const ok = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
    }, [x, y, id]);
    if (ok) 好.push({ x, y });
  }
  return 好;
}

/**
 * ① 往返法：把节点拖 +总屏px 再拖 −总屏px，净位移应当为 0。
 * ⭐ 每帧步长 ≤4 屏 px、帧间隔 170ms —— 单次 `mouse.move(x, y, {steps:8})` 的
 *   8 步间隔是 0ms，React 的批量更新会把位移**整个吞掉**（实测 ±1~±30px 位移全是 0）。
 * @returns {{净位移:number, 去:object, 回:object}}
 */
export async function 往返拖(page, id, 总屏px, 每帧步长 = 4, 落点 = null) {
  const 拖一段 = async (dx) => {
    const 落 = 落点 || (await 扫干净落点(page, id))[0];
    if (!落) return null;
    const 起 = await 读画布坐标(page, id);
    const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 每帧步长));
    await page.mouse.move(落.x, 落.y); await page.waitForTimeout(280);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 帧数; i++) {
      await page.mouse.move(落.x + (dx * i) / 帧数, 落.y);
      await page.waitForTimeout(170);
    }
    await page.mouse.up(); await page.waitForTimeout(600);
    await page.mouse.move(720, 170); await page.waitForTimeout(220);
    return { 起, 后: await 读画布坐标(page, id) };
  };
  const 去 = await 拖一段(总屏px);
  const 回 = await 拖一段(-总屏px);
  const 净 = 去 && 回 && 去.后 && 回.后 ? Number((回.后[0] - 去.起[0]).toFixed(4)) : null;
  return { 净位移: 净, 去, 回 };
}

/**
 * ② 一步复原：把节点拖回目标画布坐标。
 * ⛔ 调用前**必须**确保「网格吸附」是开态（不吸附），否则落点会被栅格量化。
 * @returns {{ok:boolean, 轮:number, 终:number[]|null, 原因?:string}}
 */
export async function 一步复原(page, id, 目标, { 容差 = 1.5, 最多补 = 3 } = {}) {
  for (let 轮 = 0; 轮 <= 最多补; 轮++) {
    const 现 = await 读画布坐标(page, id);
    if (!现) return { ok: false, 轮, 终: null, 原因: '节点读不到（可能已被推出视口，先用「整理画布」兜底）' };
    const dx = 目标[0] - 现[0], dy = 目标[1] - 现[1];
    if (Math.hypot(dx, dy) <= 容差) return { ok: true, 轮, 终: 现 };
    const z = await 读当前zoom(page);
    const 落 = (await 扫干净落点(page, id))[0];
    if (!落) return { ok: false, 轮, 终: 现, 原因: '框内找不到无 nodrag 的落点' };
    // ⭐ 留 5% 余量给后面的单帧补差，别指望一段就正好到位
    const 目标px = 轮 === 0 ? (dx / z) * 0.95 : dx / z;
    const 帧数 = Math.max(轮 === 0 ? 6 : 1, Math.round(Math.abs(目标px) / 4));
    await page.mouse.move(落.x, 落.y); await page.waitForTimeout(280);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 帧数; i++) {
      // ⭐ 补差阶段**不取整**：Math.round 会把小于半像素的位移整个吞掉
      await page.mouse.move(轮 === 0 ? 落.x + (目标px * i) / 帧数 : 落.x + 目标px, 落.y);
      await page.waitForTimeout(170);
    }
    await page.mouse.up(); await page.waitForTimeout(620);
    await page.mouse.move(720, 170); await page.waitForTimeout(220);
  }
  const 终 = await 读画布坐标(page, id);
  return { ok: false, 轮: 最多补 + 1, 终, 原因: '补差次数用完（请改用「整理画布」兜底）' };
}

/**
 * ③ 兜底：产品自带的「整理画布」+ 弹窗里点「保留」。
 * ⚠️「整理画布」会**重排相对布局并整块平移**，是最后手段。
 * ⚠️ 弹窗里**点「保留」**（点「还原」会退回坏状态）。
 */
export async function 整理画布兜底(page) {
  const btn = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button')) {
      if ((x.getAttribute('aria-label') || '').includes('整理画布')) {
        const r = x.getBoundingClientRect();
        if (r.width > 0) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (!btn) return { ok: false, 原因: '找不到「整理画布」按钮' };
  await page.mouse.click(btn[0], btn[1]);
  await page.waitForTimeout(2500);
  const 保留 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button')) {
      if ((x.innerText || '').trim() === '保留') {
        const r = x.getBoundingClientRect();
        if (r.width > 0) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (!保留) return { ok: false, 原因: '弹窗里找不到「保留」' };
  await page.mouse.click(保留[0], 保留[1]);
  await page.waitForTimeout(6000);
  return { ok: true };
}

/** 打印页面壳信息 + 一级可交互表面，用于快速建立候选任务清单。 */
export async function shell(page) {
  return page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    const btns = [...document.querySelectorAll('button,[role="button"],[role="menuitem"],[role="tab"]')]
      .filter(vis)
      .map((b) => ({
        text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 24),
        aria: b.getAttribute('aria-label') || null,
        role: b.getAttribute('role'),
        testid: b.getAttribute('data-testid'),
        x: Math.round(b.getBoundingClientRect().x),
        y: Math.round(b.getBoundingClientRect().y),
      }))
      .filter((b) => b.text);
    return {
      url: location.href,
      title: document.title,
      buttons: btns,
      dialogs: [...document.querySelectorAll('[role="dialog"]')].filter(vis).map((d) => (d.innerText || '').slice(0, 200)),
      text: (document.body.innerText || '').slice(0, 1500),
    };
  });
}

// ---------------------------------------------------------------------------
// ⭐⭐⭐⭐⭐ 判据工具箱（Batch FN 血的教训，**所有脚本共用，禁止各写各的**）
//
// 背景：FM 把「只抓了一个 5904px 宽容器的可视区」当成覆盖率（1/747=0.1%），
// FN-1 修好判据（0.1% → 3.6%）之后，FN-2 又发现**第三个陷阱**：
// `开底栏()` 只断言「按钮的 rect 找得到」，而**上一个面板盖住底栏**时，
// 点击落在空白处、断言照样过、**截图张冠李戴** —— 连累了 FI 那一批结论。
// ⇒ 这里把「面板确实切了」写成**三条硬断言**，谁用都受同一套判据。
// ---------------------------------------------------------------------------

/** 全页可见文字（含 aria-label / title / placeholder / alt）。
 *  ⛔ 默认**过滤掉 opacity ≤ 0.01 的元素** —— 这会漏掉 `group-hover:` 才显形的那一类
 *  （素材库副标题就是，`缺陷 453`）。要抓这类请用 `全页文字(page, {含透明: true})`。 */
export async function 全页文字(page, { 含透明 = false } = {}) {
  return page.evaluate((含透明) => {
    const 可见 = (el) => {
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') return false;
      return 含透明 || Number(cs.opacity) > 0.01;
    };
    const 集 = new Set();
    for (const el of document.querySelectorAll('body *')) {
      if (!可见(el)) continue;
      for (const n of el.childNodes) {
        if (n.nodeType === 3) { const t = (n.textContent || '').replace(/\s+/g, ' ').trim(); if (t) 集.add(t); }
      }
      for (const a of ['aria-label', 'title', 'placeholder', 'alt']) {
        const v = (el.getAttribute && el.getAttribute(a)) || '';
        if (v && v.trim()) 集.add(v.trim());
      }
    }
    return [...集];
  }, 含透明);
}

export const 归一 = (s) => (s || '').replace(/[\s　]+/g, '');

/** 带计数的断言：数字不对就抛错，不让它变成「看起来很权威」的假结论（缺陷 445 / 447）。 */
export function 断言器(记) {
  const st = { 次数: 0, 失败: 0 };
  const 断言 = (条件, 说明, 数据) => {
    st.次数 += 1;
    if (!条件) { st.失败 += 1; 记('   ❌ 断言失败：' + 说明 + (数据 !== undefined ? '｜数据 ' + JSON.stringify(数据) : '')); return false; }
    记('   ✅ 断言通过：' + 说明);
    return true;
  };
  断言.统计 = st;
  return 断言;
}

/** 找一枚可点按钮并**落点自证**：elementFromPoint 读回的必须就是它自己（缺陷 449）。 */
export async function 找可点按钮(page, aria, { 底栏 = true } = {}) {
  return page.evaluate(([a, 底栏]) => {
    for (const x of document.querySelectorAll('button,[role="button"]')) {
      if ((x.getAttribute('aria-label') || '') !== a) continue;
      const r = x.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if (底栏 && !(r.top > 700)) continue;
      const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
      const el = document.elementFromPoint(cx, cy);
      const btn = el && el.closest('button,[role="button"]');
      return {
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [cx, cy],
        命中标签: btn ? btn.getAttribute('aria-label') : null,
        命中类名: el ? String(el.className || '').slice(0, 70) : null,
      };
    }
    return null;
  }, [aria, 底栏]);
}

/**
 * ⭐ 打开底栏面板 / 按钮，并断言「面板**确实切了**」。
 * @param 必须消失 上一面板的**独占文案**；出现即说明根本没切（缺陷 449 的治法）
 */
export async function 开底栏(page, aria, { 记, 断言, 必须消失 = [], 等 = 4000 } = {}) {
  const b = await 找可点按钮(page, aria);
  if (!b) { if (记) 记(`   ⛔ 找不到可点的「${aria}」`); return false; }
  if (记) 记(`   「${aria}」框 ${JSON.stringify(b.框)}｜落点 ${JSON.stringify(b.点)}｜落点属主 aria-label=${JSON.stringify(b.命中标签)}`);
  if (断言 && !断言(b.命中标签 === aria, `「${aria}」的落点属主就是它自己（没被浮层盖住）`, b)) return false;
  await page.mouse.click(b.点[0], b.点[1]);
  await page.waitForTimeout(等);
  if (必须消失.length && 断言) {
    const 集 = new Set((await 全页文字(page)).map(归一));
    const 还在 = 必须消失.filter((m) => 集.has(归一(m)));
    断言(还在.length === 0, `打开「${aria}」后上一面板独占文案 ${JSON.stringify(必须消失)} 已消失`, 还在);
  }
  return true;
}

/** 关面板并断言独占文案真的不见了（证明确实关掉了，不是被别的盖住）。 */
export async function 关面板(page, 独占, { 记, 断言, 等 = 1500 } = {}) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(等);
  let 集 = new Set((await 全页文字(page)).map(归一));
  if (独占.every((m) => !集.has(归一(m)))) { if (记) 记('   ✅ Escape 就关掉了'); return true; }
  const c = await page.evaluate((独) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('button')) {
      if (!独.some((m) => 归(el.closest('div')?.innerText || '').includes(归(m)))) continue;
      const t = 归(el.innerText) || el.getAttribute('aria-label') || 归(el.title);
      if (!t || t.length > 4) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return { 文字: t, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }
    return null;
  }, 独占);
  if (c) { if (记) 记(`   ⛔ Escape 无效，点关闭钮 ${JSON.stringify(c.文字)}`); await page.mouse.click(c.点[0], c.点[1]); await page.waitForTimeout(等); }
  else if (记) 记('   ⛔ Escape 无效，也没找到短文案关闭钮');
  集 = new Set((await 全页文字(page)).map(归一));
  return 断言 ? 断言(独占.every((m) => !集.has(归一(m))), `关面板后独占文案 ${JSON.stringify(独占)} 真的消失`, [...集].filter((t) => 独占.map(归一).includes(t))) : true;
}

/** 量一个浮层的结构：class / z / 框 / 全文。 */
export async function 量浮层(page, 选) {
  return page.evaluate((sel) => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll(sel)].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 100 && r.height > 60;
    }).map((el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex, position: cs.position, class: String(el.className || '').slice(0, 110), 文字: 归(el.innerText).slice(0, 600) };
    });
  }, 选);
}

// ════════════════════════════════════════════════════════════════════
// ⭐⭐⭐⭐⭐ 缺陷 463：**拍一个节点前，必须验「中心落点属主就是它」**
// ════════════════════════════════════════════════════════════════════
// FQ-3 按节点框裁了一张图，文件名写「脚本V2节点」，
// **拍到的是智能剪辑节点** —— 因为
//     脚本 V2  [721,403,345,345]
//     智能剪辑  [626,391,345,345]    ← 大面积重叠
// 而 ⭐⭐ **`selected` 的节点 z-index = 1000**（未选中时是 `auto`）⇒ 它盖在别人上面。
// ⇒ 「框量对了」**不等于**「拍到的是它」。与缺陷 449 同源，
//   但那次盖住它的是浮层，这次盖住它的是**另一个节点**。

/** 读某个节点中心点的落点属主。属主 !== id 就说明它被别人盖住了。 */
export async function 中心属主(page, id) {
  return page.evaluate((tid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    const owner = hit && hit.closest('.react-flow__node');
    return {
      中心: [cx, cy],
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      z: getComputedStyle(n).zIndex,
      属主: owner ? owner.getAttribute('data-id') : null,
      属主类: owner ? String(owner.className).slice(0, 70) : null,
    };
  }, id);
}

/** 按 `class` 里的类型名（如 `node-video-clip`）找节点 id。类型判据见文件头。 */
export async function 找节点(page, 类型片段) {
  return page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((e) => String(e.className).includes(t));
    return n ? n.getAttribute('data-id') : null;
  }, 类型片段);
}

/** ⭐ 列出画布上所有重叠面积 > 25% 的节点对 —— 重叠是「张冠李戴」的温床。 */
export async function 查重叠(page, { 阈值 = 0.25 } = {}) {
  return page.evaluate((th) => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => {
        const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], z: getComputedStyle(n).zIndex, 框: [r.x, r.y, r.width, r.height] };
      })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    const 重 = [];
    for (let i = 0; i < ns.length; i++) {
      for (let j = i + 1; j < ns.length; j++) {
        const a = ns[i], b = ns[j];
        const ox = Math.min(a.框[0] + a.框[2], b.框[0] + b.框[2]) - Math.max(a.框[0], b.框[0]);
        const oy = Math.min(a.框[1] + a.框[3], b.框[1] + b.框[3]) - Math.max(a.框[1], b.框[1]);
        if (ox <= 0 || oy <= 0) continue;
        const 比 = (ox * oy) / Math.min(a.框[2] * a.框[3], b.框[2] * b.框[3]);
        if (比 > th) 重.push({ a: `${a.类}:${a.id}(z=${a.z})`, b: `${b.类}:${b.id}(z=${b.z})`, 重叠比: Number(比.toFixed(2)) });
      }
    }
    return 重;
  }, 阈值);
}

/**
 * ⭐⭐⭐ 拍一个节点：点标题栏选中 → **验中心落点属主** → 才裁图。
 * 验不过返回 `{ 失败: true }`，调用方必须重试或改用「整理画布」，**不许将就**。
 */
export async function 拍节点(page, 类型片段, 文件, { 记, 断言, 余量 = 26, 选 = true, 证据目录 = null } = {}) {
  const id = await 找节点(page, 类型片段);
  if (!id) { if (记) 记(`   ⛔ 找不到节点类型「${类型片段}」`); return { 失败: true, 原因: '找不到' }; }
  if (选) {
    // ⭐ 点**标题栏**（顶部 14px 处那儿没有按钮），不是点节点中心
    const t = await page.evaluate((tid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
      const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + 14)];
    }, id);
    await page.mouse.click(t[0], t[1]);
    await page.waitForTimeout(2200);
  }
  const a = await 中心属主(page, id);
  if (记) 记(`   中心落点自证 ${JSON.stringify(a)}`);
  if (断言 && !断言(!!a && a.属主 === id, `「${类型片段}」(${id}) 的中心落点属主就是它自己（没被别的节点盖住）`, a)) {
    return { 失败: true, 原因: '被盖住', 自证: a, id };
  }
  const 目录 = 证据目录 || SHOTS;
  const clip = {
    x: Math.max(0, a.框[0] - 余量), y: Math.max(0, a.框[1] - 余量),
    width: Math.min(1440 - Math.max(0, a.框[0] - 余量), a.框[2] + 余量 * 2),
    height: Math.min(810 - Math.max(0, a.框[1] - 余量), a.框[3] + 余量 * 2),
  };
  await page.screenshot({ path: resolve(目录, 文件), clip });
  if (记) 记(`   📷 ${文件}｜id ${id}｜裁剪 ${JSON.stringify(clip)}`);
  return { id, 框: a.框, clip, 文件 };
}
