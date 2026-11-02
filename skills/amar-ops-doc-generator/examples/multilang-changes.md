# 示例：<分支名> 多语言文案变更清单

> 本示例随 skill 包自带；key 名为虚构工程示例值。受众：运营/翻译（多语言平台操作），产出 key + 各语言文案。主体为表格。

## 目的

梳理 <分支名> 对比 <基线> 的多语言文案新增与修改项，供多语言平台配置参考。

| 项 | 说明 |
|---|---|
| key 来源 | 代码常量、EC 枚举、DB 档位配置字段 |
| 文案来源 | `docs/design/requirement/<需求>.md` 的通知章节（只有中文、英文） |
| 语言 | `en` 是回退语言，必须配置；其余语言待翻译 |
| 仓库资源文件 | `i18nTag.json` 有修改，见"五" |

## 一、新增/修改 key

参数说明：`{0}` 剩余次数。

| # | key | 变更类型 | 用途 | 来源 | 可用参数 | zh | en |
|---|---|---|---|---|---|---|---|
| 1 | `recheckNotPassNotice` | 新增 | 复审未通过官方号提示 | 常量 `RescanService.RECHECK_NOT_PASS_KEY` | - | `您的消息经复审未通过，已被移除。` | `Your message was removed after re-review.` |
| 2 | `30084` | 新增 | 相册审核失败提示（EC = `PLEASE_UPLOAD_REAL_PHOTOS`，key 为 EC 数字串） | `AlbumAuditService` | - | `您上传的照片未通过审核，请重新上传。` | `Your photo didn't pass review, please upload again.` |
| 3 | `tierWarningThird` | 新增（动态命名） | 第三档警告弹窗 | DB 档位配置 `warningMessageKey` | `{0}` | `您已第3次违规，剩余{0}次机会。` | `This is your 3rd violation. {0} chances left.` |

| 说明 | 内容 |
|---|---|
| 使用方 | #1 `RescanService#notifyNotPass`；#2 `AlbumAuditService#audit`；#3 `WarningProxy#sendCustomWarningDialog` |
| 动态命名 | #3 的 key 由档位配置（DB，admin 编辑）的 `warningMessageKey` 字段指定，配置前须先在多语言平台建 key。样例：`{"hitCount": 3, "type": "MUTE_AND_FILTER", "enableWarning": true, "warningMessageKey": "tierWarningThird"}` |
| 缺失表现 | #3 的 `warningMessageKey` 为空时回落默认警告弹窗：运营没建 key 不报错，但用户看到错误文案 |

## 二、渲染规则

| 规则 | 说明 |
|---|---|
| 语言回退 | 用户语言没有文案时回退 `en` |
| 单引号 | 带参数渲染的文案（#3）走 `MessageFormat`，撇号写成 `''`；无参数的文案（#1、#2）原样返回，撇号写单个 `'` |
| 测试环境 | `use-code-as-default-message: true`：key 缺失时显示 key 名 |

## 三、待确认项

| # | 问题 | 影响 | 需要 |
|---|---|---|---|
| 1 | 需求只给中文、英文 | 其他语言用户看到英文 | 翻译提供 ar、tr、id |

## 四、核对项（沿用，勿重复配置）

| 项 | 说明 |
|---|---|
| `20019` / `20020` | 基线已传入文案方法，本分支仅扩展调用场景 |

## 五、仓库内多语言资源修改

| 文件 | 修改 |
|---|---|
| `src/main/resources/i18nTag.json` | 新增 `id-ID` 的 t1/t2/t3 标签文案（diff 行级列出） |
