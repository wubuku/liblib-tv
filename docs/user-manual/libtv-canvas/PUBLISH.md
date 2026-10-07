# 发布：把手册变成可浏览的站点

> 面向**维护者**。如果你只是要读手册，看 [`README.md`](README.md) 就够了。

---

## 一句话版本

```bash
cd docs/user-manual/libtv-canvas
./serve.sh                    # 构建 + 本地预览 http://127.0.0.1:4189/
```

产物在 `.vitepress/dist/`，**整个目录拷到任意静态 Web 服务器就是发布完成**。

> ⭐ **`serve.sh` 才是日常用的启动方式。** `build-site.sh --preview` 也能起预览，
> 但它硬编码 4173，而且**端口撞了不会告诉你** —— 本仓库里多本手册并存，
> 4173 / 4188 都可能已经被别人占着。`serve.sh` 会打印是谁在占、并自动往后找空闲端口。
>
> ⛔ **4188 是 Flowable Trial 原站那本手册的**，打开它不是这一本。
> 先看标签页标题：LibTV 这本应该是「LibTV 画布用户手册」。

---

## 四个文件各管什么

| 文件 | 作用 | 什么时候改 |
|---|---|---|
| `package.json` | 只声明一个 devDependency：`vitepress` | 几乎不改 |
| `.vitepress/config.mjs` | 站点标题、侧边栏结构、搜索、发布排除项 | **加新页面时改这里** |
| `build-site.sh` | 六步构建 + 四道产物校验 | 加新门禁时改这里 |
| `serve.sh` | ⭐ **一键启动**：构建 + 起本地预览（默认 :4189），端口被占时自动避让 | 换默认端口时改这里 |
| `PUBLISH.md` | 本文件 | 换发布方式时改这里 |

新增一篇正文（比如 `10-tasks/xxx.md`）时，**必须同时**：

1. 在 `.vitepress/config.mjs` 的 `sidebar` 里加一条，否则第 6 步会 `FAIL`；
2. 在 `task-inventory.yml` 里登记，否则 Gate A 审计会拦下构建。

这是故意的：侧边栏漏收和账本漏登这两类问题，VitePress 自己不会报错，读者却只能靠页内链接抵达。

---

## 六步构建在做什么

| 步骤 | 内容 | 失败意味着 |
|---|---|---|
| 1/6 | 环境检查（node ≥ 18、config.mjs、README.md 存在） | 没装 Node，或站点文件被删了 |
| 2/6 | `npm install`（`node_modules/vitepress` 已存在则跳过） | 网络不通或 registry 不可达 |
| 3/6 | 统计页面/截图数 + **跑方法论的 Gate A 机械审计** | 手册本身先坏了（账本与正文对不上、图有裂的） |
| 4/6 | 清 `.vitepress/dist` 与 `.vitepress/cache` | — |
| 5/6 | `npx vitepress build` | 语法错误、配置写错 |
| 6/6 | 四道产物校验（见下） | 构建"成功"了但产物有问题 |

### 第 6 步的四道校验

| 校验 | 抓什么 | 为什么值得 |
|---|---|---|
| 无残留 `.md` 链接 | VitePress 没把某条 md 链接改写成 `.html` | 读者点过去是 404 |
| 侧边栏覆盖率 | 有页面没进 `config.mjs` | 导航形同虚设，build 不报错 |
| 产物无死链 | `href` 指向的 `.html` 在 dist 里真实存在 | **`srcExclude` 排掉的页面仍会被改写成 `.html`**，产物里会躺着指向 `AUDIT.html` 的死链 |
| 截图全部打包 | dist 里的 `.png` 数 == 源目录数 | 少一张通常意味着正文引用了不存在的图 |

> **关于 Gate A**：第 3 步调用的是方法论自带的
> `.agents/skills/web-studio-user-manual/scripts/audit_manual.py --phase gate-a`。
> 站点脚本**不重复实现**手册完整性校验 —— 两边各查一半、谁都不全，不如只留一处权威。
> 找不到该脚本时降级为 warn 而不是 fail（别人 clone 下来不一定带 `.agents/`）。

### 为什么不照抄 `tdcanvas-canvas/build-site.sh`

同仓的 `docs/user-manual/tdcanvas-canvas/build-site.sh` 已经长到 **12 道 Python 门禁**
（锚点校验、结构闭环、评级一致性、强断言、订正回归、账本锁定、门禁自检……），
依赖 `scripts/` 下十几个自建脚本，那是 100+ 批次逐步长出来的。

