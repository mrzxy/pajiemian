import re

class TrieNode:
    def __init__(self):
        self.children = {}
        self.end_word = None


def build_trie():
    # 假设这是你的 6000 个关键字列表
    keywords = []
    with open('nasdaq.txt', 'r') as f:
        for line in f:
            keywords.append("S" + line.strip())
            keywords.append("$" + line.strip())


    # 将关键字按长度从长到短排序，避免短关键字被长关键字包含
    keywords_sorted = sorted(keywords, key=lambda x: -len(x))

    # 构建正则表达式模式，确保只匹配整个单词
    pattern = re.compile(r'\b(' + '|'.join(re.escape(keyword) for keyword in keywords_sorted) + r')\b')

    return pattern


pattern = build_trie()


def match_f(match):
    keyword = match.group(0)
    if not keyword.startswith('$'):
        return f"${keyword[1:]}"  # 去掉第一个字符并在前面加上 $
    return keyword

def replace_keywords(text):
    return pattern.sub(match_f, text)


if __name__ == '__main__':

    # 替换函数，将匹配的关键字替换为对应的形式

    # 示例句子
    sentence = "$ZYXI is a company, STSLA is a car brand, and SQQQ is another keyword. SLA and TSLA are also here."

    result = replace_keywords(sentence)

    print(result)