# 多语言文案变更清单文档方法

完整示例随包自带：[../examples/multilang-changes.md](../examples/multilang-changes.md)。

背景：多语言文案经 yml `multilingual.autoload`（各服务 `config-key`，如 `amarmultipleMsg`）从 MSE 加载，运行时由 `MseConfigMessageSource` / `MultiLanguageService` 取文案；运营入口是**多语言平台**。与动态配置清单分开成文（受众 = 运营/翻译，产出 key + 各语言文案，不是 JSON）。

## 文档结构

```
# <分支名> 多语言文案变更清单
## 目的（表：key 来源 | 文案来源 | 语言要求 | 仓库资源文件）
## 一、新增/修改 key（主表：# | key | 变更类型 | 用途 | 配置字段或常量 | 可用参数 | zh | en | …）+ 说明表（使用方、缺失表现）
## 二、渲染规则（表：语言、回退、占位符、转义、测试环境）
## 三、需同步修改的 MSE 配置值（key 来自配置值时；表：字段 | 当前值 | 改为）
## 四、待确认项（表：问题 | 影响 | 需要）
## 五、核对项（表：沿用项与不在本清单的文案，附代码依据）
## 六、仓库内多语言资源修改（表：文件 | 修改）
```

不适用的节省略，余下各节按顺序重新编号。主体一律用表格：每个 key 一行，参数含义在主表前用一句话统一说明，行内只列可用参数编号。没有的语言填"待翻译"。

## 扫描步骤（逐仓库 `git diff <基线>...HEAD`）

1. **调用点（两层）**：
   - 直接层：`MseConfigMessageSource` 的 `getMessage` / `getMessageWithOutError` / `getAllMessages` / `getAllLanguageMessage`。
   - 封装层：注入了 `MseConfigMessageSource` 的封装类（各工程命名不一：`MultiLanguageService`、`MultiLangService` 等，已知方法含 `getMseMessage` 多签名 / `getMseMessageWithOutError` / `getMseMessageNotBlank` / `getAllMseMessage` / `getMultiLangMsg` / `getMseMessageNoError` / `getMessage` / `newBusinessException`）。**发现注入该 source 的新类，其 public 方法全部纳入**，勿只扫已知类名。
2. **间接 key（常量/枚举 + 参数值追踪）**：
   - 常量（`XXX_MSG_KEY = "..."`）与 EC 枚举，EC 来源两类：公共 `EcInfo`（依赖 jar，`javap -c -p` 看常量表取值，EC 数字串作 key）与服务自定义 `implements IEcInfo` 枚举（各工程 error/enums/common 包）。
   - 参数值追踪（调用未变但 key 取值变了）：字面量直接比对；变量追同方法/同类赋值；常量追定义；枚举追枚举定义；`@MomoConfig` 注入值追配置 key。
3. **特殊场景：MSE 配置值作多语言 key**——`@MomoConfig` 的值传入 `getMseMessage` 类方法使用；配置 key 从 v1 改 v2 时，确认 v2 的配置值包含新文案 key（与动态配置清单联动，两边都要出）。主表"配置字段"列写到字段路径（如 `xxx_multi_lang_config.advanceMsgKey`）；测试环境配置值与建议 key 名不一致时，出"需同步修改的 MSE 配置值"表，动态配置清单的样例同步改成建议名。
   - **参数对齐**：文案取自需求文档（`docs/design/requirement/**` 的 IM / 通知章节）；找不到时问用户，仍无来源的语言列填"待提供"。逐模板对照代码实际传入的 args（追到 `getMseMessage(key, lang, args)` 的 args 构造处），按代码的参数编号改写需求模板。需求里有、代码不传的部分：固定值（如比赛名称）写进模板，并检查共用同一模板 key 的实体能否区分，不能区分则拆 key；可变值（如赛道、等级组）写进待确认项，注明"改代码传参或产品接受"。
4. **返回前端的 key**：diff 新增的响应 DTO 字段名以 `Key` / `Keys` 结尾（如 `stageNameKey`、`ruleKeys`），值是多语言 key，由前端取文案。列入主表并在待确认项注明"前端取文案来源"；值来自配置字段而配置样例没配时，同时登记为漏配。
5. **动态命名 key**：档位 `warningMessageKey`（DB 配置引用）、数据驱动 `professionKey`——单列"动态命名，配置前须先在多语言平台建 key"。
6. **仓库内资源文件**：`i18nTag.json` 等多语言 JSON 资源的 diff 修改。
7. **修改与删除**：key 字符串变更（`^-` `^+` 成对）；调用删除（对应文案可能可下线，列为核对项）。

## 甄别陷阱

- **沿用判定精度**：常量在基线存在 ≠ 文案已配置——沿用条件是基线**已被传入文案方法**；预留未用的常量（定义了但从未传入）仍算新增。判定命令：`git show <基线>:<文件> | grep -E "(getMseMessage|getMessage|getMseMessageWithOutError).*<key>"`。
- **空 key 回落**：档位 `warningMessageKey` 为空回落默认弹窗——运营没建 key 不报错，但用户看到错文案；上线前必须确认 key 已建。
- **加载总开关**：`multilingual.autoload` 段属动态配置文档，但改它会导致全部文案加载失败——两份文档交叉提示。
- **回退语言**：读代码的回退逻辑（常见为用户语言 → `en`），回退语言的文案标为必配；回退也失败时的行为（不发送 / 告警 / 发 key）写进渲染规则表。
- **单引号转义**：带 args 渲染走 `MessageFormat`，`'` 是转义符，文案中的撇号写成 `''`（如 `You''ve`），否则后面的占位符不替换；花括号未闭合时渲染抛错。无 args 的调用原样返回文案，撇号写单个 `'`。按调用点是否传 args 逐 key 判定，写进主表或渲染规则表。
- **测试环境显示 key**：`application-test.yml` 的 `multilingual.autoload.use-code-as-default-message: true` 让缺失的 key 返回 key 本身，测试环境不出现"文案缺失"告警。启用时写进渲染规则表："测试环境看到 key 名即文案未配置"。
- **前端文案**：吸底、状态提示等页面文案先确认是否由服务端渲染。服务端只返回状态枚举与数值时，列入核对项"不在本清单"，并给出返回该枚举的类#方法作依据。

## 快照与自检

本文快照日期 2026-11-02。封装类方法名是各工程代码快照，偏移时更新：`rg -l "MseConfigMessageSource" --type java` 找新封装类，其 public 方法纳入检测；`rg -l "implements IEcInfo" --type java` 找新增错误码枚举。
