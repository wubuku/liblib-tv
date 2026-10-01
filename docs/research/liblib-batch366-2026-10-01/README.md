# Batch 366 — 分镜脚本编辑器的「···」行操作是死的

## 怎么找到的

Batch 364 建的覆盖普查用 `data-*` 标记覆盖率衡量「这个面有没有被验证过」。
PARTIAL 名单里 `StoryboardScriptEditor` 漏了 `storyboard-row-menu` —— 逐个核实
时发现它不是「边缘标记」:

```tsx
<button type="button" data-storyboard-row-menu
  aria-label={`镜头${row.shot}操作`}
  className="rounded px-1.5 text-[#8c8c8c] hover:bg-white/[0.06]">···</button>
```

**无 onClick、无 disabled, 却带 `hover:bg-white/[0.06]`** —— 每行最右端的
操作入口, 视觉上明确在邀请点击, 点了什么都不发生。浏览器实测确认它真的
渲染出来了(x=1354, 25×28px, `aria-label="镜头1操作"`)。

## 判据的**上界**也要验证(本批最值得记的一点)

普查报「该组件漏 1 个标记」, 我第一反应是「那这个组件应该按钮很少,
影响有限」。**错了** —— `storyboard-row-menu` 是该组件里**唯一**带
`data-*` 标记的 `<button>`, 其余几十个按钮都没标记, 普查根本统计不到。

> **标记覆盖率能回答「哪些没被验证」, 不能回答「标记少 = 控件少」。**
> 判据的**下界**(漏报)我做了阳性/阴性双向自检, 这次发现**上界**也是坏的:
> 一个标记稀少的组件, 实际控件可能很多, 普查会让人低估它。
>
> 补法: 遇到「标记少」的组件, 顺手数一下真实控件数(`<button` / `role=button`),
> 两个数对不上就说明标记体系有洞 —— 那是**可测性债务**, 该补标记。

## 为什么之前没人发现

`storyboard-row-menu` 不在任何门禁的引用列表里。而打开这个编辑器的路径不平凡:
需要「添加节点 → script → script-new」新建一个剧本生成节点, 再点
「自己编写分镜脚本」—— **默认 fixture 里没有这样的节点**, 所以大多数门禁
连编辑器都进不去。

我第一次探测时 `data-script-generator-attempt` count = 0, 差点判成「不可达」。
翻 batch531 发现它有 `add_script_generator(page)` 这个 helper 在主动新建节点。
**别人的门禁里往往已经写好了正确的路径**, 先去找现成的, 别自己重造。

## 修法: 与 358/359/360/364 同策, 不发明

源站行操作菜单(复制/删除/重排)的具体项未采样(人机验证阻塞)。不擅自发明菜单,
按既定处置让 UI 停止撒谎: 去掉 `hover:bg-white/[0.06]` + `cursor: default` +
`title="行操作菜单暂不可用"` + `data-inert="true"` 自证惰性。几何与文案不动。

## 门禁 11 项, 其中一条是我自己补的漏洞

第一次写完跑出 5/8, 但有两条**判据本身是坏的**:

1. `row-menu:no-hover-affordance` 只查 `cursor` —— 而 cursor 本来就是
   `default`, 这条**恒绿**, 抓不住「把 hover:bg-* 加回去」。补了两条直接判据:
   - `row-menu:no-hover-background-rule`: 直接遍历 `document.styleSheets`,
     找匹配该元素且带 `:hover` + `background` 的规则;
   - `row-menu:class-has-no-hover`: 断 class 串里不含 `hover:`。
2. `cells:still-editable` 拿到 0 个 —— 因为 `data-storyboard-cell-input`
   **只在编辑态出现**(`StoryboardScriptEditor.tsx:56` 的 `if (editing)`),
   必须先点单元格。差点误判成「编辑器坏了」。

补完后 11/11。变异测试: 把 `hover:bg-white/[0.06]` 加回去 → exit=1, 精确红在
`row-menu:class-has-no-hover` —— **正是新补的那条抓到的**, 旧判据抓不到。

## 不过度拦截(反向验证)

`cells:typing-works`: 点开单元格、填入「冒烟」、读回一致 —— 证明我的
`data-inert` 没有波及同一行的正常输入交互。

> 只测「该红的红」不够, 还要测「不该被拦的没被拦」。这与 365 的
> `insideMenu` 判据是同一个道理: **过滤器必须双向验证**。