本手册还没有那些脚本，硬抄过来只会得到一个「第一步就找不到脚本」的构建。
所以这里只放**本目录真能跑**的四道校验。后续要加门禁，照着它的路子逐步加。

---

## 本地预览

```bash
./serve.sh                 # ⭐ 日常就用这个：构建 + 起 :4189
./serve.sh --no-build      # 改了正文想立刻看：不重新构建
./serve.sh --status        # 看跑没跑、在哪个端口
./serve.sh --stop          # 停掉
```

底层用的是 `python3 -m http.server`，**无缓存**，所以改完刷新就能看到，
**不需要重启预览进程**。

> ⚠️⚠️ **端口别搞混。** 本仓库里同时存在多本用户手册，每本都可能起着自己的预览：
>
> | 端口 | 是谁的 |
> |---|---|
> | **4189** | ✅ **LibTV 画布手册（本手册的默认端口）** |
> | 4188 | ⛔ Flowable Trial 原站手册 —— 打开它不是这一本 |
> | 4173 | `build-site.sh --preview` 硬编码的端口，撞了不报错 |
>
> 打开后先看标签页标题确认：LibTV 这本是「**LibTV 画布用户手册**」。

### 想要热更新（改 Markdown 即时刷新）

```bash
npx vitepress dev
```

> ⚠️ **别用 `./build-site.sh --preview`。**
> `vite preview`（含 `--preview`）底层是 sirv，**在启动时缓存文件清单**。
> 构建产物更新后（新增文件或改了哈希的资产），旧预览进程会对新文件返回 404。
> 诊断特征很典型：磁盘上文件存在、页面里引用的哈希也对得上，但 HTTP 就是 404。
> 规避办法就是用 `./serve.sh`（无缓存），或者开发时用上面的 `vitepress dev`。

---

## 发布到子路径

站点现在配的是 `base: '/'`，即挂在域名根下。如果要挂在
`https://example.com/manual/` 这样的子路径下：

1. 改 `.vitepress/config.mjs` 的 `base: '/manual/'`；
2. 重新 `./build-site.sh`；
3. 把 dist 部署到服务器的 `/manual/` 目录。

**改了 `base` 必须重新构建**，直接把现在这份 dist 丢到子路径下，所有资源链接都会 404。

---

## 发布到静态服务器

产物是纯静态的，没有后端依赖。用什么都可以：

```bash
# 1) 拷到服务器
rsync -avz --delete .vitepress/dist/ user@host:/var/www/manual/

# 2) 或者直接用任意静态托管（Nginx / Caddy / GitHub Pages / 对象存储 / CDN）
```

Nginx 最小配置：

```nginx
server {
  listen 80;
  server_name example.com;
  root /var/www/manual;
  index index.html;

  # 带 hash 的资源可以长缓存
  location /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

---

## 运维 FAQ

**Q：构建时卡在 `npm install`？**
首次构建要拉 vitepress，约 125 个包。网慢就多等；离线环境可以先在有网的机器上
`npm install` 再把 `node_modules/` 一起拷过去（它已在 `.gitignore` 里，不会进版本库）。

**Q：`dist` 里图片占了 12M，会不会太大？**
65 张 2× 截图。若要瘦身：

- 降到 1×（`tools/lib.mjs` 里的 `VIEWPORT` 加 `deviceScaleFactor: 1`）重新取证，体积约降 75%；
- 或在站点侧做 WebP 转换。

但 2× 是**必要的** —— 手册里很多图要靠放大看节点卡上的小字。

**Q：能不能只构建不发？**
能，`./build-site.sh` 不带 `--preview` 就只构建。产物在 `.vitepress/dist/`，
该目录已被 `.gitignore` 忽略，**不要提交进版本库**。

**Q：改了正文要重新构建吗？**
要。站点是构建期渲染的 Markdown，不重新构建的话 dist 里还是旧内容。

---

## 产物长什么样

| 指标 | 实测值 |
|---|---|
| 页面数 | 19（含 `index` 与 `404`） |
| 截图数 | 65（与源目录一致） |
| 总体积 | 约 12M |
| 搜索 | 本地 `provider: 'local'`，`⌘K` 唤起，**不依赖任何外部服务** |

站点只包含面向使用者的页面。`AUDIT.md` / `PROGRESS.md` / `PUBLISH.md`
由 `srcExclude` 排除，不进产物。
