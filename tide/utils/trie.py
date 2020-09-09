from collections import defaultdict
from typing import Optional, Iterable


class Trie:
    def __init__(self):
        self.chars = defaultdict(Trie)
        self.leaf = False

    def find(self, name: str) -> Optional['Trie']:
        p = self
        for c in name:
            p = p.chars.get(c)

            if p is None:
                return None

        return p

    def suggest(self, name: str) -> Iterable[str]:
        trie = self.find(name)

        if trie is None:
            return

        partial = trie.words()

        for p in partial:
            yield name + p

    def insert(self, name: str) -> None:
        if name == '':
            self.leaf = True
            return

        self.chars[name[0]].insert(name[1:])

    def words(self) -> Iterable[str]:
        for c, trie in self.chars.items():
            partial = trie.words()

            for p in partial:
                yield c + p

        if self.leaf:
            yield ''


if __name__ == '__main__':

    t = Trie()
    t.insert('abc')
    t.insert('abcd')
    t.insert('babcd')

    print(list(t.suggest('dbc')))

    print(list(t.words()))
