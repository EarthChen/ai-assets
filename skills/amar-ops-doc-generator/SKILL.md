---
name: amar-ops-doc-generator
description: 基于分支 diff 生成后门 bsh 测试、动态配置、多语言、Melon 四类上线配套文档。
disable-model-invocation: true
---

# 上线配套文档生成器（后门测试 / 动态配置 / 多语言 / Melon 配置）

四类文档四类读者：后门 bsh 测试脚本（测试执行）、动态配置变更清单（后端下发 MSE）、多语言文案变更清单（运营配置文案）、Melon 配置变更说明（运维配网关）。

## 文档类型路由

| 用户指定 | 方法文档 |
|---|---|
| 后门测试 / bsh 脚本 | [references/backdoor-bsh-doc.md](references/backdoor-bsh-doc.md) |
| 动态配置 / MSE key | [references/mse-config-doc.md](references/mse-config-doc.md) |
| 多语言 / 文案 key | [references/multilang-doc.md](references/multilang-doc.md) |
| melon / 网关 | [references/melon-config-doc.md](references/melon-config-doc.md) |
| 全量 | 全部 |

用户说"配置"而未细分时，生成动态配置 + 多语言两份（读者不同，各自成文）。未指定类型时先问。每类的完整示例随包自带（examples/，虚构工程示例值）。

## 输入

| 项 | 必填 | 说明 |
|---|---|---|
| 工程/分支 | 是 | 默认当前 worktree 各子仓库当前分支；多仓库结构，逐仓库 diff |
| 对比基线 | 否 | 默认 master |
| 业务上下文 | 否 | 链路/策略，影响后门脚本参数设计 |

## 工作流程

- [ ] Step 1 确认文档类型与目标分支
- [ ] Step 2 逐仓库 `git diff <基线>...HEAD` 扫描：只看 `^+`/`^-` 行（过滤 target/test）；每个候选 key（配置/文案/URI）用 `git grep <key> <基线>` 定论 **新增 / 修改 / 沿用**——只列前两类，把沿用误判为新增会造成误配（文案 key 的沿用须基线已被传入文案方法，常量存在不算，细则见各 reference）
- [ ] Step 3 按类型提取（调用链 / 配置绑定 / 文案 key / MOA URI），每项定位到源文件
- [ ] Step 4 照对应 reference 的结构模板与坑位清单撰写；后门脚本本地 bsh 双场景（原样 + 换行抹平）实测通过后才写入
- [ ] Step 5 写入目标模块 docs/（路径见下），向用户展示待人工确认项

## 输出路径

| 类型 | 默认路径 |
|---|---|
| 后门 bsh | `docs/guide/backdoor/<主题>-bsh.md` |
| 动态配置 | `docs/guide/config/<分支名>-mse-config-changes.md` |
| 多语言 | `docs/guide/config/<分支名>-multilang-changes.md` |
| Melon | `docs/changelog/release/<需求名>-release-checklist.md` 的 melon 节，或 `docs/guide/deployment/<分支名>-melon-config.md` |

默认约定；写入前先探测目标工程 docs/ 结构，按既有层级调整。

## 产出纪律

- 只列新增与修改项；每项三要素：变更类型 + 样例 + 注释（动态配置给字段表，多语言给各语言文案）。
- 样例数据用测试 uid。
- 待人工确认项用 `git blame` 定位变更行作者，作确认联系人。

## 边界

整体上线文档、发布顺序、SQL/Kafka/Cube → `release-doc-generator`。
