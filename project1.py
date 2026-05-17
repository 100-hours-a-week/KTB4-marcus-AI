import argparse
import re

def github_alert(match):
    return match.group(1) + match.group(2).upper() + match.group(3)

parser = argparse.ArgumentParser(description='옵시디언 마크다운 변환기 (Github에 사용 용도)')
parser.add_argument('file', help="변환할 옵시디언 마크다운 파일 이름")

args = parser.parse_args()
file_name = args.file
new_file_name = file_name[:-3] + '_revised.md'


with open(file_name, 'r', encoding='utf-8') as file:
    sentences = file.readlines()

sentence_list = []

pattern1 = r"(?<!\\)\!\[\[.*?\]\]"
pattern2 = r"\\!(\[\[.*?\]\])"
pattern3 = r"(?<!\\)\[\[.*?\|(.*?)\]\]"
pattern4 = r"(?<!\\)\[\[(.*?)\]\]"
pattern5 = r"(?<=\[)\[(.*?)\](?=\])"
pattern6 = r"(?<!\\)\[(.*?)\](?!\()"

pattern7 = r"^={2,}\s*$"
pattern8 = r"(?<!\\)==(\S.*?\S|\S)=="

pattern9 = r"^(>\s?\[\!)(.*?)(\])"

for i in range(len(sentences)):    
    revise = sentences[i].rstrip() + '  \n'

    revise = re.sub(pattern1, "", revise)
    revise = re.sub(pattern2, r"!\1", revise)
    revise = re.sub(pattern3, r"\1", revise)
    revise = re.sub(pattern4, r"\1", revise)
    revise = re.sub(pattern5, r"\1", revise)
    if not re.match(pattern9, revise):
        revise = re.sub(pattern6, r"\1", revise)

    if not re.match(pattern7, revise):
        revise = re.sub(pattern8, r"**\1**", revise)

    revise = re.sub(pattern9, github_alert, revise)

    sentence_list.append(revise)

with open(new_file_name, 'w', encoding='utf-8') as file_revised:
    file_revised.writelines(sentence_list)