#!/usr/bin/env python3
"""batch 853a 源站侦察：解掉剩下 3 层的**两种不同阻碍**，把真实结构 dump 出来。

§70 结尾留了 3 层没测到，原因**各不相同**，下一步动作也完全不同 —— 这一批就是
去把那两个动作**做出来**，好让下一批（853b）能正式取样：

  A. **音乐模型 / 音乐时长 —— 前置态没成立**。要切到「音乐生成」分支，但 851b
     用 `[role=option]:text-is("音乐生成")` **计数 0** ⇒ 切不过去。
     ⚠️ 关键问题不是「找不到」，而是**「凭什么判定它不在」**：`text-is` 只认
     文本**完全相等**的 role=option，源站这一层万一：文本带空白/图标/描述、
     根本不是 role=option、或者在**别的容器**里 —— 都会得到同一个「计数 0」，
     而「计数 0」被当成了「不存在」。
     ⇒ 这一段**不按 role 找**：打开「创作类型」层后，把层里**每一个**带可见
       文本的元素（按 z/尺寸排序，带 tag/role/class/aria/矩形）全 dump 出来，
       让人眼能看见「音乐生成」到底以什么形式存在（或确实不存在）。

  B. **音色库层 —— 判据量错对象**。851b 用矩形差分认层，抓到的是 648×1932 的
     **整页容器**（role='' z=auto）—— 那不是音色面板，是认层方法错了。
     ⚠️ 851b 已经写明「**不许放宽判据**，放宽只会把伪像洗成结论」。这一段遵守：
     **不猜**它是哪个 class，而是打开它之后把**新增的**元素按 z-index + 面积
     排序全 dump，**让证据自己说出**哪一层才是音色面板（z 最高的、面积像面板的、
     带音色条目的那个）。如果 dump 完发现**根本没有**独立面板（音色库就地展开），
     那也是结论 —— 记「前置态/夹具」而不是硬凑。

只 dump，不改产品；不点任何付费动作（生成/发送/购买/充值）。
"""

import json
import sys
from pathlib import Path

# 注入的全局有 page（jimeng_headless.py run 模式）
# 计费护栏：只点下拉触发器，**绝不**点生成/发送/购买/充值/订阅。
BILLED = ("生成", "发送", "购买", "充值", "立即支付", "订阅", "开通", "兑换",
          "立即生成", "开始生成")


def guard(label):
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED or base in BILLED or any(t.startswith(b) for b in ("立即", "购买", "充值")):
        print(f"   🛑 拦下付费动作 {t!r}")
        return True
    return False


# 把整页（或某个根）里**所有带可见文本的元素** dump 出来，按 (z, 面积) 排序。
# 故意**不按 role 筛** —— 这是 A 段存在的全部理由。
DUMP_TEXTY_JS = r"""(rootSel) => {
  const root = rootSel ? document.querySelector(rootSel) : document.body;
  if (!root) return [];
  const out = [];
  for (const e of root.querySelectorAll('*')) {
    const txt = (e.innerText || '').trim();
    if (!txt) continue;
    // 只要**自己这一层**的文本（不含子孙的），否则每个祖先都会重复报一遍
    const own = [...e.childNodes]
      .filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').trim();
    if (!own) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    out.push({
      tag: e.tagName,
      role: e.getAttribute('role') || '',
      cls: (e.className || '').toString().replace(/\s+/g, ' ').slice(0, 60),
      aria: e.getAttribute('aria-label') || '',
      own_text: own.slice(0, 40),
      rect: [Math.round(r.x), Math.round(r.y),
             Math.round(r.width), Math.round(r.height)],
      z: s.zIndex,
      area: Math.round(r.width * r.height),
    });
  }
  out.sort((a, b) => (parseInt(b.z) || 0) - (parseInt(a.z) || 0)
                 || b.area - a.area);
  return out;
}"""

# 新增元素：开前后按「一个稳定签名」做差 —— 这里用
# (tag, class 前 40, 圆角矩形) 当签名，比纯矩形稳，也比 testid 通用。
SIGN_JS = r"""() => {
  const sigs = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;      // 忽略不可见的小碎片
    const cls = (e.className || '').toString().replace(/\s+/g, ' ').slice(0, 40);
    const key = [e.tagName, e.getAttribute('role') || '', cls,
                 Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)].join('|');
    sigs.add(key);
  }
  return [...sigs];
}"""


