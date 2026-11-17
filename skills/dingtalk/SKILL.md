---
name: dingtalk
description: 钉钉 dws 统一入口:在线文档(doc)、知识库(wiki)与钉盘文件管理(drive)的查找、读写与管理。
disable-model-invocation: true
---

# 钉钉 dws 路由

本机已装 `dws`(Homebrew `dingtalk-workspace-cli`)。未认证时,先让用户执行 `dws auth login`。

## 步骤

1. 按意图选目标,读取对应 SKILL.md 并在整轮会话中遵循其执行契约。目标 skill 与本 skill 部署在同一用户级 skill 目录(`~/.claude/skills/`、`~/.agents/skills/`),互为同级目录,路径按本 skill 实际所在目录解析:

   | 意图 | 加载 |
   |---|---|
   | 在线文档正文读写、导出/导入、评论、附件、版本、模板、协作者权限、分享链接 | 同级目录 `dingtalk-doc/SKILL.md` |
   | 知识库空间、库内节点、知识库成员、空间分享范围、知识库动态 | 同级目录 `dingtalk-wiki/SKILL.md` |
   | 钉盘/文档空间的文件与目录存储:浏览、搜索、上传下载、复制、移动、重命名、删除、回收站、收藏、版本、最近访问文档、文件夹同步 | 同级目录 `dingtalk-drive/SKILL.md` |
   | 认证、权限、profile、confirmation、未知错误的语义 | 同级目录 `dingtalk-shared/references/` 对应文件 |

   完成标准:目标 SKILL.md 已读取,其 DWS 执行契约接管后续全部操作。
2. 意图落在两个产品之间时,先向用户确认目标产品。知识库节点确定后的正文读写固定切 doc。
3. 同一轮跨 doc 与 wiki 时,第二个产品只补读其 SKILL.md,执行契约复用。
