# 示例：<分支名> 多语言文案变更清单

> 本示例随 skill 包自带；key 名为虚构工程示例值。受众：运营/翻译（多语言平台操作），产出 key + 各语言文案。

## 目的

梳理 <分支名> 对比 <基线> 的多语言文案新增与修改项，供多语言平台配置参考。

## 新增/修改 key

### 1. recheckNotPassNotice【新增】

使用方：`RescanService`（复审未通过官方号提示）。

| 语言 | 文案样例 |
|---|---|
| en | `Your message was removed after re-review.` |
| zh | `您的消息经复审未通过，已被移除。` |

### 2. 30084（EC = PLEASE_UPLOAD_REAL_PHOTOS）【新增】

使用方：`AlbumAuditService`；key 为 EC 数字字符串。

| 语言 | 文案样例 |
|---|---|
| en | `Your photo didn't pass review, please upload again.` |
| zh | `您上传的照片未通过审核，请重新上传。` |

### 3. 档位 warningMessageKey【新增，动态命名】

使用方：`WarningProxy#sendCustomWarningDialog`——档位配置（DB，admin 编辑）中的 `warningMessageKey` 字段值作为多语言 key。空值回落默认警告弹窗（运营没建 key 不报错，但用户看到错文案）。

档位样例（DB JSON）：

```json
{"hitCount": 3, "type": "MUTE_AND_FILTER", "durationType": "TWELVE_HOURS", "enableWarning": true, "warningMessageKey": "tierWarningThird"}
```

运营在多语言平台建 `tierWarningThird` 各语言文案。

## 仓库内多语言资源修改

- [ ] `src/main/resources/i18nTag.json`：新增 `id-ID` 的 t1/t2/t3 标签文案（diff 行级列出）。

## 核对项（基线沿用，勿重复配置）

- `20019` / `20020`：基线已在用，本分支仅扩展调用场景。
