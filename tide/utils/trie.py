from collections import defaultdict
from typing import Optional, Iterable
from dataclasses import dataclass


class Trie:
    def __init__(self):
        self.chars = defaultdict(Trie)
        self.leaf = False
        # used to tokenize words further
        # this is used so redundant_prefix does not cut full words in half
        self.alphanum_boundary = False
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

    def _insert(self, name: str, previous_char=None) -> None:
        self.count += 1

        if name == '':
            self.leaf = True
            return

        if previous_char and not previous_char.isalnum():
            self.alphanum_boundary = True

        self.chars[name[0]]._insert(name[1:], previous_char=name[0])

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

    def redundant_prefix(self):
        """Show how often a prefix is reused

        Issues
        ------
        Does not split after full word, can cut words in half

        Examples
        --------
        >>> names = Trie()
        >>> names.insert(
        ...     'SDL_BUTTON_LMASK',
        ...     'SDL_BUTTON_MMASK',
        ...     'SDL_BUTTON_RMASK',
        ...     'SDL_HAT_UP',
        ...     'SDL_HAT_RIGHT',
        ...     'read_le16',
        ...     'read_le32',
        ... )
        >>> sorted(list(names.redundant_prefix()), key=lambda x: x[1])
        [(3, 'SDL_BUTTON_'), (2, 'SDL_HAT_'), (2, 'read_')]
        """
        counts = dict()
        for w in set(self._redundant_prefix()):
            trie = self.find(w)
            counts[w] = trie.count

        for w, c in counts.items():
            if c > 1 and len(w) > 2:
                yield c, w

    def _redundant_prefix(self, previous_count=None):
        for c, t in self.chars.items():
            if (previous_count and t.count == previous_count) or t.count > 1:
                words = list(self.chars[c]._redundant_prefix(previous_count))

                for w in words:
                    yield c + w

                if len(words) == 0 and self.alphanum_boundary:
                    yield ''

            elif self.alphanum_boundary:
                yield ''

    def dumps(self, d=0, c=''):
        i = ' ' * d
        print(f'|{i} `{c}` (bucket: {self.is_bucket()}) (count: {self.count}) (len: {len(self.chars)}) (boundary: {self.alphanum_boundary})')

        for c, t in self.chars.items():
            t.dumps(d + 1, c)


@dataclass
class Bucket:
    prefix: str
    trie: Trie

    def words(self):
        for w in self.trie.immediate_words():
            yield self.prefix + w
