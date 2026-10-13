# 后门 bsh 测试脚本文档方法

完整示例随包自带：[../examples/backdoor-bsh-doc.md](../examples/backdoor-bsh-doc.md)。

## 入口约束（BackDoorMoaServiceImpl#execute）

[事实] 入口类位于各工程的 `ultron-backdoor-starter` 组件（`com.immomo.ultron.backdoor.moa.impl`）：

- MOA URI：`/service/{spring.application.name}-backdoor`（按目标服务拼，如 `/service/ultron-user-backdoor`）。
- 入参 `code` 为 bsh 脚本文本；脚本内可直接用 `context`（Spring `ApplicationContext`）。
- 已执行 `setAccessibility(true)`。
- `eval` 返回值 = 脚本最后一条语句的值（赋值语句返回所赋对象）；异常时返回 `e.getMessage()`。
- 后端 bsh 版本 2.0b6（backdoor-starter pom 依赖）。

## 写文档前的分析步骤

1. 定位被测链路的 producer 与 consumer：
   - producer 侧找发送方法（含私有方法）与其依赖 bean（`@Resource` 字段）。
   - consumer 侧找 kafka handler / service 方法的公开入口。
2. 确定事件/请求对象结构（字段、链式 setter、必填语义），从源码抄字段注释。
3. 确定每个 bean 的获取方式：bean 名称（autoconfig 方法名）或接口 class。
4. 检查 bean 是否可能被 AOP 代理（实现了接口 + 有切面 → JDK 动态代理）。

## 文档结构模板

```
# <主题>后门测试脚本
## 目的（入口 URI、code 约束）
## 链路背景（mermaid sequenceDiagram：后门 → producer → kafka → consumer）
## 事件/对象结构表（字段/类型/说明/示例）
## 脚本 A：<主推荐，显式构造并发送>（多行版，`/* */` 块注释，可直接提交 + 成功判据）
## 脚本 B：<直调真实方法>（解代理版；公共接口方法变体）
## 脚本 C：<消费侧直调，绕过 kafka>（按名取 bean + 解代理）
## 验证方法（日志关键字）
## 注意事项（灰度/幂等/判罚副作用/bsh 语法约束）
```

## bsh 语法硬约束（写脚本时逐条自查）

| 约束 | 正确写法 |
|---|---|
| 无类型声明即可，但泛型/lambda 不可用 | `uid = "123"` |
| 数组须先 new 再按下标赋值 | `argTypes = new Class[3]; argTypes[0] = String.class;` |
| 基本类型传包装类型参数须显式装箱 | `setCreateTimestamp(new Long(now))` |
| 枚举常量按静态字段访问 | `UserBehaviorEvent2Enum.hit_direct_strategy` |
| 静态泛型方法可调用（实参须真实继承关系） | `Wrapper.newEventWrapper(enum, uid, event)` |
| 末行字符串字面量 = 返回值 | `"OK uid=" + uid` |

## 已踩坑（必须写进文档的注意事项）

1. **注释吞行（已本地复现）**：调用平台抹平多行 code 的换行，首个 `//` 行注释吞掉其后全部代码，指纹 = 返回体 `result` 为中间变量对象（如 extDto 序列化）或 null（首行即注释时全脚本被吞）且 `ec=0`。规避：**多行版一律用 `/* */` 块注释**（有闭合符，抹平后不吞行，已实测原样/抹平双场景通过）。空行无影响；bsh 解释器本身对多行+`//` 解析正常。文档只给多行版（块注释，可直接提交）。
2. **AOP 代理**：`getBean` 返回代理时，私有方法/不在接口上的方法直调报 `Method Invocation ...`。规避：`AopUtils.isAopProxy(x)` + `((Advised) x).getTargetSource().getTarget()` 解包后在 target 上调用。解包后私有方法可直调（setAccessibility 生效），反射仅作兜底。
3. **按具体类取 JDK 代理 bean 会直接失败**（代理不是该 Class 实例）→ 用 bean 名称取。
4. **状态不跨请求**：每次 `execute` 新建 Interpreter，无法分多次提交脚本。

## 脚本正确性的验证方法（写文档前必做）

多行版脚本本地实测（原样 + 换行抹平双场景）后再写入文档：

1. 从 `~/.m2` 取 bsh 2.0b6 + spring-aop/core/beans + commons-logging jar。
2. 用 stub 类复刻目标结构（同 FQN 包名、接口、私有方法、链式 setter、枚举）。
3. stub context 用 `new ProxyFactory(target).getProxy()` 造 JDK 代理。
4. `Interpreter.eval` 跑多行脚本：先原样执行，再做一次 `replace("\n", "")` 抹平变体；断言：目标方法被调用（stdout 打印）、返回末行字符串、解包后 targetClass 为真实实现类。
5. 复刻时注意 stub 继承关系要与真实类一致（泛型擦除匹配）。

## 成功判据写法

每份脚本给两条判据：① moa 返回 `result` 为预期的末行字符串（若返回对象 = 注释吞行/未完整执行）；② 业务日志关键字（如 `sendUserBehaviorEvent success` / handler 日志）。
