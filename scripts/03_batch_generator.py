#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Step 3.2 切分适度批次与初始化进度锁 (scripts/03_batch_generator.py)
将 work/working_novel.txt 按每批次 12 章切分为独立文本文件 work/Batch_001.txt 至 work/Batch_N.txt，
并生成 work/audit_manifest.json（所有批次初始 status 必须为 "PENDING"）。
禁令：严禁创建任何 patches_Batch_*.json 文件！
"""

import os
import re
import json

def generate_batches():
    work_file = "work/working_novel.txt"
    work_dir = "work"
    manifest_file = os.path.join(work_dir, "audit_manifest.json")

    os.makedirs(work_dir, exist_ok=True)

    with open(work_file, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    chapter_regex = re.compile(r'^\s*(第[0-9一二三四五六七八九十百千]+[章回节卷集部].*)$')

    chapter_indices = []
    chapter_titles = []
    for idx, line in enumerate(lines):
        m = chapter_regex.match(line)
        if m:
            chapter_indices.append(idx)
            chapter_titles.append(m.group(1).strip())

    if not chapter_indices:
        raise ValueError("[BatchGenerator] 未在 working_novel.txt 中检测到任何章节标题！")

    chapters_per_batch = 12
    total_chapters = len(chapter_indices)
    batches = []

    for b_idx in range(0, total_chapters, chapters_per_batch):
        batch_num = len(batches) + 1
        batch_id = f"Batch_{batch_num:03d}"

        # 批次的起始行为当前批次第一章的行号（第一批从第0行开始包含书名头部）
        if b_idx == 0:
            start_line = 0
        else:
            start_line = chapter_indices[b_idx]

        # 批次的结束行为下一批次第一章的前一行（最后一个批次直到文本末尾）
        if b_idx + chapters_per_batch < total_chapters:
            end_line = chapter_indices[b_idx + chapters_per_batch] - 1
        else:
            end_line = len(lines) - 1

        batch_chapters = chapter_titles[b_idx: b_idx + chapters_per_batch]
        batch_lines = lines[start_line: end_line + 1]
        batch_text = "\n".join(batch_lines) + "\n"

        batch_file = os.path.join(work_dir, f"{batch_id}.txt")
        with open(batch_file, "w", encoding="utf-8") as bf:
            bf.write(batch_text)

        batches.append({
            "batch_id": batch_id,
            "batch_index": batch_num,
            "file": f"{batch_id}.txt",
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": end_line - start_line + 1,
            "char_count": len(batch_text),
            "chapter_count": len(batch_chapters),
            "chapter_range": f"{batch_chapters[0]} - {batch_chapters[-1]}",
            "start_chapter": batch_chapters[0] if batch_chapters else "",
            "end_chapter": batch_chapters[-1] if batch_chapters else "",
            "status": "PENDING"
        })

    manifest_data = {
        "novel_title": "面壁者但元婴期",
        "total_lines": len(lines),
        "total_characters": sum(b["char_count"] for b in batches),
        "total_chapters": total_chapters,
        "total_batches": len(batches),
        "chapters_per_batch": chapters_per_batch,
        "batches": batches
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print(f"[BatchGenerator] 批次进度锁与独立切片文件生成成功: {manifest_file}")
    print(f"  - 总章节数: {total_chapters}")
    print(f"  - 总批次数: {len(batches)} (Batch_001 ~ {batches[-1]['batch_id']})")
    print(f"  - 每批规模: 约 {chapters_per_batch} 章 (25,000 ~ 50,000 字符)")

if __name__ == "__main__":
    generate_batches()
