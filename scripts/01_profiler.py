import os
import json
import shutil
import re
from collections import Counter

def process_file():
    input_file = "input/面壁者但元婴期.txt"
    backup_file = "backup/面壁者但元婴期_backup.txt"
    work_file = "work/working_novel.txt"
    profile_file = "novels_meta/面壁者但元婴期_profile.json"

    shutil.copy2(input_file, backup_file)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_file, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()

    with open(work_file, 'w', encoding='utf-8') as f:
        f.write(content)

    chapters = []
    chapter_pattern = re.compile(r'^\s*(第[零一二三四五六七八九十百千万0-9]+[章回节卷集部].*)$', re.MULTILINE)

    lines = content.split('\n')
    for i, line in enumerate(lines):
        match = chapter_pattern.match(line)
        if match:
            chapters.append({
                "line_number": i + 1,
                "title": match.group(1).strip()
            })

    words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
    counter = Counter(words)
    top_entities = [w for w, c in counter.most_common(50) if c > 10]

    profile = {
        "title": "面壁者但元婴期",
        "total_lines": len(lines),
        "total_chars": len(content),
        "chapters": chapters,
        "canonical_entities": top_entities
    }

    with open(profile_file, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print("Profiler completed successfully.")

if __name__ == '__main__':
    process_file()
