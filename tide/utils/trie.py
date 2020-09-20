from collections import defaultdict
from typing import Optional, Iterable
from dataclasses import dataclass


class Trie:
    def __init__(self):
        self.chars = defaultdict(Trie)
        self.leaf = False
        # count the number of leaves downstream
        self.count = 0

    def find(self, name: str) -> Optional['Trie']:
        """Returns the Trie found for the given word"""
        p = self
        for c in name:
            p = p.chars.get(c)

            if p is None:
                return None

        return p

    def suggest(self, name: str, full_words=True) -> Iterable[str]:
        """Suggest full words to complete the partial string provided

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert('abc', 'abcd')
        >>> sorted(list(trie.suggest('ab')))
        ['abc', 'abcd']
        >>> sorted(list(trie.suggest('ab', full_words=False)))
        ['c', 'cd']
        """
        trie = self.find(name)

        if trie is None:
            return

        partial = trie.words()

        for p in partial:
            if not full_words:
                yield p
            else:
                yield name + p

    def insert(self, *names) -> None:
        """Insert new names into the Trie

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert('abc', 'abcd')
        """
        for n in names:
            self._insert(n)

    def _insert(self, name: str) -> None:
        self.count += 1

        if name == '':
            self.leaf = True
            return

        self.chars[name[0]].insert(name[1:])

    def words(self) -> Iterable[str]:
        """Returns all possible words after that point

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert('abc', 'abcd')
        >>> sorted(list(trie.words()))
        ['abc', 'abcd']
        >>> t = trie.find('abc')
        >>> sorted(list(t.words()))
        ['', 'd']
        """
        for c, trie in self.chars.items():
            partial = trie.words()

            for p in partial:
                yield c + p

        if self.leaf:
            yield ''

    def immediate_words(self):
        """Returns all the available words that we know for sure (no recursive branching)"""
        for c, trie in self.chars.items():
            if trie.count == 1 or trie.leaf:
                partial = trie.immediate_words()

                for p in partial:
                    yield c + p

        if self.leaf:
            yield ''

    def is_bucket_item(self):
        return self.count == 1 or self.leaf

    def is_bucket(self):
        """A bucket is a Trie with more that one leaves"""
        for c, t in self.chars.items():
            if not t.is_bucket_item():
                return False

        return True

    def buckets(self, prefix=''):
        """Returns bucket of words that matches
        This is used to group macro constant together inside an enum

        Examples
        --------
        >>> constant_names = Trie()
        >>> constant_names.insert(
        ...     'SDL_BUTTON_LMASK',
        ...     'SDL_BUTTON_MMASK',
        ...     'SDL_BUTTON_RMASK',
        ...     'SDL_HAT_UP',
        ...     'SDL_HAT_RIGHT',
        ...     'SDL_HAT_DOWN'
        ... )
        >>> for i, bucket in enumerate(constant_names.buckets()):
        ...     print(f'Bucket #{i}')
        ...     for w in bucket.words():
        ...         print(f'    {w}')
        Bucket #0
            SDL_BUTTON_LMASK
            SDL_BUTTON_MMASK
            SDL_BUTTON_RMASK
        Bucket #1
            SDL_HAT_UP
            SDL_HAT_RIGHT
            SDL_HAT_DOWN
        """

        if self.is_bucket():
            yield Bucket(prefix, self)
        else:
            for c, t in self.chars.items():
                buckets = t.buckets(prefix + c)

                for b in buckets:
                    yield b

    def dumps(self, d=0, c=''):
        i = ' ' * d
        print(f'|{i} `{c}` (bucket: {self.is_bucket()}) (count: {self.count}) (len: {len(self.chars)})')

        for c, t in self.chars.items():
            t.dumps(d + 1, c)


@dataclass
class Bucket:
    prefix: str
    trie: Trie

    def words(self):
        for w in self.trie.immediate_words():
            yield self.prefix + w
