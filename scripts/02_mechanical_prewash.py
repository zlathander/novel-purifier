#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Step 3.1 基于已知记忆库的全局机械预洗 (scripts/02_mechanical_prewash.py)
1. 加载 memory/deterministic_rules.json。
2. 解码所有 HTML 实体（如 &#183; -> · 等）。
3. 清除文件头尾采集站信息、行内/独立行首发网址水印、乱码域名（如 101??????.??????）。
4. 清除章节标题求票/加更后缀，清除采集站导致的连续重复章节标题行。
5. 将独立的“请假条”、“上架感言”、“卡文通知”完整剥离并存档至 reports/author_notes.txt。
6. 批量修正已知高频编码错字（什幺/那幺/怎幺 -> 什么/那么/怎么，擡 -> 抬 等）及明显机械叠词（。。 -> 。）。
7. 输出至 work/working_novel.txt。
"""

import os
import re
import json
import html

def run_prewash():
    novel_title = "面壁者但元婴期"
    input_file = f"backup/{novel_title}_backup.txt"
    rules_file = "memory/deterministic_rules.json"
    work_dir = "work"
    reports_dir = "reports"
    work_file = f"{work_dir}/working_novel.txt"
    notes_file = f"{reports_dir}/author_notes.txt"

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    with open(rules_file, "r", encoding="utf-8") as f:
        rules = json.load(f)

    # 1. 读取原备份文件（UTF-8 或 GB18030）
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_file, "r", encoding="gb18030", errors="ignore") as f:
            content = f.read()

    print(f"[Prewash] 原始文本字符数: {len(content)}")

    # 2. 解码所有 HTML 实体
    content = html.unescape(content)

    # 3. 批量修正确定性高频编码错字及机械叠词
    for rule in rules.get("exact_matches", []):
        pat = rule["pattern"]
        rep = rule["replacement"]
        content = content.replace(pat, rep)

    # 处理多余行内乱码域名
    for inline_rule in rules.get("inline_replacements", []):
        pat = inline_rule["pattern"]
        rep = inline_rule["replacement"]
        content = re.sub(pat, rep, content)

    lines = content.splitlines()
    print(f"[Prewash] 初始行数: {len(lines)}")

    # 4. 识别并提取独立请假条/感言单章
    leave_pattern = re.compile(r'^\s*(请假条|超级请假条|卡文ing|卡文[，,].*|上架感言.*)\s*$')
    chapter_start_pattern = re.compile(r'^\s*(?:第[0-9一二三四五六七八九十百千]+章|第一十一|第一十二|第一十三|第一十四|第一十五|第一十六|第一十七|第一十八|第一十九|第二十[一二三四五]章)')

    extracted_notes = []
    cleaned_lines = []

    in_author_note = False
    current_note_lines = []
    current_note_title = ""

    for idx, line in enumerate(lines):
        line_num = idx + 1
        s = line.strip()

        # 检查是否进入请假条/作者单章
        if not in_author_note and leave_pattern.match(s):
            in_author_note = True
            current_note_title = s
            current_note_lines = [f"=== 原书行号 ~{line_num}: {s} ==="]
            continue

        # 在请假条区域内，直到遇到下一个章节标题
        if in_author_note:
            if chapter_start_pattern.match(line):
                # 请假条结束，遇到新章节
                in_author_note = False
                extracted_notes.append("\n".join(current_note_lines))
                current_note_lines = []
                # 当前行进入普通行处理流程
            else:
                current_note_lines.append(line)
                continue

        cleaned_lines.append(line)

    if in_author_note and current_note_lines:
        extracted_notes.append("\n".join(current_note_lines))

    # 将提取的请假条写入 reports/author_notes.txt
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + "\n\n".join(extracted_notes) + "\n")
    print(f"[Prewash] 独立请假条/单章剥离完成，共剥离 {len(extracted_notes)} 篇，存档至: {notes_file}")

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
    # 增加带括号的通用求票加更正则
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
                        # 发现连续紧邻标题，且当前行是未缩进/混乱的爬虫抓取头
                        # 跳过当前行（保留第二行真实章节名）
                        has_dup = True
                        break
                    elif next_line.strip() != "":
                        break
            if has_dup:
                duplicate_titles_removed += 1
                i += 1
                continue

            # 清洗章节标题中的求票后缀
            original_title = line
            cleaned_title = original_title
            for suf in title_suffixes:
                if suf in cleaned_title:
                    cleaned_title = cleaned_title.replace(suf, "")
                    title_suffixes_cleaned += 1

            m = ticket_suffix_regex.search(cleaned_title.strip())
            if m:
                cleaned_title = cleaned_title.replace(m.group(0), "")
                title_suffixes_cleaned += 1

            # 规范化章节标题格式：统一首行无缩进或4空格
            cleaned_title = cleaned_title.strip()
            final_lines.append(cleaned_title)
            i += 1
            continue

        final_lines.append(line)
        i += 1

    print(f"[Prewash] 重复章节标题移除: {duplicate_titles_removed} 处")
    print(f"[Prewash] 章节求票后缀清洗: {title_suffixes_cleaned} 处")

    # 7. 写出至 work/working_novel.txt
    final_text = "\n".join(final_lines)
    # 去除尾部多余空白行与孤立 HTML 符号
    final_text = re.sub(r'(&gt;|>)\s*$', '', final_text.rstrip()) + "\n"

    with open(work_file, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"[Prewash] 预洗完成！输出文件: {work_file}")
    print(f"  - 最终行数: {len(final_lines)}")
    print(f"  - 最终字符数: {len(final_text)}")

if __name__ == "__main__":
    run_prewash()
