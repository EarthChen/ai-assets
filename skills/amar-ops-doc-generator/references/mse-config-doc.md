# 动态配置变更清单文档方法（@MomoConfig / yml）

完整示例随包自带：[../examples/mse-config-changes.md](../examples/mse-config-changes.md)。

与多语言文案变更清单**分属两份文档**：受众、操作平台、下发时机均不同（本文件给下发配置的后端，多语言见 [multilang-doc.md](multilang-doc.md)）。

## 文档结构

```
# <分支名> 动态配置变更清单
## 目的（一两行：范围 + 基线）
## 测试环境链接（表：key | 命名空间 | 链接）
## 一、配置中心 key（@MomoConfig）——只列新增与修改项
### <mse key>【新增|修改】
- 链接 / 命名空间 / 读取方（Provider 类） / 样例（整包 JSON） / 字段注释表（字段|类型|默认值|说明）
## 二、yml / 环境项——只列新增与修改项
### <属性>【新增|修改】读取方、样例、字段注释
## 待人工确认项
## 下发核对（首次发布 + Provider 错误日志关键字）
```

每项三要素：**变更类型（新增/修改）+ 样例 + 字段注释**。不列沿用项；风险（整包替换、静默丢弃、空值不可达）压缩进字段注释。

## 链接与命名空间

每个 key 带自己的**测试环境链接**：取 `mse --region test --json share APPKEY KEY -n NS` 输出的 `url`（momo-tools，等同网页"分享"按钮，链接带 `configKey`；APPKEY 取服务 `src/main/resources/app.yaml` 的 `appKey`）。只放测试环境（alpha）一个链接。链接逐条取自命令输出，URL 参数的格式由 `mse share` 决定。key 尚未在 MSE 创建时 `share` 会拒绝，该行写"待创建"，创建后补链接。

命名空间逐 key 标注：已存在的 key 用 `mse --region test search KEY` 的 NameSpace 列；新 key 按用户指定（私有命名空间的 key 名与代码 `@MomoConfig(key = ...)` 全名一致，含前缀）。

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

- **整包 JSON key**：`@MomoConfig` 绑定整体 Config 类的，样例必须给**整包**，字段注释里注明"未带字段回退代码默认值"。重复列表（奖励表、板块、名次）只展开一项，样例标题标"结构示意"，其余字段照整包给。
- **校验静默失败**：Provider 在 `init()` / 反序列化失败时多为打 error 日志并保留旧配置，MSE 发布照样显示成功。把 `init()` 的校验规则逐条写进字段注释（它们是下发者真正的约束），并在"下发核对"列出 Provider 的 `log.error` 关键字。
- **新 key 首次发布**：`mse create` 或网页新建的 key 状态为"未生效"，没有发布记录、实例读不到；必须再发布一次（网页"发布"或用保存值 `mse publish`）。"下发核对"写明这一步。
- **间接 key**：动态配置 key 一般是字面量；若经常量/枚举引用，先解引用再登记。
- **下发时序（滚动发布兼容）**：key 重命名 v1→v2 不兼容（新实例读 v2、旧实例读 v1）——上线前 MSE 双 key 并存（内容一致），全量切换后删 v1；新增字段检查反序列化类是否有 `@JsonIgnoreProperties(ignoreUnknown = true)`，无则旧实例遇新字段反序列化失败，字段注释须标注。

## 快照与自检

本文快照日期 2026-11-02。Provider 不限路径、方法级 `@MomoConfig` 等是代码快照；怀疑偏移时 `rg "@MomoConfig" --type java` 全工程复核注册面。
