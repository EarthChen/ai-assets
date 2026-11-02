# 示例：签到活动前端接口文档

> 本示例随 skill 包自带；接口、字段与值为虚构工程示例值。结构：总览 / 通用约定 / 接口详情（每个接口：入参表、入参样例、出参表、出参样例）/ 公共类型 / 注意事项。

## 目的

供前端对接签到活动查询接口。来源：`SignInMoaWebService`（MOA `/service/demo/activity/sign-in`）。服务端只返回数据与状态，展示文案由前端决定。样例中的值均为示例值。

## 一、接口总览

| # | 接口 | path | 说明 |
|---|---|---|---|
| 1 | [getSignInInfo](#1-getsignininfo签到信息) | `/doversea/activity/sign-in/getSignInInfo` | 签到信息 |
| 2 | [getSignInRank](#2-getsigninrank签到榜) | `/doversea/activity/sign-in/getSignInRank` | 连续签到榜 |

调用顺序：签到信息（取 `defaultDay`）→ 签到榜。

## 二、通用约定

### 公共入参（header）

| 字段 | 说明 |
|---|---|
| uid | 当前用户，由网关从 header 填充。为空时返回 `30043` |
| lang | 用户语言 |

### 出参外层

```json
{"ec": 0, "em": "", "traceId": "…", "data": {}}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| ec | int | `0` 成功 |
| em | String | 错误码对应的多语言提示 |
| traceId | String | 链路 id |
| data | Object | 各接口出参 |

出参类带 `@JsonInclude(NON_NULL)`：null 字段不下发，下文记为"缺失"。

### 错误码

| ec | 含义 | 触发条件 |
|---|---|---|
| 0 | 成功 | - |
| 30043 | 参数错误 | uid 为空；`day` 不在 1~7 |
| 700015 | 活动信息不存在 | 活动配置未加载 |

```json
{"ec": 30043, "em": "<30043 的多语言提示>", "traceId": "…"}
```

### 枚举取值

| 名称 | 取值 |
|---|---|
| 状态 status | `NOT_STARTED`、`ONGOING`、`ENDED` |

## 三、接口详情

### 1. getSignInInfo（签到信息）

path：`/doversea/activity/sign-in/getSignInInfo`

**入参**：只有公共入参，body 为空对象。

```json
{}
```

**出参**：`SignInInfoResp`

| 字段 | 类型 | 说明 |
|---|---|---|
| status | String | 活动状态 |
| defaultDay | Integer | 默认选中的天：进行中为今天，结束后为 7 |
| signedDays | List&lt;Integer&gt; | 已签到的天 |
| countdownMillis | Long | 距活动结束毫秒数；已结束时缺失 |

**出参样例**（进行中）：

```json
{"ec": 0, "data": {"status": "ONGOING", "defaultDay": 3, "signedDays": [1, 2], "countdownMillis": 3600000}}
```

### 2. getSignInRank（签到榜）

path：`/doversea/activity/sign-in/getSignInRank`

**入参**：`SignInRankReq`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| day | Integer | 否 | 第几天（1~7）。不传取默认天；越界返回 30043 |

```json
{"day": 3}
```

**出参**：`SignInRankResp`

| 字段 | 类型 | 说明 |
|---|---|---|
| day | Integer | 所查天 |
| list | List&lt;[SignInUserDTO](#signinuserdto签到用户)&gt; | 前 100 名 |
| mine | [SignInUserDTO](#signinuserdto签到用户) | 我的行；未签到时缺失 |

**出参样例**（我未签到）：

```json
{"ec": 0, "data": {"day": 3, "list": [{"rank": 1, "uid": "1001", "avatar": "https://…", "userName": "User A"}, {"rank": 2, "needHideRank": true}]}}
```

## 四、公共类型

### SignInUserDTO（签到用户）

| 字段 | 类型 | 说明 |
|---|---|---|
| rank | Long | 名次，从 1 开始 |
| uid / avatar / userName | String | 用户信息 |
| needHideRank | Boolean | 神秘人 |

| 场景 | 返回 | 前端展示 |
|---|---|---|
| 神秘人 | 只有 `rank` 与 `needHideRank=true` | 神秘人头像、昵称 |
| 展示信息加载超时 | 只有 `rank` | 占位 |

## 五、前端注意事项

| 场景 | 处理 |
|---|---|
| 字段缺失 | null 字段不下发 |
| 切换天 | 只用 1~7，其他值返回 30043 |
