# 示例：<分支名> 动态配置变更清单

> 本示例随 skill 包自带；key 名与字段为虚构工程示例值。结构：配置中心 key / yml 两节，每项为变更类型 + 样例 + 字段注释。

## 目的

梳理 <分支名> 对比 <基线> 的动态配置新增与修改项，供配置下发参考。

## 一、配置中心 key（@MomoConfig）

### 1. newStrategyGrayConfig【新增】

读取方：`pangu/NewStrategyGrayConfigProvider`（`@MomoConfig(key = "newStrategyGrayConfig", defaultVal = "{}")`）

样例：

```json
{
  "enabled": false,
  "testWhitelistUids": ["123456789"]
}
```

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| enabled | Boolean | false | true=新策略全量开启 |
| testWhitelistUids | Set&lt;String&gt; | 空集合 | enabled=false 时白名单 uid 放行；灰度外命中静默丢弃（无报错不落库） |

### 2. service-b.strategy_config【修改：新增 2 个子对象】

读取方：`pangu/StrategyConfigProvider#initStrategyConfig`（`@MomoConfig(key = "service-b.strategy_config")`）

样例（整包；须与既有字段合并下发，未带字段回退代码默认值）：

```json
{
  "newStrategyA": {"enabled": true, "whiteUserIds": [], "hitSessionCount": 3},
  "newStrategyB": {"enabled": true, "windowMinutes": 60, "minAppVersionCode": 0, "excludedOriginCodes": []}
}
```

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| newStrategyA.enabled / whiteUserIds | Boolean / Set | true / 空 | 继承 Strategy：enabled=false 时仅白名单参与 |
| newStrategyA.hitSessionCount | int | 3 | 命中会话数阈值 |
| newStrategyB.windowMinutes | int | 60 | 检测窗口长度（分钟） |
| newStrategyB.minAppVersionCode | int | 0 | 起始客户端版本码；≤0=版本门控未启用 |
| newStrategyB.excludedOriginCodes | Set&lt;String&gt; | 空集 | 空=默认排除集；非空=整表替换 |

## 二、yml / 环境项

### 3. audit.callback.url【新增】

读取方：`AuditPortImpl`（`@Value("${audit.callback.url:}")`）

样例：

```yaml
audit:
  callback:
    url: https://{domain}/service/xxx-callback?biz=album
```

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| url | String | 空串 | 审核回调地址；空=回调不可达，上线必配 |

### 4. multilingual.autoload.config-key【修改】

读取方：多语言加载框架（yml 段，当前值 `amarmultipleMsg`）。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| config-key | String | amarmultipleMsg | 多语言文案 MSE key；变更=全量文案迁移，须与多语言平台同步 |
| enable | Boolean | true | false=全部文案加载失败，运行时报错 |
