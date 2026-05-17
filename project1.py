import argparse
import re

def github_alert(match):
    return match.group(1) + match.group(2).upper() + match.group(3)

pattern1 = r"(?<!\\)!\[\[.*?\]\]"
pattern2 = r"\\(!\[\[.*?\]\])"
pattern3 = r"(?<!\\)\[\[.*?\|(.*?)\]\]"
pattern4 = r"(?<!\\)\[\[(.*?)\]\]"
pattern5 = r"(?<=\[)\[(.*?)\](?=\])"
pattern6 = r"(?<!\\)\[(.*?)\](?!\()"

pattern7 = r"^={2,}\s*$"
pattern8 = r"(?<!\\)==((?:(?!\*\*).)*?)=="
pattern9 = r"(?<!\\)==(\S.*?\S|\S)=="

pattern10 = r"^(>\s?\[\!)(.*?)(\])"

def revise_grammar(revise):
    revise = re.sub(pattern1, "", revise)
    revise = re.sub(pattern2, r"\1", revise)
    revise = re.sub(pattern3, r"\1", revise)
    revise = re.sub(pattern4, r"\1", revise)
    revise = re.sub(pattern5, r"\1", revise)
    if not re.match(pattern10, revise):
        revise = re.sub(pattern6, r"\1", revise)

    if not re.match(pattern7, revise):
        if re.search(pattern9, revise):
            revise = re.sub(pattern8, r"\1", revise)
            revise = re.sub(pattern9, r"**\1**", revise)

    revise = re.sub(pattern10, github_alert, revise)

    return revise

def find_inline_code(match):
    match_block = match.group(0)

    if match_block.startswith("`"):
        return match_block
    else:
        return revise_grammar(match_block)

parser = argparse.ArgumentParser(description='옵시디언 마크다운 변환기 (Github에 사용 용도)')
parser.add_argument('file', help="변환할 옵시디언 마크다운 파일 이름")

args = parser.parse_args()
file_name = args.file
new_file_name = file_name[:-3] + '_revised.md'

with open(file_name, 'r', encoding='utf-8') as file:
    sentences = file.readlines()

# file = open(file_name, 'r')는 별로인가 보다

sentence_list = []

pattern_verify = r"`[^`]+`|[^`]+"

in_code_block = False

for i in range(len(sentences)):
    stc = sentences[i].rstrip() + '  \n'

    if stc.strip().startswith('```'):
        in_code_block = not in_code_block
        sentence_list.append(stc)
        continue

    if in_code_block:
        sentence_list.append(stc)
        continue

    stc = re.sub(pattern_verify, find_inline_code, stc)

    sentence_list.append(stc)

with open(new_file_name, 'w', encoding='utf-8') as file_revised:
    file_revised.writelines(sentence_list)
