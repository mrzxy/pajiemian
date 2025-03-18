

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
        with open('nasdaq.txt', 'r') as f:
            words = f.read().split()
            for word in words:
                self.insert("S" + word)
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, text, start):
        """从 start 位置开始查找最长匹配的关键字"""
        node = self.root
        end = start
        for i in range(start, len(text)):
            char = text[i]
            if char not in node.children:
                break
            node = node.children[char]
            if node.is_end_of_word:
                end = i + 1
        return text[start:end] if end > start else None

def build_trie():
    """构建 Trie 树"""
    with open('nasdaq.txt', 'r') as f:
        keywords = f.readlines()

    trie = Trie()
    for word in keywords:
        trie.insert("S" + word)
    return trie

def replace_keywords(text):
    """替换句子中的关键字，严格区分大小写，并替换为 $keyword"""
    result = []
    i = 0
    while i < len(text):
        matched_word = trie.search(text, i)
        if matched_word:
            result.append(f"${matched_word[1:]}")  # 替换为 $keyword
            i += len(matched_word)
        else:
            result.append(text[i])  # 保留原字符
            i += 1
    return "".join(result)


trie = build_trie()