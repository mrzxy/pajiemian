



class TrieNode:
    def __init__(self):
        self.children = {}
        self.end_word = None


def build_trie():
    with open('nasdaq.txt', 'r') as f:
        keywords = [line.strip() for line in f]
    root = TrieNode()
    replacements = {word: "$" + word[1:] if word.startswith("S") else word for word in keywords}
    for word, replacement in replacements.items():
        node = root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.end_word = replacement  # 存储最终替换内容
    return root


def replace_keywords(text):
    result = []
    i, n = 0, len(text)
    while i < n:
        node = trie
        j = i
        match = None
        while j < n and text[j] in node.children:
            node = node.children[text[j]]
            j += 1
            if node.end_word:  # 找到最长匹配
                match = (i, j, node.end_word)

        if match:
            result.append(match[2])  # 替换匹配到的单词
            i = match[1]  # 跳过匹配的部分
        else:
            result.append(text[i])
            i += 1

    return ''.join(result)


trie = build_trie()