def select_audio_node():
    """插一个音频节点，返回 testid；插不出返回 None。

    ⚠️⚠️ batch 853 第一版栽在这里，而且栽法很典型：第一版只查了一次
    `button[aria-label="音频"]`，查不到就直接判 `no_audio_node`。但 **851a 明明
    插出过** ⇒ 「这一次查不到」**不能**推出「夹具不具备」。两种可能：
      ① 画布/左栏还没渲染完（冷启动 race）—— 源站这种重页面很常见；
      ② 按钮的 aria-label 变了。
    所以这一版：先 dump 左栏**到底有哪些按钮**（把「按钮不存在」和「按钮叫别的
    名字」区分开），再带**重试 + settle 等待**去插入。**没插出 ≠ 夹具不具备**，
    前者要交出「我够得着吗」的证据，后者才记 BLOCKED_BY_FIXTURE。
    """
    page.set_viewport_size({"width": 1512, "height": 1200})
    # 等画布真的挂上节点（冷启动 race）
    for _ in range(20):
        n = page.evaluate(
            "() => document.querySelectorAll('.react-flow__node').length")
        if n:
            break
        page.wait_for_timeout(700)
    page.wait_for_timeout(800)

    # 先把左栏真实有哪些入口 dump 出来 —— 区分「没有音频」和「不叫音频」
    rail = page.evaluate("""() => {
      const out = [];
      for (const b of document.querySelectorAll('button,[role=button]')) {
        const r = b.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) continue;
        out.push({al: b.getAttribute('aria-label') || '',
                  txt: (b.innerText || '').trim().slice(0, 12),
                  r: [Math.round(r.x), Math.round(r.y),
                      Math.round(r.width), Math.round(r.height)]});
      }
      return out;
    }""")
    print(f"== 左栏可见按钮 {len(rail)} 个 ==")
    labels = sorted({(c["al"] or c["txt"]) for c in rail if (c["al"] or c["txt"])})
    print("  ", labels)

    for attempt in range(3):
        picked = None
        for cand in ('button[aria-label="音频"]', 'button:has-text("音频")',
                     '[aria-label*="音频"]'):
            loc = page.locator(cand)
            if loc.count():
                picked = (cand, loc)
                break
        if not picked:
            print(f"   [试{attempt + 1}] 左栏里**没有**音频入口 ⇒ 夹具不具备")
            return None
        cand, loc = picked
        print(f"== [试{attempt + 1}] 用 {cand} 插入 ==")
        before = set(page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')"))
        try:
            loc.first.click(timeout=10000)
        except Exception as e:  # noqa: BLE001
            print(f"   点击异常：{str(e)[:80]}")
            continue
        page.wait_for_timeout(3000)
        after = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        print(f"   新增节点：{new}")
        if new:
            return new[0]
        print("   点完没新节点 ⇒ 重试")
    print("   试了 3 次都插不出 ⇒ 夹具不具备（BLOCKED_BY_FIXTURE）")
    return None


def click_node(tid):
    pt = page.evaluate("""(tid) => {
      const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                              [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
        const x = r.x + r.width*fx, y = r.y + r.height*fy;
        const t = document.elementFromPoint(x, y);
        if (t && n.contains(t) && !t.closest(CTRL)) return [Math.round(x), Math.round(y)];
      }
      return null;
    }""", tid)
    if not pt:
        return False
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(1200)
    return page.evaluate(
        "() => document.querySelectorAll('.react-flow__node.selected').length") == 1


report = {}
# ⚠️⚠️ batch 853 第二版补的关键一步：**探针必须自己 goto 画布 URL**。
#    第一版忘了这行，`run` 模式把页面留在 runner 的默认页（首页/推广弹层），
#    于是左栏 dump 出来全是「电影级长镜头运镜 / 打开画布 / 新建画布」——
#    那是**首页**，不是画布编辑器，自然没有「音频」入口。
#    ⚠️ 教训跟 843/851 一脉相承：**「我没检测到」必须先确认「我够得着」** ——
#    这一版甚至不是够不着，是**根本没去那个页面**。851a/851b/852 都自带 goto，
#    是我抄漏了。凡是 `run` 模式的源站探针，**第一件事就是 goto 画布**。
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
# 与 850/851/852 同口径：面板挂在节点下方，950 高的视口点不到触发器
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print(f"== 当前 URL: {page.url} ==")
report["url"] = page.url

print("\n########## A. 「创作类型」下拉：音乐生成到底在不在、什么形态 ##########")
tid = select_audio_node()
if not tid:
    print("!! 这一版画布**插不出**音频节点 ⇒ A/B 两条都 BLOCKED_BY_FIXTURE")
    report["verdict"] = "no_audio_node"
else:
    report["audio_tid"] = tid
    print(f"== 音频节点 {tid} ==")
    if not click_node(tid):
        print("!! 选不中音频节点")
        report["verdict"] = "cannot_select"
    else:
        # 打开「创作类型」层
        trig = page.locator('button[aria-label^="创作类型"]')
        print(f"== 「创作类型」触发器 {trig.count()} 个 ==")
        if not trig.count():
            report["verdict"] = "no_gen_type_trigger"
        else:
            al = trig.first.get_attribute("aria-label") or ""
            if guard(al):
                report["verdict"] = "guarded"
            else:
                trig.first.click(timeout=8000)
                page.wait_for_timeout(900)
                # 找到刚刚打开的浮层容器：取 z 最高的、含「生成」二字的近祖
                dump_all = page.evaluate(DUMP_TEXTY_JS, None)
                # 只保留和「生成/音乐/音频/配音/朗读」相关的行 + 最高 z 若干行
                rel = [d for d in dump_all
                       if any(k in (d["own_text"] + d["aria"])
                              for k in ("生成", "音乐", "音频", "配音", "朗读", "类型"))]
                topz = dump_all[:12]
                print(f"== 全页带文本元素 {len(dump_all)} 个；"
                      f"相关 {len(rel)} 个；z 最高 12 个： ==")
                for d in topz:
                    print(f"   z={d['z']:>5} area={d['area']:>7} "
                          f"<{d['tag']} role={d['role']!r}> "
                          f"rect={d['rect']} own={d['own_text']!r} "
                          f"aria={d['aria']!r}")
                print("== 相关行（按 z/面积）==")
                for d in rel:
                    print(f"   z={d['z']:>5} <{d['tag']} role={d['role']!r} "
                          f"cls={d['cls'][:36]!r}> rect={d['rect']} "
                          f"own={d['own_text']!r} aria={d['aria']!r}")
                report["A_createtype"] = {
                    "n_texty": len(dump_all), "n_rel": len(rel),
                    "top_z": topz, "relevant": rel,
                }
                # 明确回答：有没有任何元素的文本含「音乐」
                music = [d for d in dump_all if "音乐" in (d["own_text"] + d["aria"])]
                report["A_has_music"] = len(music)
                print(f"\n== 含「音乐」二字的元素：{len(music)} 个 ==")
                for d in music:
                    print(f"   z={d['z']} <{d['tag']} role={d['role']!r}> "
                          f"own={d['own_text']!r} aria={d['aria']!r} rect={d['rect']}")
                # 关掉这一层（点触发器或按 Esc，尽力）
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)

        # ── B. 音色库层：认层方法错了，这次让证据自己说 ──────────────────
        print("\n########## B. 「音色: 音色库」层：真正的面板是哪一块 ##########")
        if not click_node(tid):
            print("!! 重新选不中音频节点")
            report["B"] = "cannot_reselect"
        else:
            btrig = page.locator('button[aria-label^="音色"]')
            print(f"== 「音色」触发器 {btrig.count()} 个 ==")
            if not btrig.count():
                report["B"] = "no_voice_trigger"
            else:
                bal = btrig.first.get_attribute("aria-label") or ""
                if guard(bal):
                    report["B"] = "guarded"
                else:
                    before_sigs = set(page.evaluate(SIGN_JS))
                    btrig.first.click(timeout=8000)
                    page.wait_for_timeout(1000)
                    after_dump = page.evaluate(DUMP_TEXTY_JS, None)
                    after_sigs = set(page.evaluate(SIGN_JS))
                    # 新增的、带文本的元素里，跟音色相关的 + z 最高的
                    new_txt = [d for d in after_dump
                               if f"{d['tag']}|{d['role']}|{d['cls']}|"  # 粗略找新增
                               not in "" and d["area"] > 2000]
                    voice_rel = [d for d in after_dump
                                 if any(k in (d["own_text"] + d["aria"])
                                        for k in ("音色", "发音", "童声", "男", "女",
                                                  "情感", "语速", "库"))]
                    print(f"== 开层后带文本元素 {len(after_dump)} 个 ==")
                    print(f"== 音色相关 {len(voice_rel)} 个（按 z/面积）==")
                    for d in voice_rel[:20]:
                        print(f"   z={d['z']:>5} area={d['area']:>7} "
                              f"<{d['tag']} role={d['role']!r}> rect={d['rect']} "
                              f"own={d['own_text']!r} aria={d['aria']!r} "
                              f"cls={d['cls'][:40]!r}")
                    topb = after_dump[:15]
                    print("== z 最高 15 个（找「真正的面板」）==")
                    for d in topb:
                        print(f"   z={d['z']:>5} area={d['area']:>7} "
                              f"<{d['tag']} role={d['role']!r}> rect={d['rect']} "
                              f"own={d['own_text']!r} cls={d['cls'][:44]!r}")
                    report["B_voicelib"] = {
                        "n_texty": len(after_dump),
                        "n_voice_rel": len(voice_rel),
                        "voice_rel": voice_rel[:20],
                        "top_z": topb,
                    }

with open("/tmp/b853a-source-audiostruct.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("\n== 已写 /tmp/b853a-source-audiostruct.json ==")
print("== 结论摘要 ==")
print(f"   A 含「音乐」元素数: {report.get('A_has_music', 'N/A')}")
print(f"   B 音色相关元素数: {report.get('B_voicelib', {}).get('n_voice_rel', 'N/A')}")
