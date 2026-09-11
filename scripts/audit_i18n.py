#!/usr/bin/env python3
"""Global i18n audit for csp-logs: compare every root changelog page against its en/ mirror.

Checks per page:
  1. frontmatter has translated_by: ai
  2. AI-translation notice with correct en/ link
  3. `# 更新日志` header present
  4. bullet count (top + nested) EN == ZH
  5. all backtick code spans from EN preserved in ZH
  6. metadata values (Version ID / Size / Published date) preserved
  7. CJK sanity (body has substantial Chinese)

Usage: python3 scripts/audit_i18n.py [--all | file1 file2 ...]
Exit 1 if any page fails.
"""
import re
import sys
import glob
import os

DOCS = os.path.join(os.path.dirname(__file__), "..", "src", "content", "docs")

BULLETS = r"^\s*(?:\*   |• |- )"


def body_of(md: str) -> str:
    m = re.match(r"^---\n[\s\S]*?\n---\n", md)
    return md[m.end():] if m else md


def audit(zh_path: str):
    name = os.path.basename(zh_path)
    en_path = os.path.join(DOCS, "en", name)
    problems = []
    if not os.path.exists(en_path):
        return name, ["en/ mirror missing"]
    zh = open(zh_path, encoding="utf-8").read()
    en = open(en_path, encoding="utf-8").read()
    slug = name[:-3]

    if "translated_by: ai" not in zh.split("---")[1] if zh.startswith("---") else True:
        problems.append("frontmatter 缺 translated_by: ai")
    if "本页面由 AI 翻译" not in zh:
        problems.append("缺 AI 翻译声明")
    if f"/csp-logs/en/{slug}/" not in zh:
        problems.append("声明缺英文版链接(或链接错误)")
    if "# Changelog" in en and "# 更新日志" not in zh:
        problems.append("缺 `# 更新日志`")

    zb, eb = body_of(zh), body_of(en)
    # EN uses `*   `, `• ` or `- ` depending on page age/source; count all three
    z_items = len(re.findall(BULLETS, zb, re.M))
    e_items = len(re.findall(BULLETS, eb, re.M))
    if z_items != e_items:
        problems.append(f"列表项 EN {e_items} ≠ ZH {z_items}")

    e_codes = set(re.findall(r"`[^`\n]+`", eb))
    missing = [c for c in e_codes if c not in zh]
    if missing:
        problems.append(f"缺代码片段 {len(missing)}: {missing[:3]}")

    for pat, label in [(r"Version ID:\s*(\d+)", "版本 ID"), (r"Size:\s*([0-9.]+ MB)", "大小"), (r"Published:\s*([\d-]+)", "发布日期")]:
        m = re.search(pat, eb)
        if m and m.group(1) not in zh:
            problems.append(f"{label} 值缺失: {m.group(1)}")

    cjk = len(re.findall(r"[\u4e00-\u9fff]", zb))
    if cjk < 30 and len(eb) > 200:
        problems.append(f"正文中文过少 CJK={cjk}")

    return name, problems


def main():
    args = sys.argv[1:]
    if args and args[0] != "--all":
        files = [a if a.endswith(".md") else a + ".md" for a in args]
        files = [os.path.join(DOCS, f) for f in files]
    else:
        files = sorted(glob.glob(os.path.join(DOCS, "*.md")))
    fails = 0
    for f in files:
        name, problems = audit(f)
        if problems:
            fails += 1
            print(f"✗ {name}")
            for p in problems:
                print(f"    {p}")
    total = len(files)
    print(f"\n{total - fails}/{total} 通过" + ("" if fails else " ✓ 全部合规"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
