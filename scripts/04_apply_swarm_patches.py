#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Step 3.4 汇总应用蜂群补丁 (scripts/04_apply_swarm_patches.py)
1. 读取所有 work/patches_Batch_*.json，将高置信度 (>=0.90) 的 patches 精确替换应用到 work/working_novel.txt。
2. 将所有 uncertain_items 汇总写入 reports/uncertain_review.log。
"""

import os
import glob
import json

def apply_patches():
    work_novel = "work/working_novel.txt"
    work_dir = "work"
    reports_dir = "reports"
    uncertain_file = os.path.join(reports_dir, "uncertain_review.log")

    os.makedirs(reports_dir, exist_ok=True)

    with open(work_novel, "r", encoding="utf-8") as f:
        novel_text = f.read()

    patch_files = sorted(glob.glob(os.path.join(work_dir, "patches_Batch_*.json")))
    print(f"[ApplyPatches] 找到 {len(patch_files)} 个批次补丁文件。")

    applied_count = 0
    skipped_count = 0
    all_uncertain = []

    for pf in patch_files:
        with open(pf, "r", encoding="utf-8") as f:
            data = json.load(f)

        patches = data.get("patches", [])
        for p in patches:
            orig = p.get("original_snippet", "")
            fixed = p.get("fixed_snippet", "")
            conf = p.get("confidence", 1.0)
            reason = p.get("reason", "")

            if not orig or not fixed or orig == fixed:
                continue

            if conf >= 0.90:
                if orig in novel_text:
                    novel_text = novel_text.replace(orig, fixed)
                    applied_count += 1
                else:
                    skipped_count += 1
            else:
                all_uncertain.append({
                    "batch": data.get("batch_id"),
                    "chapter": p.get("chapter"),
                    "snippet": orig,
                    "reason": f"Low confidence ({conf}): {reason}"
                })

        for u in data.get("uncertain_items", []):
            all_uncertain.append({
                "batch": data.get("batch_id"),
                "chapter": u.get("chapter"),
                "snippet": u.get("snippet"),
                "reason": u.get("reason")
            })

    # 写回 working_novel.txt
    with open(work_novel, "w", encoding="utf-8") as f:
        f.write(novel_text)

    # 写入 uncertain_review.log
    with open(uncertain_file, "w", encoding="utf-8") as f:
        f.write(f"# 低置信度存疑条目审查清单 (Total: {len(all_uncertain)})\n\n")
        for idx, item in enumerate(all_uncertain, 1):
            f.write(f"[{idx}] 批次: {item.get('batch')} | 章节: {item.get('chapter')}\n")
            f.write(f"    原文: {item.get('snippet')}\n")
            f.write(f"    存疑原因: {item.get('reason')}\n\n")

    print(f"[ApplyPatches] 补丁合入完成！")
    print(f"  - 成功应用高置信度补丁: {applied_count} 处")
    print(f"  - 未匹配跳过: {skipped_count} 处")
    print(f"  - 存疑条目记录: {len(all_uncertain)} 处，已写入 {uncertain_file}")

if __name__ == "__main__":
    apply_patches()
