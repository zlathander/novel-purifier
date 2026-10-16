#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Step 3.2 建立全书批次进度锁 (scripts/03_batch_generator.py)
将 work/working_novel.txt 按每批次 5 章划分为连续批次（Batch_001 至 Batch_N），
写入 reports/audit_manifest.json，所有批次初始状态设为 PENDING。
"""

import os
import re
import json

def generate_batches():
    work_file = "work/working_novel.txt"
    manifest_file = "reports/audit_manifest.json"
    reports_dir = "reports"

    os.makedirs(reports_dir, exist_ok=True)

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

    batches = []
    chapters_per_batch = 5
    total_chapters = len(chapter_indices)

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

        batches.append({
            "batch_id": batch_id,
            "batch_index": batch_num,
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": end_line - start_line + 1,
            "chapter_count": len(batch_chapters),
            "start_chapter": batch_chapters[0] if batch_chapters else "",
            "end_chapter": batch_chapters[-1] if batch_chapters else "",
            "status": "PENDING"
        })

    manifest_data = {
        "novel_title": "面壁者但元婴期",
        "total_lines": len(lines),
        "total_chapters": total_chapters,
        "total_batches": len(batches),
        "chapters_per_batch": chapters_per_batch,
        "batches": batches
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print(f"[BatchGenerator] 批次进度锁生成成功: {manifest_file}")
    print(f"  - 总章节数: {total_chapters}")
    print(f"  - 总批次数: {len(batches)} (Batch_001 ~ {batches[-1]['batch_id']})")
    print(f"  - 每批规模: 约 {chapters_per_batch} 章 (8,000~12,000 字)")

if __name__ == "__main__":
    generate_batches()
