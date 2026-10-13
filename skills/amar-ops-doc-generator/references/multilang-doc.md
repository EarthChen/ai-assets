# 多语言文案变更清单文档方法

完整示例随包自带：[../examples/multilang-changes.md](../examples/multilang-changes.md)。

背景：多语言文案经 yml `multilingual.autoload`（各服务 `config-key`，如 `amarmultipleMsg`）从 MSE 加载，运行时由 `MseConfigMessageSource` / `MultiLanguageService` 取文案；运营入口是**多语言平台**。与动态配置清单分开成文（受众 = 运营/翻译，产出 key + 各语言文案，不是 JSON）。

## 文档结构

```
# <分支名> 多语言文案变更清单
## 目的（一两行）
## 新增/修改 key
### <key>【新增|修改】使用方（类#方法）、样例（各语言文案）
## 仓库内多语言资源修改（i18nTag.json 等）
```

## 扫描步骤（逐仓库 `git diff <基线>...HEAD`）

1. **调用点（两层）**：
   - 直接层：`MseConfigMessageSource` 的 `getMessage` / `getMessageWithOutError` / `getAllMessages` / `getAllLanguageMessage`。
   - 封装层：注入了 `MseConfigMessageSource` 的封装类（各工程命名不一：`MultiLanguageService`、`MultiLangService` 等，已知方法含 `getMseMessage` 多签名 / `getMseMessageWithOutError` / `getMseMessageNotBlank` / `getAllMseMessage` / `getMultiLangMsg` / `getMseMessageNoError` / `getMessage` / `newBusinessException`）。**发现注入该 source 的新类，其 public 方法全部纳入**，勿只扫已知类名。
2. **间接 key（常量/枚举 + 参数值追踪）**：
   - 常量（`XXX_MSG_KEY = "..."`）与 EC 枚举，EC 来源两类：公共 `EcInfo`（依赖 jar，`javap -c -p` 看常量表取值，EC 数字串作 key）与服务自定义 `implements IEcInfo` 枚举（各工程 error/enums/common 包）。
   - 参数值追踪（调用未变但 key 取值变了）：字面量直接比对；变量追同方法/同类赋值；常量追定义；枚举追枚举定义；`@MomoConfig` 注入值追配置 key。
3. **特殊场景：MSE 配置值作多语言 key**——`@MomoConfig` 的值传入 `getMseMessage` 类方法使用；配置 key 从 v1 改 v2 时，确认 v2 的配置值包含新文案 key（与动态配置清单联动，两边都要出）。
4. **动态命名 key**：档位 `warningMessageKey`（DB 配置引用）、数据驱动 `professionKey`——单列"动态命名，配置前须先在多语言平台建 key"。
5. **仓库内资源文件**：`i18nTag.json` 等多语言 JSON 资源的 diff 修改。
6. **修改与删除**：key 字符串变更（`^-` `^+` 成对）；调用删除（对应文案可能可下线，列为核对项）。

## 甄别陷阱

- **沿用判定精度**：常量在基线存在 ≠ 文案已配置——沿用条件是基线**已被传入文案方法**；预留未用的常量（定义了但从未传入）仍算新增。判定命令：`git show <基线>:<文件> | grep -E "(getMseMessage|getMessage|getMseMessageWithOutError).*<key>"`。
- **空 key 回落**：档位 `warningMessageKey` 为空回落默认弹窗——运营没建 key 不报错，但用户看到错文案；上线前必须确认 key 已建。
- **加载总开关**：`multilingual.autoload` 段属动态配置文档，但改它会导致全部文案加载失败——两份文档交叉提示。

## 快照与自检

本文快照日期 2026-10-13。封装类方法名是各工程代码快照，偏移时更新：`rg -l "MseConfigMessageSource" --type java` 找新封装类，其 public 方法纳入检测；`rg -l "implements IEcInfo" --type java` 找新增错误码枚举。
