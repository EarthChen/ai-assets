# Melon 配置变更文档方法

完整示例随包自带：[../examples/melon-config.md](../examples/melon-config.md)。

## 概念

- Melon = 网关路由配置平台（`melon.wemomo.com`），为对外暴露的 MOA/HTTP 接口配置路由。
- 平台入口（线下/线上两环境，链接见下方模板，全文仅一份）。

## 扫描步骤（逐仓库 `git diff <基线>...HEAD`）

1. 新增 provider：diff 中 `+` 的 `@MoaProvider` 行与 `service_uri` / `SERVICE_URI` 常量（**两种大小写都要匹配**）。过滤 diff 文件头的写法：`git diff <基线>...HEAD | grep '^+' | grep -v '^+++'`——勿用 `'^\+[^+].*@Xxx'`（`[^+]` 吞掉 `+@MoaProvider` 的 `@` 后模式又要求再匹配一个 `@`，新增注解行全部漏报，已实测踩坑）。
2. 找对应接口方法：MOA 方法是 io/api 模块 interface 中的**普通 public 方法，无方法级注解**——从 `@MoaProvider` 实现类的 `implements` 接口定位方法清单；URI 常量在 interface（`String service_uri = "/service/..."`）或 `@MoaProvider(uri = ...)` 中。
3. 接口位置判定规则：
   - `**/interfaces/external/**`、`**/facade/external/**` → external 包 + `@MoaProvider`，需要 Melon 路由。
   - `**/internal/**` 下 Later 工单回调 → 走 HTTP 而非 MOA，按 HTTP 回调路由单列。
4. 修改类变更：既有 URI 的 io/api **interface 文件（diff M 状态）里 `+` 的方法签名** = 方法清单增删 → 归"修改"，写明新增/删除的方法名；接口注释 `@path /xx/yy` 即该方法的网关路径，新方法 = 新路径要补配。只扫 `@MoaProvider` 增删会漏掉这类（已实测踩坑）。
5. `spring.application.name` 从各服务 `application.yml` 取，用于拼后门/服务标识时交叉核对。

## 文档结构模板（checklist 节样式，团队惯称“melon 配置”）

```markdown
### 2.2 melon 配置

平台入口（两环境独立配置，链接全文仅此一份）：

- [ ] 线下：https://melon.wemomo.com/gateway/outRoute?corp=alpha&env=stage&tenant=ddoversea
- [ ] 线上：https://melon.wemomo.com/gateway/outRoute?corp=overseas&env=overseas&tenant=ddoversea

- [ ] /service/<uri>（新增 | 修改：新增方法 <m>）
  - 方法：<新增/全部方法名，逗号分隔>
```

独立文档时另加：目的、URI 总览表、每个 URI 的方法明细、配置风险、验收（MOA/HTTP 接口可正常访问）。

## 硬性风险

- **Melon 路由必须在服务部署前配置完毕，否则客户端调用 404**——文档首条风险，checkbox 未勾时禁止发版结论。
- 线下与线上是两个独立配置动作，在文档头部平台入口处分别勾选；**链接只保留这一份**，不为每个接口重复。
- 回调类（云审 callbackUrl、Later 工单）与 Melon 路由是两回事，不要混写；回调地址配置归动态配置清单。
- `internal/` 包 ≠ 免路由：调用方是外部系统（如审核方回调）时仍需网关暴露，internal 只指包组织位置。

## 验收

- [ ] melon 配置已生效，MOA/HTTP 接口可正常访问（线下先行）。

