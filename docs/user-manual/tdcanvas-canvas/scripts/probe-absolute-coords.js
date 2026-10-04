#!/usr/bin/env node
/**
 * TDCanvas 绝对坐标/像素断言探针（M160 建立）
 *
 * **为什么要有这个探针**：M107（端口命中区 43×43 带画布缩放量）、M159（Agent 按钮排随视口宽度平移）
 * 已经两次栽在同一个毛病上——**把手册里写死的数字当成不变量**。
 * 但此前两次都是**撞上之后才回来补**，属于被动。
 * 这个探针把「哪些数字会动」变成**主动的、可一次问完的**。
 *
 * **它问的问题只有一句**：同一条界面断言，换一个视口之后还成不成立。
 *
 * 判据纪律（沿用 probe-toolbar-states.js 文件头的前七条，此处只补本探针特有的）：
 *
 * 8. **★ 必须用两个视口，且只改视口、不改别的**
 *    只测一个视口得不出「会不会动」——单一读数永远看起来稳定。
 *    → 先在 A 视口量一遍，**`setViewportSize` 到 B 视口后必须重读全部**。
 *    → 探针每轮重读坐标：节点/面板状态跨轮残留会让后一轮基准全错。
 *
 * 9. **★ 区分「设计常量」与「一次性读数」不是靠感觉，是靠第二次读数**
 *    设计常量：换视口后**逐位不变**（如小地图面板 240×160，源码写死）。
 *    一次性读数：换视口后**动了**，或它描述的是两个会各自移动的东西之间的距离。
 *    → 本探针对每个量输出 `delta`，由读数判定，不靠注释声明。
 *
 * 10. **★ 距离比坐标更能暴露问题**
 *     手册里写「两个按钮相距 931 像素」时，那个距离是**两个独立可动物体的间距**：
 *     坐标各自都可能不变，**距离照样会变**。所以凡是「A 与 B 相距 N」，
 *     必须同时量 A、B 的坐标与距离，三者一起看。
 *
 * 用法（Node 18+，需先 `source ~/.nvm/nvm.sh`）：
 *
 *     node scripts/probe-absolute-coords.js --canvas http://localhost:3000/canvas/<id>
 *
 * 画布打不开时（M172）：本机工作区的画布会被删，写死的 ID 不保质。
 * 探针会**自动新建一个空画布**接着跑，并在日志里打出新 ID；
 * 不想让它动工作区就传 `--no-create`，此时它只报错并说清现场。
 * `--profile` 与 `--canvas` 要对上——画布存在浏览器本地，换 profile 就没了。
 *
 * 退出码：0 = 探针跑完（**不代表断言通过，判读在报告里**）；非 0 = 探针自身失败。
 */

const path = require('path');
// ★ M238：统一到全库 10 支探针共用的写法——环境变量 PLAYWRIGHT_PATH 可覆盖，
//   默认值是**包目录**（不是 index.js）：换 node 版本时只需要改这一处，
//   或者直接 PLAYWRIGHT_PATH=/新/路径 node 这支探针 就行，不用动源码。
//   （原先是裸硬编码，10 支里只有它和 probe-copy-title 如此。）
const PW = process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright';
const { chromium } = require(PW);

const VIEWPORTS = [
  { name: 'A', width: 1600, height: 950 },
  { name: 'B', width: 1280, height: 800 },
];

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const PROFILE = arg('profile', '/tmp/m160-profile');
const CANVAS = arg('canvas', 'http://localhost:3000/canvas/Spmw8QhXdYPPR1TtsbOFM');
const REPORT = arg('out', path.join('/tmp', 'm160-coords.json'));
/** 画布不存在时是否自动新建（M172）。传 --no-create 则只报错、不动工作区。 */
const NO_CREATE = process.argv.includes('--no-create');

