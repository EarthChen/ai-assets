# 后门 / 接口模拟测试文档方法（QA 版）

完整示例随包自带：[../examples/backdoor-bsh-doc.md](../examples/backdoor-bsh-doc.md)。

读者是 QA。每个功能只回答三件事：什么时候用、参数怎么填、怎么看结果。文档要短。

## 入口约束（写给作者，不原样写进 QA 文档）

[事实] 入口类位于各工程的 `ultron-backdoor-starter` 组件（`com.immomo.ultron.backdoor.moa.impl.BackDoorMoaServiceImpl#execute`）：

- 入参 `code` 为 bsh 脚本文本；脚本内可直接用 `context`（Spring `ApplicationContext`）。
- 已执行 `setAccessibility(true)`。
- `eval` 返回值 = 脚本最后一条语句的值（赋值语句返回所赋对象）；异常时返回 `e.getMessage()`。
- bsh 版本以 backdoor-starter 的 pom 为准，实际部署版本不确定，本地验证两个版本都跑（见“验证方法”）。

**后门地址由用户提供**（每个服务一个，QA 在该页面提交脚本）。不要猜 MOA URI，不要把 `/service/{应用名}-backdoor` 写进 QA 文档。缺地址时向用户索要，或在文档中留待确认项。

## 写文档前的分析步骤

先扫覆盖面，再写脚本。漏一类入口比脚本写错更常见。

1. **穷举触发入口**，按类别分组：
   - Kafka 事件：找 producer 的发送点（`sendUserBehaviorEvent(<枚举>, ...)`）和 consumer 的 `addHandler(<枚举>, ...)`，一个事件枚举 = 一类入口。
   - 网关 HTTP / 内部 MOA 接口：diff 中新增或修改的接口方法，取注释里的 `@path`。
   - 定时任务、其他回调。
2. **穷举策略/类型枚举值**：读枚举定义，把每个值归到一类入口。每个值要么有模拟方式，要么在文档里写“不可模拟 + 原因”。
3. **生产 producer 是字段取值的权威**：ext 字段、策略名常量、日期格式都从生产 producer 代码抄（如 `emitXxxHit`），不手写占位值。旧文档里引用的方法，用 `git grep` 确认仍存在；已不存在就删。
4. **列出静默丢弃点**：性别过滤、灰度门控、总开关、幂等键、每日闸门/计数。每一处都写进“先读这里”或“常见问题”，因为 QA 看到的现象是“发送成功但无数据”。
5. 确定每个 bean 的获取方式（bean 名称或接口 class），检查是否 AOP 代理（实现接口 + 有切面 → JDK 动态代理）。
6. 确定事件/请求对象的字段与链式 setter，从源码抄字段注释。

## 文档结构模板

```
# <业务主题>模拟指南（QA 版）
## 先读这里
   测试数据前提 3-4 条（用户条件、灰度、副作用）+ 后门地址表（服务 | 后门地址 | 执行的脚本）
### 策略覆盖范围   （类别 | 策略码 | 怎么模拟）
### 功能速查       （我想… | 用哪个 | 在哪执行 | 要改的参数，每行带锚点链接）
## 脚本 A：<功能>   固定四块：用途 / 参数表（参数 | 怎么填 | 示例）/ 脚本 / 怎么看结果
## 脚本 B…          同上
## <HTTP 接口>（有网关接口时）
## 脚本 N：清理<状态>（有闸门/计数/幂等限制时）
## 常见问题         现象 | 原因与处理
```

写作规则：

- 不放 sequenceDiagram、事件结构表。字段信息进参数表。
- 不放开发调试用的脚本（直调私有方法、反射兜底），除非用户要求。QA 用不上。
- 参数表只列 QA 要改的参数，对应脚本开头的“可修改参数”块；其余写死。
- 同类策略用 `if / else if` 让一个脚本覆盖，不要让 QA 替换代码段。
- `if` 内赋值的变量先在块外初始化（`extDto = new X();` 再在块内调 setter）。
- 脚本名带用途（“脚本 A：模拟资料/头像/相册命中（走 Kafka）”）。锚点用 GitHub slug：小写、去标点、空格转 `-`。
- 文件名按业务主题命名，不以实现手段命名（用 `<主题>-simulation.md`，不用 `<主题>-bsh.md`），因为同一份文档可能含 HTTP 调用。

## HTTP 接口模拟节

触发：diff 中新增或修改了带 `@path` 的内部/回调接口。

内容：

- 地址表：测试、线上两个完整 URL = 域名 + `@path`。**域名由用户提供**。
- 方法与格式：同服务其他网关接口的惯例是 `POST` + JSON。网关鉴权（header、签名）从代码看不出时，列入待确认项，不要编。
- 参数表：必填、怎么填。取自请求类注解和 service 的校验逻辑。
- 幂等键：写明哪个字段，并要求每次换新值；示例里用 `$(date +%s)` 生成。
- curl 示例：线上只换域名。
- 结果：成功响应只写有来源的内容（接口注释里的 `ec=0, result=true`）。不编 `em` 和失败 `ec` 值，失败场景用文字描述。
- 前置：Melon 路由已配置，链接到 Melon 配置文档；路由没配时返回 404。
- 静默跳过的场景（如非目标用户返回成功但不落库）单独列出。

