import json
import re

def generate_batches():
    work_file = "work/working_novel.txt"
    manifest_file = "reports/audit_manifest.json"

    with open(work_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    chapter_pattern = re.compile(r'^\s*(第[零一二三四五六七八九十百千万0-9]+[章回节卷集部].*)$')

    chapter_indices = []
    for i, line in enumerate(lines):
        if chapter_pattern.match(line):
            chapter_indices.append(i)

    if not chapter_indices:
        chapter_indices = [0]

    batches = []
    chapters_per_batch = 5

    for i in range(0, len(chapter_indices), chapters_per_batch):
        start_line = chapter_indices[i]

        if i + chapters_per_batch < len(chapter_indices):
            end_line = chapter_indices[i + chapters_per_batch] - 1
        else:
            end_line = len(lines) - 1

        batch_id = f"Batch_{len(batches) + 1:03d}"
        batches.append({
            "batch_id": batch_id,
            "start_line": start_line,
            "end_line": end_line,
            "status": "PENDING"
        })

    manifest = {
        "batches": batches
    }

    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Batch manifest generated with {len(batches)} batches.")

if __name__ == '__main__':
    generate_batches()
