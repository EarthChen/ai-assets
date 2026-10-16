# 示例：命中模拟指南（QA 版）

> 本示例随 skill 包自带，展示 QA 版后门/接口模拟文档的完整形态。类名、bean 名、域名、后门地址均为虚构示例值，使用时替换为目标工程的真实值。

手动触发命中，验证“命中 → 落库 → 自动处理”。本文每个功能只回答三件事：什么时候用、参数怎么填、怎么看结果。

## 先读这里

1. **测试 uid 必须是目标用户类型**。不符合的 uid 会被静默跳过（返回成功，但不落库）。
2. **测试 uid 必须在新策略灰度内**：配置 `newStrategyGrayConfig` 中 `enabled=true`，或 uid 在 `testWhitelistUids` 里。灰度外的命中被静默丢弃，表现为“发送成功但无数据”。
3. **命中会触发真实处理**。线上只用测试 uid。
4. 后门脚本在对应服务的后门页面执行：入参 `code` 填脚本全文，脚本最后一行的值是返回值。

   | 服务 | 后门地址 | 执行的脚本 |
   |---|---|---|
   | service-a | https://backdoor.example.com/a | 脚本 A |
   | service-b | https://backdoor.example.com/b | 脚本 B、C |

### 策略覆盖范围

| 类别 | 策略码 | 怎么模拟 |
|---|---|---|
| 事件类 | `TYPE_PROFILE`（资料）、`TYPE_AVATAR`（头像） | 脚本 A |
| 回调类 | `TYPE_EXTERNAL`（外部回调） | HTTP 回调 |
| 会话类 | `TYPE_CHAT`（私聊）等 | 不可模拟：命中由离线任务分析聊天数据产出，条件无法手动构造 |

### 功能速查

