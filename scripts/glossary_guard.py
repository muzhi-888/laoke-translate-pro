#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glossary_guard.py — 双语术语库管理与翻译一致性检查（纯标准库）
================================================================

做技术文档 / 专业资料翻译时的两个老大难：
  1. 术语翻错或前后不一致（"缓存" 一会儿 cache 一会儿 buffer）。
  2. 源语种词漏翻，残留在译文里（"点击 Login 按钮"）。

本脚本零依赖，提供：
  add      往术语库追加一条 源词→译词（可带领域）
  list     列出当前术语库
  check    对一篇译文做一致性 + 漏翻检查，输出问题清单
  demo     生成示例术语库与示例译文并跑检查，验证环境

数据文件：glossary.csv（UTF-8，表头 src,tgt,domain）
  src   源语种词（如英文术语）
  tgt   目标语种译词（如中文术语）
  domain 领域标签（可选，如 计算机/医疗/金融）

设计目标：纯本地、不联网、不读目录外文件、可审计，便于接进翻译工作流。

退出码：0 = 成功（即使检查发现警告也返回 0，由用户判读）；2 = 参数/IO 错误。
"""

import argparse
import csv
import os
import re
import sys

GLOSSARY_DEFAULT = "glossary.csv"


def esc(t):
    return t.replace("\n", " ").strip()


def load_glossary(path):
    gloss = {}
    if not os.path.exists(path):
        return gloss
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = (row.get("src") or "").strip()
            tgt = (row.get("tgt") or "").strip()
            domain = (row.get("domain") or "").strip()
            if src and tgt:
                # 同一源词允许多译词（同义），以集合记录
                gloss.setdefault(src, {"tgts": set(), "domain": domain})
                gloss[src]["tgts"].add(tgt)
                if domain:
                    gloss[src]["domain"] = domain
    return gloss


def save_glossary(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["src", "tgt", "domain"])
        for r in rows:
            w.writerow([r["src"], r["tgt"], r.get("domain", "")])


def cmd_add(args):
    path = args.glossary
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    # 避免完全重复
    for r in rows:
        if r.get("src", "").strip() == args.src and r.get("tgt", "").strip() == args.tgt:
            print("SKIP: 该术语已存在，跳过。")
            return 0
    rows.append({"src": args.src, "tgt": args.tgt, "domain": args.domain or ""})
    save_glossary(path, rows)
    print("OK: 已添加 %s -> %s (领域=%s)，当前 %d 条。" % (args.src, args.tgt, args.domain or "-", len(rows)))
    return 0


def cmd_list(args):
    gloss = load_glossary(args.glossary)
    if not gloss:
        print("术语库为空：%s" % args.glossary)
        return 0
    print("术语库 %s 共 %d 条：" % (args.glossary, len(gloss)))
    for src, v in gloss.items():
        print("  %-24s -> %s   [%s]" % (src, " / ".join(sorted(v["tgts"])), v["domain"] or "-"))
    return 0


def cmd_check(args):
    gloss = load_glossary(args.glossary)
    if not gloss:
        sys.stderr.write("ERROR: 术语库为空或不存在：%s\n" % args.glossary)
        return 2
    if not os.path.exists(args.text):
        sys.stderr.write("ERROR: 译文文件不存在：%s\n" % args.text)
        return 2
    with open(args.text, encoding="utf-8") as f:
        text = f.read()
    issues = []
    # 1) 漏翻检查：源词残留在译文中
    for src in gloss:
        if len(src) < 2:
            continue
        # 词边界匹配（避免子串误伤，如 "in" 在 "input" 中）
        pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(src) + r"(?![A-Za-z0-9])")
        hits = pat.findall(text)
        if hits:
            issues.append(("漏翻", src, "译文中仍出现源词 '%s'（%d 处），应译为 %s" % (src, len(hits), " / ".join(sorted(gloss[src]["tgts"])))))
    # 2) 不一致检查：同一源词在译文中出现多种不同译法
    # 收集译文中出现过的各译词
    used_tgt = {}
    for src, v in gloss.items():
        for tgt in v["tgts"]:
            if len(tgt) < 1:
                continue
            if re.search(re.escape(tgt), text):
                used_tgt.setdefault(src, set()).add(tgt)
    for src, tgts in used_tgt.items():
        if len(tgts) > 1:
            issues.append(("不一致", src, "源词 '%s' 在译文中出现多种译法：%s，请统一" % (src, " / ".join(sorted(tgts)))))
    # 3) 译词冲突：不同源词映射到同一译词（可能串义）
    tgt_to_src = {}
    for src, v in gloss.items():
        for tgt in v["tgts"]:
            tgt_to_src.setdefault(tgt, set()).add(src)
    for tgt, srcs in tgt_to_src.items():
        if len(srcs) > 1:
            issues.append(("译词冲突", tgt, "译词 '%s' 被多个源词共用：%s，确认是否串义" % (tgt, " / ".join(sorted(srcs)))))
    # 输出
    if not issues:
        print("OK: 译文通过术语一致性检查，未发现漏翻 / 不一致 / 冲突。")
    else:
        print("发现 %d 项需复核：" % len(issues))
        for kind, key, msg in issues:
            print("  [%s] %s" % (kind, msg))
    return 0


def cmd_demo(args):
    here = os.path.dirname(os.path.abspath(__file__))
    gp = os.path.join(here, GLOSSARY_DEFAULT)
    save_glossary(gp, [
        {"src": "cache", "tgt": "缓存", "domain": "计算机"},
        {"src": "buffer", "tgt": "缓冲区", "domain": "计算机"},
        {"src": "thread", "tgt": "线程", "domain": "计算机"},
        {"src": "throughput", "tgt": "吞吐量", "domain": "计算机"},
    ])
    tp = os.path.join(here, "demo_translated.txt")
    with open(tp, "w", encoding="utf-8") as f:
        f.write(
            "系统使用 cache 来加速读取。\n"
            "数据先写入 buffer 缓冲区再落盘。\n"  # 故意不一致：buffer 又写"缓冲区"
            "每个 thread 线程独立运行。\n"
            "吞吐量 throughput 提升明显。\n"
        )
    print("已生成示例术语库 %s 与示例译文 %s" % (gp, tp))
    return cmd_check(argparse.Namespace(glossary=gp, text=tp))


def main(argv=None):
    ap = argparse.ArgumentParser(description="双语术语库管理与翻译一致性检查")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_add = sub.add_parser("add", help="追加术语")
    a_add.add_argument("src", help="源词")
    a_add.add_argument("tgt", help="译词")
    a_add.add_argument("--domain", default="", help="领域标签")
    a_add.add_argument("--glossary", default=GLOSSARY_DEFAULT)
    a_add.set_defaults(func=cmd_add)
    a_list = sub.add_parser("list", help="列出术语库")
    a_list.add_argument("--glossary", default=GLOSSARY_DEFAULT)
    a_list.set_defaults(func=cmd_list)
    a_check = sub.add_parser("check", help="检查译文")
    a_check.add_argument("--glossary", default=GLOSSARY_DEFAULT)
    a_check.add_argument("--text", required=True, help="译文文件路径")
    a_check.set_defaults(func=cmd_check)
    a_demo = sub.add_parser("demo", help="生成示例并自检")
    a_demo.set_defaults(func=cmd_demo)
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        sys.stderr.write("ERROR: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
