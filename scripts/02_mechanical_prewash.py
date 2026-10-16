#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Step 3.1 确定性脚本全局机械预洗 (scripts/02_mechanical_prewash.py)
1. 解码全部 HTML 实体。
2. 剥离文件头尾采集站信息、行内/独立行首发网址水印、乱码域名。
3. 合并消除爬虫产生的连续重复章节标题行；剥离独立请假条/单章至 reports/author_notes.txt；清除章节标题求票/加更后缀。
4. 批量修复已知高频编码错字（什幺/那幺/怎幺/这幺/多幺/要幺 -> 什么/那么/怎么/这么/多么/要么，擡 -> 抬，凭藉 -> 凭借）及机械叠词（。。 -> 。）。
5. 修复句末反向引号（...「 -> ...」）及孤立网页分页遗留符（>）。
6. 输出至 work/working_novel.txt。
"""

import os
import re
import json
import html

def run_prewash():
    novel_title = "面壁者但元婴期"
    backup_path = f"backup/{novel_title}_backup.txt"
    rules_path = "memory/deterministic_rules.json"
    work_dir = "work"
    reports_dir = "reports"
    work_path = f"{work_dir}/working_novel.txt"
    notes_path = f"{reports_dir}/author_notes.txt"

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    # 1. 安全读取备份文件 (UTF-8 或 GB18030)
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(backup_path, "r", encoding="gb18030", errors="ignore") as f:
            content = f.read()

    print(f"[Prewash] 原始输入文本字符数: {len(content)}")

    # 2. 解码所有 HTML 实体
    content = html.unescape(content)

    # 3. 批量精确替换已知高频确定性编码错字
    for item in rules.get("exact_matches", []):
        pat = item["pattern"]
        rep = item["replacement"]
        content = content.replace(pat, rep)

    # 行内乱码域名替换
    for inline_item in rules.get("inline_replacements", []):
        pat = inline_item["pattern"]
        rep = inline_item["replacement"]
        content = re.sub(pat, rep, content)

    lines = content.splitlines()
    print(f"[Prewash] 初始行数: {len(lines)}")

    # 4. 识别并提取独立请假条/感言单章
    leave_pattern = re.compile(r'^\s*(请假条|超级请假条|卡文ing|卡文[，,].*|上架感言.*)\s*$')
    chapter_start_pattern = re.compile(r'^\s*(?:第[0-9一二三四五六七八九十百千]+章|第一十[一二三四五六七八九]章|第二十[一二三四五]章)')

    extracted_notes = []
    cleaned_lines = []

    in_author_note = False
    current_note_lines = []

    for idx, line in enumerate(lines):
        line_num = idx + 1
        s = line.strip()

        # 检查是否进入请假条/作者单章
        if not in_author_note and leave_pattern.match(s):
            in_author_note = True
            current_note_lines = [f"=== 原书行号 ~{line_num}: {s} ==="]
            continue

        # 在请假条区域内，直到遇到下一个章节标题
        if in_author_note:
            if chapter_start_pattern.match(line):
                # 请假条结束，遇到新章节
                in_author_note = False
                extracted_notes.append("\n".join(current_note_lines))
                current_note_lines = []
            else:
                current_note_lines.append(line)
                continue

        cleaned_lines.append(line)

    if in_author_note and current_note_lines:
        extracted_notes.append("\n".join(current_note_lines))

    with open(notes_path, "w", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + "\n\n".join(extracted_notes) + "\n")
    print(f"[Prewash] 独立请假条/单章剥离完成，共剥离 {len(extracted_notes)} 篇，归档至: {notes_path}")

    # 5. 去除采集站水印行与文件头尾元数据
    watermark_regexes = [re.compile(p) for p in rules.get("regex_watermarks", [])]
    filtered_lines = []
    watermarks_removed = 0

    for idx, line in enumerate(cleaned_lines):
        s = line.strip()
        # 排除头部的来源信息
        if idx < 10 and (s.startswith("来源：") or s.startswith("网址：") or s.startswith("章节范围：")):
            watermarks_removed += 1
            continue

        # 排除末尾的站点链接
        if idx > len(cleaned_lines) - 10 and s.startswith("更多精彩小说，请访问："):
            watermarks_removed += 1
            continue

        # 检查防盗水印（负面约束：若行内包含对话或长故事段落，不误删）
        is_watermark = False
        if not ('「' in line and '」' in line):
            for w_re in watermark_regexes:
                if w_re.match(line):
                    is_watermark = True
                    break

        if is_watermark:
            watermarks_removed += 1
            continue

        filtered_lines.append(line)

    print(f"[Prewash] 水印及头尾采集信息过滤完成，共移除 {watermarks_removed} 行")

    # 6. 处理章节标题污染与连续重复标题
    title_suffixes = rules.get("title_suffixes", [])
    ticket_suffix_regex = re.compile(r'[（\(【](?:求追读|求月票|求首订|求推荐票|求收藏|求打赏|求全订|求订阅|加更|补更)[^）\(\)】]*[）\)】]$')

    final_lines = []
    i = 0
    duplicate_titles_removed = 0
    title_suffixes_cleaned = 0

    while i < len(filtered_lines):
        line = filtered_lines[i]
        s = line.strip()

        # 检测章节标题
        is_ch = re.match(r'^\s*(?:第[0-9一二三四五六七八九十百千]+章|第一十[一二三四五六七八九]章|第二十[一二三四五]章)', line)
        if is_ch:
            # 检查后续 1~3 行内是否存在重复/正规章节标题
            has_dup = False
            for step in range(1, 4):
                if i + step < len(filtered_lines):
                    next_line = filtered_lines[i + step]
                    if re.match(r'^\s*第[0-9一二三四五六七八九十百千]+章', next_line):
                        has_dup = True
                        break
                    elif next_line.strip() != "":
                        break
            if has_dup:
                duplicate_titles_removed += 1
                i += 1
                continue

            # 清洗章节标题中的求票后缀
            cleaned_title = line
            for suf in title_suffixes:
                if suf in cleaned_title:
                    cleaned_title = cleaned_title.replace(suf, "")
                    title_suffixes_cleaned += 1

            m = ticket_suffix_regex.search(cleaned_title.strip())
            if m:
                cleaned_title = cleaned_title.replace(m.group(0), "")
                title_suffixes_cleaned += 1

            cleaned_title = cleaned_title.strip()
            final_lines.append(cleaned_title)
            i += 1
            continue

        # 修复句末反向引号 ...「 -> ...」
        if line.endswith("「") and ("「" in line[:-1] or "」" in line[:-1] or line.startswith("    「") or "，" in line or "。" in line):
            line = line[:-1] + "」"

        # 过滤孤立成行的分页遗留符 >
        if s in [">", "&gt;"]:
            i += 1
            continue

        final_lines.append(line)
        i += 1

    print(f"[Prewash] 重复章节标题移除: {duplicate_titles_removed} 处")
    print(f"[Prewash] 章节求票后缀清洗: {title_suffixes_cleaned} 处")

    # 7. 写出至 work/working_novel.txt
    final_text = "\n".join(final_lines)
    final_text = re.sub(r'(&gt;|>)\s*$', '', final_text.rstrip()) + "\n"

    with open(work_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"[Prewash] 机械预洗完成！输出文件: {work_path}")
    print(f"  - 最终行数: {len(final_lines)}")
    print(f"  - 最终字符数: {len(final_text)}")

if __name__ == "__main__":
    run_prewash()
