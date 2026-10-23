import Link from "next/link";

import { CLONE_PAGES, type ClonePageEntry } from "@/lib/clonePages";

/**
 * 1032-③：**克隆总览**（`/clones`）。
 *
 * ⭐⭐⭐⭐⭐ **这个页为什么存在**：站点的根路由 `/` 是 LibTV 画布本身，
 * ⇒ ⇒ ⇒ ⇒ ⇒ 而**即梦画布、FrameOS 画布、项目列表**这些同样是「已完成的克隆成果」
 * ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 却曾经只能靠手敲 URL 才走得到** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 * ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「做完了」不等于「走得到」**
 * ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**
 *
 * ⚠️ **它不手写任何清单**：下面的每一条都来自 `@/lib/clonePages` 这一份真源 ⇒
 * ⇒ ⇒ ⇒ ⇒ ⇒ 而 `scripts/jimeng_probe1033_clone_reachability.py` 会核
 * ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「页面 ↔ 真源 ↔ 文档」三处逐条对得上 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 */

function PageCard({ entry }: { entry: ClonePageEntry }) {
  return (
    <article
      data-clone-page-id={entry.id}
      className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-[#1d1d1d] p-5"
    >
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-lg font-medium text-[#f7f7f7]">{entry.name}</h2>
        <code className="rounded bg-white/[0.06] px-1.5 py-0.5 text-xs text-[#8c8c8c]">
          {entry.route}
        </code>
        <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] text-[#8c8c8c]">
          {entry.kind === "clone" ? "克隆成果" : "本站索引"}
        </span>
        <Link
          href={entry.route}
          data-clone-page-open={entry.id}
          className="ml-auto rounded-lg bg-[#2f2f2f] px-3 py-1.5 text-xs text-[#f7f7f7] hover:bg-[#3b3b3b]"
        >
          打开
        </Link>
      </header>

      <p className="text-sm leading-6 text-[#c9c9c9]">{entry.summary}</p>

      <dl className="grid gap-3 text-xs leading-5 text-[#a9a9a9] sm:grid-cols-2">
        <div>
          <dt className="mb-1 text-[#f7f7f7]">复刻对象</dt>
          <dd>{entry.product}</dd>
        </div>
        <div>
          <dt className="mb-1 text-[#f7f7f7]">从根目录怎么走到</dt>
          <dd>
            <ul className="list-disc space-y-0.5 pl-4">
              {entry.reachableVia.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </dd>
        </div>
        <div>
          <dt className="mb-1 text-[#f7f7f7]">怎么交互测试</dt>
          <dd>
            <ul className="list-disc space-y-0.5 pl-4">
              {entry.trySteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </dd>
        </div>
        <div>
          <dt className="mb-1 text-[#f7f7f7]">mock 边界（什么不能当真）</dt>
          <dd>{entry.mockBoundary}</dd>
        </div>
      </dl>

      {entry.manual ? (
        <p className="text-xs text-[#8c8c8c]">
          对应用户手册：<code className="text-[#c9c9c9]">{entry.manual}</code>
          （仓库内路径；手册本身也可构建成静态站点，见各手册目录的{" "}
          <code className="text-[#c9c9c9]">build-site.sh</code>）
        </p>
      ) : null}
    </article>
  );
}

export default function CloneIndexPage() {
  const clones = CLONE_PAGES.filter((p) => p.kind === "clone");
  const site = CLONE_PAGES.filter((p) => p.kind === "site");

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium text-[#f7f7f7]">克隆总览</h1>
        <p className="text-sm leading-6 text-[#a9a9a9]">
          本仓库已完成 {clones.length} 个克隆页面。它们都在站点根目录挂有入口，
          点下面的「打开」即可进入；每页都写明了从根目录怎么走到、可以怎么交互测试，
          以及哪些是 mock（不能当真）。
        </p>
        <p className="text-xs text-[#8c8c8c]">
          ⚠️ 全部生成、发布、会员、积分类入口都是原型态：点了只出本地状态提示，
          不发起任何真实请求、不消耗任何额度。
        </p>
      </header>

      <section className="flex flex-col gap-4">
        <h2 className="text-sm text-[#8c8c8c]">克隆成果（{clones.length}）</h2>
        {clones.map((entry) => (
          <PageCard key={entry.id} entry={entry} />
        ))}
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-sm text-[#8c8c8c]">本站</h2>
        {site.map((entry) => (
          <PageCard key={entry.id} entry={entry} />
        ))}
      </section>

      <footer className="mt-2 border-t border-white/10 pt-4 text-xs leading-5 text-[#8c8c8c]">
        本页内容全部来自{" "}
        <code className="text-[#c9c9c9]">src/lib/clonePages.ts</code>{" "}
        这一份真源；仓库根 <code className="text-[#c9c9c9]">README.md</code> 的路由表与{" "}
        <code className="text-[#c9c9c9]">docs/CLONE_PAGES_INDEX.md</code>{" "}
        都与它对账，由{" "}
        <code className="text-[#c9c9c9]">scripts/jimeng_probe1033_clone_reachability.py</code>{" "}
        这道门守着。
      </footer>
    </main>
  );
}
