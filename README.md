# laoke-translate-pro · 技术文档翻译精校

> 局内人·老K · 专注实体老板 AI 落地实战

把"机翻一眼假、术语前后乱、读着像翻译腔"的译文，修成"像人写的、专业、一致"的成品。本仓库交付一套**可落地的翻译工作流** + 一个**零依赖术语/一致性检查脚本**，覆盖从预处理到后编辑到质检的每一步。

纯标准库、本地运行、不联网、可审计、开箱即用。

## 解决什么

- 术语翻错或前后不一致（"缓存"一会儿 cache 一会儿 buffer）。
- 机翻痕迹重（满屏"首先/其次/需要注意的是"）。
- 漏翻（源词残留在译文里）。
- 翻译腔（西化语序、被动堆砌、代词满天飞）。
- 没有术语库，每次从头翻，质量不可控。

## 快速上手

```bash
# 建术语库
python scripts/glossary_guard.py add cache 缓存 --domain 计算机
python scripts/glossary_guard.py add throughput 吞吐量 --domain 计算机

# 看术语库
python scripts/glossary_guard.py list

# 质检译文（抓漏翻/不一致/译词冲突）
python scripts/glossary_guard.py check --glossary glossary.csv --text 译文.txt

# 验证环境
python scripts/glossary_guard.py demo
```

完整工作流、后编辑规范、领域适配、提示词模板见 `SKILL.md` 与 `references/`。

## 能力边界（说实话）

- ✅ 后编辑、术语管理、一致性质检、去机翻腔。
- ✅ 零依赖、可审计、可接入工作流。
- ❌ 不联网调用翻译 API（需联网翻译请用对应服务）。
- ❌ 不替代专业本地化（大规模项目用 CAT 工具）。
- ❌ 文学性翻译（诗歌/小说）只做基础，需人工润色。

## 相关资源

- SkillHub 作者主页：搜索 `laoke-translate-pro`
- 作者落地页（更多 AI 落地实战与工具合集）：https://muzhi-888.github.io/ju-nei-ren-lao-k/

## 许可证与免责声明

MIT License。本工具仅供学习与研究使用，不构成任何翻译准确性或法律合规的保证；使用者须对输入内容的授权合法性、译文准确性及高风险材料（法律/医疗）的专业终审负责，禁止用于伪造、篡改或误导性翻译。