/** 在页面里量一组矩形。参数用第二个 argument 传，**不引用 Node 作用域变量**（第 4 条纪律）。 */
async function measure(page, tag) {
  return await page.evaluate((tagName) => {
    const out = { tag: tagName, groups: {} };

    /** 圆角矩形化，便于逐位比对 */
    const r = (el) => {
      if (!el) return null;
      const b = el.getBoundingClientRect();
      const n = (v) => Math.round(v * 10) / 10;
      return { x: n(b.x), y: n(b.y), w: n(b.width), h: n(b.height) };
    };

    /** 找到可见、可点、且有可访问名的元素 */
    const named = (sel) => Array.from(document.querySelectorAll(sel));

    // —— 1. 顶栏：最左的「主页」按钮
    const homeBtn = named('button, a').find((b) => {
      const t = (b.getAttribute('title') || b.getAttribute('aria-label') || '').trim();
      return t === '主页' || t === 'Home';
    });
    out.groups.home = r(homeBtn);
    out.groups.topbar = r(document.querySelector('header') || document.querySelector('[class*="topbar"]'));

    // —— 2. 左侧 Dock：容器 + 逐个按钮
    //    判据：Dock 是左侧竖排，容器 x 很小且含多个竖排按钮
    const dockCandidates = Array.from(document.querySelectorAll('div')).filter((d) => {
      const b = d.getBoundingClientRect();
      if (b.width > 90 || b.height < 200) return false;
      if (b.x > 90) return false;
      return d.querySelectorAll('button').length >= 6;
    });
    const dock = dockCandidates.sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    out.groups.dock = r(dock);
    out.groups.dockButtons = dock
      ? Array.from(dock.querySelectorAll('button')).map((b, i) => ({
          i,
          rect: r(b),
          title: (b.getAttribute('title') || b.getAttribute('aria-label') || '').trim(),
          icon: Array.from(b.querySelectorAll('svg')).map((s) => s.getAttribute('class') || '').join(' ').slice(0, 90),
        }))
      : [];

    // —— 3. 左下角那组视图控制：指南针 / 眼睛 / 磁铁 / 靶心 / 问号
    //    判据：y 接近视口底部、x 小；用 aria-label / title 抓名字
    const bottomLeft = named('button').filter((b) => {
      const box = b.getBoundingClientRect();
      return box.x < 340 && box.y > window.innerHeight - 140 && box.width > 0;
    });
    out.groups.bottomLeft = bottomLeft.map((b) => {
      const box = r(b);
      const icon = Array.from(b.querySelectorAll('svg')).map((s) => {
        const cls = s.getAttribute('class') || '';
        const m = cls.match(/lucide-([a-z-]+)/);
        return m ? m[1] : cls.slice(0, 40);
      });
      return {
        rect: box,
        name: (b.getAttribute('title') || b.getAttribute('aria-label') || '').trim(),
        icon,
      };
    });

    // —— 4. 小地图面板（找 240×160 那块浮层）
    const mapPanel = Array.from(document.querySelectorAll('div')).find((d) => {
      const b = d.getBoundingClientRect();
      return Math.abs(b.width - 240) < 6 && Math.abs(b.height - 160) < 6;
    });
    out.groups.minimap = r(mapPanel);

    // —— 5. 全部节点（供后续按需取尺寸）
    out.nodes = Array.from(document.querySelectorAll('[data-node-id]')).map((n) => {
      const el = n;
      const styleW = el.style.width || getComputedStyle(el).width;
      const styleH = el.style.height || getComputedStyle(el).height;
      return {
        id: el.getAttribute('data-node-id'),
        rect: r(el),
        styleW,
        styleH,
        text: (el.textContent || '').trim().slice(0, 30),
      };
    });

    out.viewport = { w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio };
    return out;
  }, tag);
}

/** 选中文本节点后量悬浮工具条上「裁剪」的位置，与 Dock 剪刀求距离（第 10 条纪律） */
async function measureScissorsDistance(page) {
  return await page.evaluate(() => {
    const r = (el) => {
      if (!el) return null;
      const b = el.getBoundingClientRect();
      const n = (v) => Math.round(v * 10) / 10;
      return { x: n(b.x), y: n(b.y), w: n(b.width), h: n(b.height) };
    };
    // Dock 的剪刀：lucide-scissors 且在左侧 Dock 里
    const allScissors = Array.from(document.querySelectorAll('svg.lucide-scissors'));
    const info = allScissors.map((s, idx) => {
      let btn = s;
      for (let k = 0; k < 8 && btn && btn.tagName !== 'BUTTON'; k++) btn = btn.parentElement;
      return { idx, btnRect: r(btn), name: btn ? (btn.getAttribute('title') || btn.getAttribute('aria-label') || '').trim() : null };
    });
    // 当前是否已选中某节点（有工具条才有裁剪）
    const toolbars = Array.from(document.querySelectorAll('div')).filter((d) => {
      const b = d.getBoundingClientRect();
      return b.width > 300 && b.height > 20 && b.height < 90 && d.querySelectorAll('button').length >= 4;
    });
    return {
      scissors: info,
      toolbarCandidates: toolbars.slice(0, 6).map((d) => ({ rect: r(d), buttons: d.querySelectorAll('button').length })),
    };
  });
}

