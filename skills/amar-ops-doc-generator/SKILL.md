---
name: amar-ops-doc-generator
description: 生成上线配套文档：QA 后门/接口模拟、前端接口、动态配置、多语言、Melon 配置。
disable-model-invocation: true
---

# 上线配套文档生成器

## 文档类型

| 用户说 | 读者 | 方法文档 | 默认输出路径 |
|---|---|---|---|
| 后门测试 / bsh 脚本 / 接口模拟 | QA | [references/backdoor-bsh-doc.md](references/backdoor-bsh-doc.md) | `docs/guide/backdoor/<业务主题>-simulation.md` |
| 接口文档 / 前端对接 / 出入参 | 前端 | [references/api-doc.md](references/api-doc.md) | `docs/guide/api/<业务主题>-api.md` |
| 动态配置 / MSE / 盘古 key | 下发配置的后端 | [references/mse-config-doc.md](references/mse-config-doc.md) | `docs/guide/config/<分支名>-mse-config-changes.md` |
| 多语言 / 文案 key | 运营、翻译 | [references/multilang-doc.md](references/multilang-doc.md) | `docs/guide/config/<分支名>-multilang-changes.md` |
| melon / 网关路由 | 运维 | [references/melon-config-doc.md](references/melon-config-doc.md) | `docs/changelog/release/<需求名>-release-checklist.md` 的 melon 节，或 `docs/guide/deployment/<分支名>-melon-config.md` |

- "配置"未细分：动态配置 + 多语言两份，各自成文。
- "接口文档"读者不明（前端对接 / QA 模拟）、或未指定类型：先问。
- "全量"：全部类型。
- 输出路径是默认约定；写入前探测目标工程 `docs/` 的既有层级并对齐。

## 输入

| 项 | 默认 |
|---|---|
| 工程 / 分支 | 当前 worktree 各子仓库的当前分支；多仓库逐仓库处理 |
| 对比基线 | master |

各类型的专属输入（后门地址、网关域名、接口类、文案来源、appKey）见对应方法文档。

## 工作流程

- [ ] Step 1 确认文档类型、目标分支，读对应方法文档。
- [ ] Step 2 取材。diff 类文档（后门、动态配置、多语言、Melon）：逐仓库 `git diff <基线>...HEAD`，只看 `^+` / `^-` 行（过滤 target、test）；每个候选项（配置 key / 文案 key / URI）用 `git grep <key> <基线>` 定为**新增 / 修改 / 沿用**，只列前两类（沿用误判为新增会造成重复配置）。前端接口文档：按方法文档的取材步骤读指定接口类。每项定位到源文件。
- [ ] Step 3 按方法文档的结构模板与陷阱清单撰写。
- [ ] Step 4 交付：方法文档的自查项全部通过；文档写入 `docs/`；向用户列出待人工确认项，每项附 `git blame` 定位的变更行作者作联系人。

## 通用规则

- 样例数据用测试 uid。

## 边界

整体上线文档、发布顺序、SQL / Kafka / Cube 不在本 skill 范围内。