| 我想… | 用哪个 | 在哪执行 | 要改的参数 |
|---|---|---|---|
| 模拟资料/头像命中，走完整 Kafka 链路 | [脚本 A](#脚本-a模拟资料头像命中走-kafka) | service-a 后门 | `uid` `strategyId`，另按策略填 `hitContent` `imageUrl` |
| 模拟外部回调命中 | [HTTP 回调](#外部回调http) | 网关 HTTP（curl） | `uid` `dataTime` `data.msgid` |
| 同一天重复测同一档位 | [脚本 B](#脚本-b清理当天命中计数) | service-b 后门 | `uid` `hitDate` `configIdsText` |

## 脚本 A：模拟资料/头像命中（走 Kafka）

**用途**：在 service-a 构造并发送命中事件，service-b 消费后落库、处理。

**参数**（只改脚本开头的“可修改参数”）：

| 参数 | 怎么填 | 示例 |
|---|---|---|
| `uid` | 测试用户 ID | `"123456789"` |
| `strategyId` | `TYPE_PROFILE`（资料）或 `TYPE_AVATAR`（头像） | `"TYPE_PROFILE"` |
| `hitContent` | 仅资料命中用：命中的文本，随便写 | `"bsh-test-content"` |
| `imageUrl` | 仅头像命中用：图片 URL | `"https://xxx/test.jpg"` |

**脚本**：

```java
/* ===== 可修改参数 ===== */
uid = "123456789";
strategyId = "TYPE_PROFILE";
hitContent = "bsh-test-content";
imageUrl = "https://xxx/test.jpg";

/* ===== 构造 ext（按 strategyId 取对应字段；取值与生产 producer 一致） ===== */
extDto = new com.example.bean.HitExtDto();
if (strategyId.equals("TYPE_PROFILE")) {
    extDto.setHitContent(hitContent).setAuditName("audit_nickname");
} else if (strategyId.equals("TYPE_AVATAR")) {
    extDto.setHitImageUrl(imageUrl).setAuditName("audit_avatar_pic");
}

/* ===== 构造并发送事件 ===== */
now = System.currentTimeMillis();
today = new java.text.SimpleDateFormat("yyyy-MM-dd").format(new java.util.Date(now));
ticket = new com.example.bean.HitEvent.Ticket()
    .setUid(uid).setStrategyId(strategyId).setDate(today)
    .setCreateTimestamp(new Long(now))
    .setExt(com.example.util.JsonUtils.toJSON(extDto));
event = new com.example.bean.HitEvent().setTicket(ticket);
producer = context.getBean("eventProducerService");
future = producer.send(com.example.enums.EventEnum.hit_event, uid, event);
future.get();
"send ok: uid=" + uid + ", strategyId=" + strategyId + ", date=" + today;
```

**怎么看结果**：

- 返回值是字符串 `send ok: uid=...`。返回对象或其他内容，说明脚本没执行完整（见“常见问题”）。
- service-a 日志有 `send success`。
- service-b 日志有 `[handleHit]`，命中记录表新增一条，`strategy_code` 与 `strategyId` 一致。

## 外部回调（HTTP）

**用途**：模拟外部审核系统回调。不走后门，直接调网关。

**地址**（`POST`，`Content-Type: application/json`）：

| 环境 | URL |
|---|---|
| 测试 | `http://gateway-test.example.com/api/hit/internal/callback` |
| 线上 | `http://gateway.example.com/api/hit/internal/callback` |

前提：网关路由已配置（见 Melon 配置文档）。路由没配时返回 404。

**参数**：

| 参数 | 必填 | 怎么填 |
|---|---|---|
| `uid` | 是 | 测试用户 ID，必须等于 `data.userid` |
| `dataTime` | 是 | 命中时间，**秒级**时间戳。示例用 `$(date +%s)` |
| `data.msgid` | 是 | 消息 ID，**每次调用换新值**（幂等键），不超过 128 字符 |
| `data.userid` | 是 | 与 `uid` 相同 |

**示例**（测试环境；线上只替换域名）：

```bash
curl -X POST 'http://gateway-test.example.com/api/hit/internal/callback' \
  -H 'Content-Type: application/json' \
  -d '{
    "uid": "123456789",
    "dataTime": '"$(date +%s)"',
    "data": {
      "msgid": "test-'"$(date +%s)"'",
      "userid": "123456789"
    }
  }'
```

**怎么看结果**：

- 成功返回 `{"ec": 0, "result": true}`。
- 返回成功但无数据：uid 不是目标用户类型，或不在灰度内。
- 返回参数错误：`msgid` 缺失或超长、`uid` 与 `data.userid` 不一致。
- service-b 日志有 `[callback]`，命中记录表新增一条。

## 脚本 B：清理当天命中计数

**用途**：同一天重复测同一个档位。处理逻辑每个配置每天只处理一次：当天已有计数行，再次命中会被跳过。脚本 B 清掉指定日期的计数行，该用户当天再次命中时重新被当作“当天首次命中”。

**在哪执行**：service-b 后门。

**参数**：

| 参数 | 怎么填 |
|---|---|
| `uid` | 要清理的测试用户 ID |
| `hitDate` | 要清理的日期 `yyyy-MM-dd`。留空 = 今天 |
| `configIdsText` | 配置 ID，逗号分隔，如 `"7,8"`。留空 = 全部配置 |

**脚本**：

```java
/* ===== 可修改参数 ===== */
uid = "123456789";
hitDate = "";
configIdsText = "";

/* ===== 解析日期与配置 ===== */
date = hitDate.length() == 0 ? java.time.LocalDate.now() : java.time.LocalDate.parse(hitDate);
configIds = new java.util.LinkedHashSet();
if (configIdsText.length() == 0) {
    configs = context.getBean(com.example.dao.ConfigDao.class).listAll();
    for (i = 0; i < configs.size(); i++) {
        configIds.add(configs.get(i).getId());
    }
} else {
    parts = configIdsText.split(",");
    for (i = 0; i < parts.length; i++) {
        configIds.add(new Long(parts[i].trim()));
    }
}

/* ===== 调生产回滚方法清理，并回读剩余计数 ===== */
countService = context.getBean(com.example.service.HitCountService.class);
removed = countService.rollbackHitCount(uid, configIds, date);
remain = new StringBuffer();
it = configIds.iterator();
while (it.hasNext()) {
    id = it.next();
    remain.append(id).append("=").append(countService.getHitCount(uid, id, null)).append(" ");
}
"cleared: uid=" + uid + ", hitDate=" + date + ", removedRows=" + removed + ", remainCount: " + remain.toString().trim();
```

**怎么看结果**：返回 `cleared: ... removedRows=N, remainCount: 配置ID=次数`。`removedRows=0` 表示该用户当天没有计数行，常见原因：当天没命中、被灰度丢弃、总开关关闭、`hitDate` 填错。

**不会清理**：命中记录、已执行的处理结果、幂等键。重测时：脚本 A 每次自动生成新事件 ID；HTTP 回调换新的 `data.msgid`。线上只对测试 uid 执行。

## 常见问题

| 现象 | 原因与处理 |
|---|---|
| 发送成功但没有数据 | uid 不是目标用户类型，或不在灰度内。`strategyId` 非法时日志有 `Unknown strategyId`，事件被丢弃 |
| 同一 uid 同一天第二次命中没有再处理 | 每个配置每天只处理一次。执行脚本 B 清当天计数 |
| HTTP 回调第二次没有新数据 | `data.msgid` 重复，被幂等拦截。换新值 |
| 后门返回的是对象（如 `extDto`），不是 `send ok` / `cleared` 字符串 | 脚本没执行完整。后门平台会抹平换行，`//` 行注释会吞掉其后全部代码。只用 `/* */` 块注释 |
| 后门返回报错文本 | 看报错内容。bsh 不支持泛型和 lambda；`long` 传参需 `new Long(x)` 装箱 |
