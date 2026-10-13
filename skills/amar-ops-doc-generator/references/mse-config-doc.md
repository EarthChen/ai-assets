# 动态配置变更清单文档方法（@MomoConfig / yml）

完整示例随包自带：[../examples/mse-config-changes.md](../examples/mse-config-changes.md)。

与多语言文案变更清单**分属两份文档**：受众、操作平台、下发时机均不同（本文件给下发配置的后端，多语言见 [multilang-doc.md](multilang-doc.md)）。

## 文档结构

```
# <分支名> 动态配置变更清单
## 目的（一两行：范围 + 基线）
## 一、配置中心 key（@MomoConfig）——只列新增与修改项
### <mse key>【新增|修改】
- 读取方（Provider 类） / 样例（整包 JSON） / 字段注释表（字段|类型|默认值|说明）
## 二、yml / 环境项——只列新增与修改项
### <属性>【新增|修改】读取方、样例、字段注释
```

每项三要素：**变更类型（新增/修改）+ 样例 + 字段注释**。不列沿用项；风险（整包替换、静默丢弃、空值不可达）压缩进字段注释。

## 扫描步骤（逐仓库 `git diff <基线>...HEAD`）

1. **新增绑定**：`+ @MomoConfig(key = "...")`（Provider 新增或绑定方法新增；`@MomoConfig` 也可标注在方法上；Provider 不限 `pangu/` 路径——`config/`、`provider/` 等任意位置，**全工程递归**；Pangu 只是 MSE 内部叫法，勿当成另一系统）。
2. **间接变更三场景**（grep `@MomoConfig` 行**不命中**，必须递归检查 Bean）：
   - A 嵌套类：绑定类型或其嵌套类新增/修改字段（key 不变 → 归"修改"）；已有字段**默认值修改**；`@MomoConfig` 的 `defaultVal` 变更。
   - B 回调反序列化：Provider 的 `value`/`onChange` 把 JSON 反序列化为**另一个** Config 类，该类字段变更。
   - C 配置驱动注册：diff 新增 Handler/策略类且经 `businessId`/`handlerName` 等配置驱动注册 → 须在既有 key 的 JSON 中**新增条目**。最隐蔽的漏配形态：代码上线、条目没加 → 新 Handler 静默不生效。文档中该 key 归"修改"并注明须新增的条目。
3. **key 重命名/删除**：`^- @MomoConfig` 与 `^+ @MomoConfig` 成对出现 → 老配置失效，必须给迁移说明。
4. **跨服务同 key 消费**：对每个检出 key 在**所有涉及工程**搜索 `@MomoConfig(key = "该key")`——同一 key 可能多个服务各自绑定 + 各自 Bean，改一边须列"受影响服务"全查，单服务视角会让另一消费方反序列化失败。
5. **yml 项**：`+ @Value("${...}")`；`multilingual.autoload.{enable,config-key}` 段变更（多语言文案加载总开关，改错=全部文案加载失败）。
6. **代码主动写配置**：diff 中新增 `PanguConfigHttpProvider#updateConfig` 之类调用（DB→MSE 同步通道）→ 列为配置写入路径变更。
7. **联动多语言**：检出 key 的 getter 被传入文案方法（`getMseMessage` 等）→ 该 key 的值本身是多语言 key，转多语言清单的"特殊场景"（见 [multilang-doc.md](multilang-doc.md)）。

## 甄别陷阱

- **整包 JSON key**：`@MomoConfig` 绑定整体 Config 类的，样例必须给**整包**，字段注释里注明"未带字段回退代码默认值"。
- **间接 key**：动态配置 key 一般是字面量；若经常量/枚举引用，先解引用再登记。
- **下发时序（滚动发布兼容）**：key 重命名 v1→v2 不兼容（新实例读 v2、旧实例读 v1）——上线前 MSE 双 key 并存（内容一致），全量切换后删 v1；新增字段检查反序列化类是否有 `@JsonIgnoreProperties(ignoreUnknown = true)`，无则旧实例遇新字段反序列化失败，字段注释须标注。

## 快照与自检

本文快照日期 2026-10-13。Provider 不限路径、方法级 `@MomoConfig` 等是代码快照；怀疑偏移时 `rg "@MomoConfig" --type java` 全工程复核注册面。