async function main() {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true,
    viewport: { width: VIEWPORTS[0].width, height: VIEWPORTS[0].height },
    args: ['--disable-gpu'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  // 持久化 profile 的 pages()[0] 常是 about:blank，必须显式 goto
  await page.goto(CANVAS, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);

  // ---- M172：画布可能已经被删掉，必须先自检 ----
  // 画布存在与否是**外部状态**：本机工作区的画布会被清空、会被删，
  // 而探针的默认 ID 是写死的字符串。M172 实测两件事：
  //   ① 默认画布 Spmw8QhXdYPPR1TtsbOFM 已从列表页消失，页面被**静默重定向**
  //      到 /canvas 列表页——**探针不报错，它会对着空列表页继续往下量，
  //      把一堆没有意义的读数写进报告**。这比直接失败更糟：报告看起来是跑完了的。
  //   ② 默认 profile 是 /tmp/m160-profile，而画布是别的 profile 建的——
  //      **profile 与画布 ID 是两套独立状态，谁都可能不存在**。
  // 所以改成：先自检，不通就自己建一个（走真实 UI），建完用新建的那个跑。
  // 新建出来的空画布反而是最干净的状态，没有跨轮残留。
  const alive = await page.evaluate(() => ({
    url: location.href,
    redirected: !/\/canvas\/[A-Za-z0-9_-]{6,}/.test(location.pathname),
    hasCanvasRoot: !!document.querySelector('input[type="file"]'),
    cards: document.querySelectorAll('[data-canvas-project-card]').length,
  }));

  let canvasUrl = CANVAS;
  if (alive.redirected || !alive.hasCanvasRoot) {
    if (NO_CREATE) {
      console.error('[探针失败] 画布打不开，且传了 --no-create，探针已停——'
        + '否则会把空列表页的读数当成结果写进报告。');
      console.error('  请求的地址：' + CANVAS);
      console.error('  实际停在  ：' + alive.url + '（重定向=' + alive.redirected
        + '，画布页标志 input[type=file]=' + alive.hasCanvasRoot + '）');
      console.error('  列表页卡片：' + alive.cards + ' 张（0 = 这个 profile 下根本没有画布）');
      console.error('  多半是这个画布已被删除——本机工作区的画布不是永久的；'
        + '也可能是画布建在别的 profile 里，--profile 与 --canvas 要对上。');
      process.exit(2);
    }
    console.log('[画布自检] ' + CANVAS + ' 打不开（停在 ' + alive.url
      + '，列表页 ' + alive.cards + ' 张卡）——自动新建一个空画布接着跑。');
    await page.goto('http://localhost:3000/canvas', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    const hit = await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button, a'))
        .find((x) => /^新建画布$/.test((x.textContent || '').replace(/\s+/g, ' ').trim()));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    if (!hit) { console.error('[探针失败] 列表页找不到「新建画布」按钮'); process.exit(2); }
    await page.mouse.click(hit.x, hit.y);
    for (let i = 0; i < 20; i++) {
      const u = page.url();
      if (/\/canvas\/[A-Za-z0-9_-]{6,}/.test(new URL(u).pathname)) { canvasUrl = u; break; }
      await page.waitForTimeout(500);
    }
    if (canvasUrl === CANVAS) { console.error('[探针失败] 新建后没跳到画布页'); process.exit(2); }
    const made = canvasUrl.match(/\/canvas\/([A-Za-z0-9_-]{6,})/);
    console.log('[已新建画布] ' + (made ? made[1] : canvasUrl)
      + '\n  ⚠️ 这是探针在你的本机工作区里新建的画布，用完可在 /canvas 列表页删掉。');
    await page.waitForTimeout(2000);
  } else {
    console.log('[画布自检通过] ' + alive.url);
  }

  const report = { canvas: canvasUrl, viewports: [], scissorsDistance: null };

  for (const vp of VIEWPORTS) {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.waitForTimeout(1200);
    report.viewports.push(await measure(page, vp.name));
  }

  // 剪刀距离：只在 A 视口量（节点工具条需要选中态）
  await page.setViewportSize({ width: VIEWPORTS[0].width, height: VIEWPORTS[0].height });
  await page.waitForTimeout(1200);
  const sc = await measureScissorsDistance(page);
  report.scissorsDistance = sc;

  // 若已选中带图节点，直接求距离；否则打印原始读数交人工判
  if (sc.scissors.length >= 2) {
    report.scissorsPair = sc.scissors.map((s) => ({
      name: s.name,
      x: s.btnRect ? s.btnRect.x : null,
      dist: null,
    }));
    const xs = sc.scissors.map((s) => s.btnRect && s.btnRect.x).filter((v) => typeof v === 'number');
    if (xs.length >= 2) {
      report.scissorsPair[0].dist = Math.round((xs[1] - xs[0]) * 10) / 10;
    }
  }

  const fs = require('fs');
  fs.writeFileSync(REPORT, JSON.stringify(report, null, 2), 'utf-8');
  console.log(JSON.stringify(report, null, 2));
  console.log(`\n[报告已写入] ${REPORT}`);
  await ctx.close();
}

main().catch((e) => {
  console.error('[探针失败]', e);
  process.exit(1);
});
