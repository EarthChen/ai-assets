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

1. **调用点**（扫全部方法变体）：`MseConfigMessageSource#getMessage` / `#getMessageWithOutError`；`MultiLanguageService` 的 `getMseMessage`（String/Locale 多签名）/ `getMseMessageWithOutError` / `getMseMessageNotBlank` / `getAllMseMessage` / `getMsgMessageForLangNoError` / `getMsgMessageNoErrorRtCode`。
2. **间接 key**：常量（`XXX_MSG_KEY = "..."`）与枚举（`EcInfo.X.getEC()`——EC 数字串作 key，依赖 jar 里的枚举用 `javap -c -p` 看常量表取值）。diff 中新增常量/枚举后 grep 引用，确认其成为文案 key。
3. **动态命名 key**：档位 `warningMessageKey`（DB 配置引用）、数据驱动 `professionKey`——单列"动态命名，配置前须先在多语言平台建 key"。
4. **仓库内资源文件**：`i18nTag.json` 等多语言 JSON 资源的 diff 修改。
5. **修改与删除**：key 字符串变更（`^-` `^+` 成对）；调用删除（对应文案可能可下线，列为核对项）。

## 甄别陷阱

- **空 key 回落**：档位 `warningMessageKey` 为空回落默认弹窗——运营没建 key 不报错，但用户看到错文案；上线前必须确认 key 已建。
- **加载总开关**：`multilingual.autoload` 段属动态配置文档，但改它会导致全部文案加载失败——两份文档交叉提示。
