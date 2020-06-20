#include <vector>
#include <unordered_map>
#include <memory>
#include <algorithm>

#include "exception.h"

template<typename ...Args>
using tuple = std::tuple<Args...>;


template<typename Impl, typename K, typename V>
struct DictInterface{
public:
    using Iterator = typename Impl::Iterator;
    using ConstIterator = typename Impl::ConstIterator;

#define DICT_METHODS(impl)\
    void          remove     (K const& k) { return (impl).remove(k); }\
    V             pop        (K const& k) { return (impl).pop(k);}\
    V             pop        (K const& k, V const& def) { return (impl).pop(k, def);}\
    V             get        (K const& k, V const& def) const { return (impl).get(k, def);}\
    void          setdefault (K const& k, V const& def) { return (impl).setdefault(k, def);   }\
    tuple<K, V>   popitem    ()            { return (impl).popitem();}\
    void          clear      ()            { return (impl).clear();}\
    list<tuple<K, V>> items  () const      { return (impl).items(); }\
    list<K>       keys       () const      {        (impl).reverse();}\
    list<V>       values     () const      {        (impl).copy();}\
    Iterator      begin      ()            { return (impl).begin(); }\
    Iterator      end        ()            { return (impl).end();   }\
    ConstIterator begin      ()      const { return (impl).begin(); }\
    ConstIterator end        ()      const { return (impl).end();   }\
    Iterator      rbegin     ()            { return (impl).rbegin(); }\
    Iterator      rend       ()            { return (impl).rend();   }\
    ConstIterator rbegin     ()      const { return (impl).rbegin(); }\
    ConstIterator rend       ()      const { return (impl).rend();   }\
    T&            operator[] (Key const& i) const { return (impl)[i]; }\
    T&            operator[] (Key const& i)       { return (impl)[i]; }\
    int           __len__     ()     const { return (impl).__len__(); }\
    bool          __contains__()     const { return (impl).__contains__(); }\
    template<typename Iterable>\
    void          update(Iterable const& iterable) { (impl).update(iterable); }\

    DICT_METHODS(*reinterpret_cast<Impl*>(this))
};

// https://softwaremaniacs.org/blog/2020/02/05/dicts-ordered/en/
// Note that we cannot use std::map as it is a sorted map not an ordered map
// sorted  == used compare to insert a new key
// ordered == conserve insertion order
template<typename K, typename V>
struct OrderedDict{
public:




private:
    std::vector<tuple<K, V>>   _data;
    std::unordered_map<K, int> _map;
}


// Python list like Object that behaves like a reference
// and not a value like VectorList
template<typename Impl, typename K, typename V>
struct DictRef {
    using Iterator = typename Impl::Iterator;
    using ConstIterator = typename Impl::ConstIterator;

    DictRef(): _data(std::make_shared<Impl>())
    {}

    DICT_METHODS(*_data)

private:
    std::shared_ptr<Impl> _data;
};

template<typename K, typename V>
using dict = DictRef<OrderedDict<K, V>, K, V>;
