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

1. **新增绑定**：`+ @MomoConfig(key = "...")`（Provider 新增或绑定方法新增；注意 `@MomoConfig` 也可标注在方法上；`pangu/` 包是 Provider 惯例位置，里面用的就是 MSE，Pangu 只是内部叫法，勿当成另一系统）。
2. **Config 类变更**：绑定的 Config 类新增字段/内部类（key 不变 → 归"修改"）；已有字段**默认值修改**；`@MomoConfig` 的 `defaultVal` 变更。
3. **key 重命名/删除**：`^- @MomoConfig` 与 `^+ @MomoConfig` 成对出现 → 老配置失效，必须给迁移说明。
4. **yml 项**：`+ @Value("${...}")`；`multilingual.autoload.{enable,config-key}` 段变更（多语言文案加载总开关，改错=全部文案加载失败）。
5. **代码主动写配置**：diff 中新增 `PanguConfigHttpProvider#updateConfig` 之类调用（DB→MSE 同步通道）→ 列为配置写入路径变更。

## 甄别陷阱

- **整包 JSON key**：`@MomoConfig` 绑定整体 Config 类的，样例必须给**整包**，字段注释里注明"未带字段回退代码默认值"。
- **间接 key**：动态配置 key 一般是字面量；若经常量/枚举引用，先解引用再登记。