## 状态清理脚本

触发：业务逻辑有“每天一次”“幂等”“累计计数”类限制，QA 反复测同一场景会被拦截。

做法：

1. 读代码，找可复用的生产方法（如判罚失败时回滚计数的方法），在脚本里调用它，不手写 SQL。
2. 确认清理后能重新写入（软删除时唯一键是否含 `deleted`）。
3. 参数：`uid`、日期（留空 = 今天）、配置 ID（留空 = 全部）。
4. 返回清理行数和清理后的剩余计数，QA 一眼能验证。
5. 文档写明“不会清理”的数据（命中记录、已执行的处罚、幂等键）和对应的重测办法（换新事件 ID、换新 msgid、后台手动解除）。
6. 提醒线上只对测试 uid 执行。

## bsh 语法硬约束（写脚本时逐条自查）

| 约束 | 正确写法 |
|---|---|
| 无类型声明即可，泛型/lambda 不可用 | `uid = "123"` |
| 集合用原始类型 | `new java.util.ArrayList()` |
| 数组须先 new 再按下标赋值 | `argTypes = new Class[3]; argTypes[0] = String.class;` |
| 基本类型传包装类型参数须显式装箱 | `new Long(now)`、`new Integer(1)` |
| 枚举常量按静态字段访问 | `UserBehaviorEvent2Enum.hit_direct_strategy` |
| 取 bean 按接口 | `context.getBean(com.x.Foo.class)` |
| 末行字符串字面量 = 返回值 | `"OK uid=" + uid` |
| 循环用下标 | `for (i = 0; i < list.size(); i++)` |

## 已踩坑（写成 QA 文档“常见问题”表的行，不单列章节）

1. **注释吞行**：调用平台抹平多行 code 的换行，首个 `//` 行注释吞掉其后全部代码。指纹 = 返回体 `result` 是中间变量对象（如 `extDto`）或 null，且 `ec=0`。规避：多行版一律用 `/* */` 块注释。空行无影响。
2. **AOP 代理**：`getBean` 返回代理时，私有方法/不在接口上的方法直调报 `Method Invocation ...`。规避：`AopUtils.isAopProxy(x)` + `((Advised) x).getTargetSource().getTarget()` 解包后调用。
3. **按具体类取 JDK 代理 bean 会失败**（代理不是该 Class 的实例）：用 bean 名称取。
4. **状态不跨请求**：每次 `execute` 新建 Interpreter，不能分多次提交脚本。

## 验证方法（写入文档前必做）

脚本必须本地跑通。验证的是**成品文档里的文本**，不是另写的副本。

1. 用 Python 从成品 md 按标题提取每个 ` ```java ` 块，存成 `.bsh`。
2. 从 `~/.m2` 取 bsh **2.0b6 和 2.0b4 两个版本**，加 spring-aop/core/beans/jcl（脚本用到 `AopUtils`/`Advised` 时）。
3. 用 stub 类复刻目标结构：同 FQN 包名、链式 setter、枚举、静态工厂；stub 的 `context.getBean` 返回带 `System.out.println` 的 stub bean。需要代理场景时用 `new ProxyFactory(target).getProxy()`。
4. harness 用 `bsh.Capabilities.setAccessibility(true)`（2.0b6 的 `Interpreter` 没有 `setAccessibility` 方法）；`i.set("context", ctx)`；`i.eval(code)`。
5. 每个脚本跑这些场景：
   - 多行原样、`replace("\n", " ")` 抹平，两次结果一致。
   - 每个分支取值各跑一次（如 `strategyId` 的每个合法值）。
   - 带参数变体（如把“留空”参数改成非空）。
6. 断言：stub 方法被调用、返回末行字符串、解代理后 `targetClass` 为真实实现类。

stub 只证明 bsh 语法和调用语义正确，不证明真实 bean 的行为。向用户汇报时明说“未连真实环境执行”。

## 成功判据写法

每个脚本给两条：① moa 返回 `result` 为预期的末行字符串（约定前缀：`send ok` / `handled` / `cleared`；返回对象 = 注释吞行或未执行完）；② 业务日志关键字（`sendUserBehaviorEvent success`、handler 日志）。清理类脚本补充 `removedRows=0` 的常见原因。

## 交付前自查

- 覆盖表里每个枚举值都有归属（模拟方式或“不可模拟 + 原因”）。
- 后门地址、网关域名来自用户，没有猜测。
- 没有未经证实的响应字段、`ec` 值、鉴权方式。
- ext 字段和常量与生产 producer 一致。
- 文档里没有已不存在的方法引用。
- 所有脚本已按“验证方法”跑过，汇报里说明验证范围。
