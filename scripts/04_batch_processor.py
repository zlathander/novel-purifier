import json
import re
import os

def process_batches():
    manifest_file = "reports/audit_manifest.json"
    work_file = "work/working_novel.txt"
    cases_file = "memory/contextual_cases.json"

    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    with open(work_file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    with open(cases_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    name_drift = cases.get("name_drift", [])
    phrase_drift = cases.get("phrase_drift", [])

    for batch_idx, batch in enumerate(manifest["batches"]):
        if batch["status"] == "COMPLETED":
            continue

        batch_id = batch["batch_id"]
        start_line = batch["start_line"]
        end_line = batch["end_line"]

        patches = []

        for i in range(start_line, end_line + 1):
            if i >= len(lines):
                break

            original_line = lines[i]
            new_line = original_line

            for drift in name_drift:
                if len(drift) >= 2:
                    wrong, right = drift[0], drift[1]
                    if wrong in new_line:
                        new_line = new_line.replace(wrong, right)

            for drift in phrase_drift:
                if len(drift) >= 2:
                    wrong, right = drift[0], drift[1]
                    if wrong in new_line:
                        new_line = new_line.replace(wrong, right)

            new_line = new_line.replace('战土', '战士').replace('未日', '末日')

            new_line = re.sub(r'「([^「」]+)「', r'「\1」', new_line)
            new_line = re.sub(r'［注\d+］', '', new_line)

            if new_line != original_line:
                patches.append({
                    "line_number": i + 1,
                    "original": original_line,
                    "fixed": new_line
                })
                lines[i] = new_line

        patch_file = f"work/patches_{batch_id}.json"
        with open(patch_file, 'w', encoding='utf-8') as f:
            json.dump(patches, f, ensure_ascii=False, indent=2)

        batch["status"] = "COMPLETED"

    with open(work_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("Batch processing completed.")

if __name__ == '__main__':
    process_batches()
