import fitz

import re

def split_string_multiple_delimiters(text, delimiters):
    pattern = '|'.join(map(re.escape, delimiters))
    return re.split(pattern, text)


with open("/home/swarup/workspace/spring25/distsys/final-project-feynman/milestone-4/distributed-rag/services/document-processor/src/uploaded_test.pdf", "rb") as f:
    pdf_bytes = f.read()

text = ""
with fitz.open(stream=pdf_bytes, filename="pdf") as doc:
    for page in doc:
        text += page.get_text()

# l = s.split_text(text)

l = split_string_multiple_delimiters(text, [". ", ".\n", "\n\n"])

print(len(l))

for ele in l:
    print("\n\nCHUNK: ", ele)