# 示例：<需求名> Melon 配置变更说明

> 本示例随 skill 包自带；URI 与方法名为虚构工程示例值。

## 目的

列出 <分支名> 新增/修改的对外接口及对应 Melon 网关路由配置项，供运维在部署前配置。

## 配置总览

| URI | 变更 | 方法数 | 服务 |
|---|---|---|---|
| /service/xxx-quality-tag | 新增 | 4 | service-a |

## melon 配置

平台入口（两环境独立配置，链接全文仅此一份；下方每个 URI 勾选 = 该路由已配置）：

- [ ] 线下：https://melon.wemomo.com/gateway/outRoute?corp=alpha&env=stage&tenant=ddoversea
- [ ] 线上：https://melon.wemomo.com/gateway/outRoute?corp=overseas&env=overseas&tenant=ddoversea

- [ ] /service/xxx-quality-tag（新增）
  - 方法：queryQualityList、addQualityTag、removeQualityTag、queryTagConfig

方法级修改示例（URI 未变、方法增删）：

- [ ] /service/xxx-message（修改）
  - 新增方法：rescanQuickMessage
  - 删除方法：legacyCheck

## 风险

- **Melon 路由必须在服务部署前配置完毕，否则客户端调用 404**——checkbox 未全部勾选时不得给出可发版结论。
- 线下与线上是两次独立配置动作，在平台入口处分别勾选。

## 验收

- [ ] melon 配置已生效，MOA/HTTP 接口可正常访问（线下先行）。
