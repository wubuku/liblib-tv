/**
 * probe-storage-shape.js —— 读「画布数据到底落在哪、长什么样」。
 *
 * 复现的断言：
 *   ① 库 `tdcanvas` 里有哪几张表；`app_state` 里有哪几个键、每个键的 `state` 里有什么；
 *   ② **每一个**画布项目的字段清单（不是只看第一个）——`undo-persistence.md` 那句
 *      「一个画布项目在数据库里一共 12 个字段」就是靠这条读数；
 *   ③ `chatSessions` 到底是不是空的（M190 断言它一直是空的）；
 *   ④ 素材字节在 `image_files` / `media_files` 里，而不在 `app_state` 里。
 *
 * 用法：
 *   node scripts/probe-storage-shape.js http://localhost:3000/canvas/<id> [/tmp/m157-profile]
 *
 * ★ **只读。** 本探针只开 `readonly` 事务，不写、不删、不迁移版本。
 *
 * ══ 这一批实际栽过的四个坑，写在这里免得下一个人重犯 ══
 *
 * 1. ★ **`app_state` 存的是 JSON 字符串，不是对象。**
 *    第一版直接 `Object.keys(record)`，于是拿到的是 0..1487 这些**字符下标**——
 *    读数彻底是假的，输出还刷了两千多个下标。
 *    **先问「这条记录是什么类型」，再谈它有哪些字段。**
 *
 * 2. ★ **`getAll()` 不给键名。** 只给值。要核对手册里写的键名（`tdcanvas:canvas_store`）
 *    必须另外调 `getAllKeys()`，否则「键叫什么」只能靠猜。
 *
 * 3. ★ **只看第 0 条记录会得出「`state` 里没有 `projects`」这种结论。**
 *    `app_state` 里有**两条**记录：`tdcanvas:asset_store` 与 `tdcanvas:canvas_store`。
 *    第一条当然没有 projects——**一条记录不代表整张表**。
 *    「零结果先怀疑判据」：先把表里的记录全枚举出来再说话。
 *
 * 4. ★ **`indexedDB.open` 不指定版本会拿到当前版本；别顺手带上版本号去「确保一致」**——
 *    带了一个高于当前的版本号就会触发 `upgradeneeded`，而**只读探针不该改任何结构**。
 *    本探针干脆不传版本。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const URL = process.argv[2];
const PROFILE = process.argv[3] || '/tmp/m157-profile';
if (!URL) {
  console.error('用法：node scripts/probe-storage-shape.js <画布URL> [profile]');
  process.exit(2);
}
const say = (...a) => console.log(a.join(' '));

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 950 },
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 140)));
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);

  const out = await page.evaluate(async () => {
    const db = await new Promise((res, rej) => {
      // 坑 4：不传版本号，避免触发 upgradeneeded
      const r = indexedDB.open('tdcanvas');
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    const stores = Array.from(db.objectStoreNames);
    const read = (store, fn) => new Promise((res, rej) => {
      const tx = db.transaction(store, 'readonly');
      const rq = fn(tx.objectStore(store));
      rq.onsuccess = () => res(rq.result);
      rq.onerror = () => rej(rq.error);
    });
    const count = async (store) => {
      try { return await read(store, (os) => os.count()); } catch (e) { return '读取失败：' + e; }
    };

    let appRows = [];
    try {
      const keys = await read('app_state', (os) => os.getAllKeys());
      const vals = await read('app_state', (os) => os.getAll());
      appRows = vals.map((v, i) => {
        const rec = typeof v === 'string' ? JSON.parse(v) : v;   // 坑 1
        const st = (rec && typeof rec.state === 'object' && rec.state) || {};
        return { key: String(keys[i]), top: Object.keys(rec || {}), version: rec && rec.version, stateKeys: Object.keys(st) };
      });
    } catch (e) { appRows = [{ key: '读取失败', top: [], version: null, stateKeys: [] }]; }

    let projects = [];
    try {
      const rec = await read('app_state', (os) => os.get('tdcanvas:canvas_store'));
      const parsed = typeof rec === 'string' ? JSON.parse(rec) : rec;
      const list = (parsed && parsed.state && parsed.state.projects) || [];
      projects = list.map((p) => ({
        id: p.id, title: p.title,
        fields: Object.keys(p),
        n: Object.keys(p).length,
        nodes: Array.isArray(p.nodes) ? p.nodes.length : null,
        chatSessions: JSON.stringify(p.chatSessions),
        viewport: p.viewport ? Object.keys(p.viewport).join('/') : null,
      }));
    } catch (e) { projects = [{ id: '读取失败：' + e, fields: [], n: -1 }]; }

    const others = {};
    for (const s of stores) if (s !== 'app_state') others[s] = await count(s);
    return { stores, appRows, projects, others };
  });

  say('=== 库 tdcanvas 的表 ===');
  say('  ' + out.stores.join('、'));
  say('');
  say('=== app_state 的每一条记录（键名 + state 里的键） ===');
  out.appRows.forEach((r) => {
    say(`  键 ${r.key}`);
    say(`    顶层键：${r.top.join('、')}｜version=${r.version}`);
    say(`    state 的键：${r.stateKeys.join('、')}`);
  });
  say('');
  say('=== 每一个画布项目的字段（逐个核，不只看第一个） ===');
  if (!out.projects.length) say('  **一条都没读到**（不报 0）');
  const counts = new Set();
  out.projects.forEach((p) => {
    counts.add(p.n);
    say(`  ${p.title || '(无标题)'}（${p.id}）→ **${p.n} 个字段**｜节点 ${p.nodes} 个｜viewport=${p.viewport}`);
    say(`     ${p.fields.join('、')}`);
    say(`     chatSessions=${p.chatSessions}`);
  });
  say('');
  if (out.projects.length) {
    say(`  ★ 字段数取值集合 = ${JSON.stringify(Array.from(counts))}（只有一个值＝所有画布一致）`);
    say(`    手册与台账记的是 12 → ${counts.size === 1 && counts.has(12) ? '**逐个画布全部对上**' : '**对不上**'}`);
    say(`    chatSessions 全为空数组/空值 → ${
      out.projects.every((p) => /^(\[\]|null|undefined|"")/.test(p.chatSessions) || p.chatSessions === '')
        ? '**M190 那条「一直是空的」仍成立**' : '**有画布的 chatSessions 不是空的**'}`);
  }
  say('');
  say('=== 其余表（素材字节在这里，不在 app_state 里） ===');
  for (const [k, v] of Object.entries(out.others)) say(`  ${k}：${v} 条`);
  say('');
  say(`页面错误 ${errs.length} 个`);
  await ctx.close();
})().catch((e) => { console.error('探针崩了:', e); process.exit(1); });
