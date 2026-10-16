#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 2: 全书特征画像与结构诊断 (scripts/01_profiler.py)
1. 自动编码探测与安全备份至 backup/，并在后续统一以 UTF-8 处理。
2. 目录树与结构污染诊断：扫描全书章节标题，识别是否存在爬虫重复章节标题行、正文夹杂的请假条/感言单章、章节断号。
3. 全书实体指纹提取：统计高频人名、核心势力名、专有名词、英文缩写，建立标准基准对照表。
4. 输出诊断画像至 novels_meta/面壁者但元婴期_profile.json。
"""

import os
import re
import json
import shutil
from collections import Counter

def run_profiler():
    novel_title = "面壁者但元婴期"
    input_path = f"input/{novel_title}.txt"
    backup_dir = "backup"
    backup_path = f"{backup_dir}/{novel_title}_backup.txt"
    meta_dir = "novels_meta"
    profile_path = f"{meta_dir}/{novel_title}_profile.json"

    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    # 1. 安全备份原文件
    shutil.copy2(input_path, backup_path)
    print(f"[Profiler] 安全备份完成: {backup_path}")

    # 读取并统一转为 UTF-8
    with open(input_path, "rb") as f:
        raw_bytes = f.read()

    decoded_text = None
    used_encoding = None
    for enc in ["utf-8", "gb18030", "gbk", "big5"]:
        try:
            decoded_text = raw_bytes.decode(enc)
            used_encoding = enc
            print(f"[Profiler] 成功识别并以 {enc} 编码解码，总字符数: {len(decoded_text)}")
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise ValueError("[Profiler] 无法解码输入文件！")

    lines = decoded_text.splitlines()

    # 2. 章节异常扫描与目录树分析
    chapter_regex = re.compile(r'^\s*(第[0-9一二三四五六七八九十百千]+[章回节卷集部].*)$')
    number_regex = re.compile(r'第([0-9]+)章')
    leave_regex = re.compile(r'^\s*(请假条|超级请假条|卡文ing|卡文[，,].*|上架感言.*)\s*$')

    all_raw_chapters = []
    consecutive_duplicates = []
    author_notes = []

    for idx, line in enumerate(lines):
        line_num = idx + 1
        s = line.strip()

        # 检测独立请假条/单章
        if leave_regex.match(s):
            author_notes.append({
                "line_number": line_num,
                "title": s
            })

        # 检测章节标题
        m = chapter_regex.match(line)
        if m:
            title = m.group(1).strip()
            num_match = number_regex.search(title)
            ch_num = int(num_match.group(1)) if num_match else None
            all_raw_chapters.append({
                "line_number": line_num,
                "title": title,
                "chapter_number": ch_num,
                "indent": len(line) - len(line.lstrip())
            })

    # 检测连续重复标题
    dedup_chapters = []
    for i, ch in enumerate(all_raw_chapters):
        if i > 0:
            prev = all_raw_chapters[i - 1]
            clean_t1 = re.sub(r'\s+', '', prev["title"])
            clean_t2 = re.sub(r'\s+', '', ch["title"])
            if (clean_t1 == clean_t2 or (prev["chapter_number"] and prev["chapter_number"] == ch["chapter_number"])) and (ch["line_number"] - prev["line_number"] <= 3):
                consecutive_duplicates.append({
                    "first_line": prev["line_number"],
                    "second_line": ch["line_number"],
                    "first_title": prev["title"],
                    "second_title": ch["title"]
                })
                continue
        dedup_chapters.append(ch)

    # 检测跳号/断号
    numbered_chapters = [c for c in dedup_chapters if c["chapter_number"] is not None]
    gaps = []
    for i in range(len(numbered_chapters) - 1):
        cur_num = numbered_chapters[i]["chapter_number"]
        nxt_num = numbered_chapters[i + 1]["chapter_number"]
        if nxt_num != cur_num + 1:
            gaps.append({
                "from_chapter": cur_num,
                "to_chapter": nxt_num,
                "from_line": numbered_chapters[i]["line_number"],
                "to_line": numbered_chapters[i + 1]["line_number"],
                "from_title": numbered_chapters[i]["title"],
                "to_title": numbered_chapters[i + 1]["title"]
            })

    # 3. 全书实体指纹提取 (Canonical Entities)
    known_canonicals = {
        "雷格亚兹": "雷迪亚兹",
        "西恩斯": "希恩斯",
        "pcd": "PDC",
        "pdc": "PDC",
        "bbc": "BBC",
        "eto": "ETO"
    }

    # 提取英文缩写频次
    acronyms = Counter(re.findall(r'\b[A-Za-z]{2,5}\b', decoded_text))

    # 统计高频中文词汇（人名、设定、势力）
    words = re.findall(r'[\u4e00-\u9fa5]{2,5}', decoded_text)
    stopwords = {"这个", "那个", "自己", "他们", "我们", "没有", "一个", "什幺", "那么", "怎么", "什么", "如果", "但是", "因为", "所以", "现在", "虽然", "已经", "知道", "看到", "听到", "觉得", "可以", "出现", "出来", "进去", "正在", "还是", "不是", "就是", "这些", "那些", "时候", "然后", "随后", "只是", "似乎", "仿佛", "可能", "甚至", "开始", "最后", "整个", "一样", "这样", "那样", "突然", "不过", "其实", "而且", "对于", "关于", "为了"}
    word_counts = Counter(w for w in words if w not in stopwords and len(w) >= 2)
    top_entities = [{"entity": w, "count": c} for w, c in word_counts.most_common(80)]

    profile_data = {
        "novel_title": novel_title,
        "source_encoding": used_encoding,
        "total_lines": len(lines),
        "total_characters": len(decoded_text),
        "total_raw_chapter_matches": len(all_raw_chapters),
        "total_dedup_chapters": len(dedup_chapters),
        "consecutive_duplicate_count": len(consecutive_duplicates),
        "consecutive_duplicates_sample": consecutive_duplicates[:15],
        "chapter_gaps_count": len(gaps),
        "chapter_gaps": gaps,
        "author_notes_count": len(author_notes),
        "author_notes": author_notes,
        "canonical_entity_mapping": known_canonicals,
        "top_acronyms": [{"acronym": k, "count": v} for k, v in acronyms.most_common(20)],
        "top_entities": top_entities[:50]
    }

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

    print(f"[Profiler] 结构诊断完成！画像已写入: {profile_path}")
    print(f"  - 原始章节匹配: {len(all_raw_chapters)}")
    print(f"  - 连续重复标题数: {len(consecutive_duplicates)}")
    print(f"  - 章节跳号断号数: {len(gaps)}")
    print(f"  - 独立请假条/感言数: {len(author_notes)}")

if __name__ == "__main__":
    run_profiler()
