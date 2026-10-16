import json
import re
import os

def prewash():
    work_file = "work/working_novel.txt"
    rules_file = "memory/deterministic_rules.json"

    with open(rules_file, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    with open(work_file, 'r', encoding='utf-8') as f:
        content = f.read()

    for rule in rules.get("regex_replacements", []):
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        content = re.sub(pattern, replacement, content)

    for rule in rules.get("exact_matches", []):
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        content = content.replace(pattern, replacement)

    content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    content = re.sub(r'（求追读）', '', content)
    content = re.sub(r'（求推荐票）', '', content)
    content = re.sub(r'\(求推荐票\)', '', content)
    content = re.sub(r'（求月票）', '', content)
    content = re.sub(r'【求月票】', '', content)
    content = re.sub(r'请记住本书首发域名：.*', '', content)
    content = re.sub(r'最新网址：.*', '', content)
    content = re.sub(r'无弹窗小说网.*', '', content)

    with open(work_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Mechanical prewash completed.")

if __name__ == '__main__':
    prewash()
