#ifndef KIWI_DICT_HEADER
#define KIWI_DICT_HEADER

#include <vector>
#include <unordered_map>
#include <memory>
#include <algorithm>
#include <list>
#include <sstream>

#include "exception.h"

template<typename ...Args>
using tuple = std::tuple<Args...>;

template<typename Iter>
struct Generator {
    Generator(Iter&& b, Iter&& e): _b(std::move(b)), _e(std::move(e)) {}

    Iter begin() {  return _b;}
    Iter end()   {  return _e;}

    Iter _b;
    Iter _e;
};


//template<typename Iterable>
//auto iter(Iterable& obj) -> Generator<std::result_of<decltype(begin)(Iterable*)>::type> {
//    return Generator(std::begin(obj), std::end(obj));
//}


template<typename Impl, typename K, typename V>
struct DictInterface{
public:
    using KeyIterator = typename Impl::KeyIterator;
    using ConstKeyIterator = typename Impl::ConstKeyIterator;

    using ValueIterator = typename Impl::ValueIterator;
    using ConstValueIterator = typename Impl::ConstValueIterator;

    using ItemIterator = typename Impl::ItemIterator;
    using ConstItemIterator = typename Impl::ConstItemIterator;

#define DICT_METHODS(impl)\
    INLINE void          remove     (K const& k) { return (impl).remove(k); }\
    INLINE V             pop        (K const& k) { return (impl).pop(k);}\
    INLINE V             pop        (K const& k, V const& def) { return (impl).pop(k, def);}\
    INLINE V             get        (K const& k, V const& def) const { return (impl).get(k, def);}\
    INLINE void          setdefault (K const& k, V const& def) { return (impl).setdefault(k, def);   }\
    INLINE tuple<K, V>   popitem    ()            { return (impl).popitem();}\
    INLINE void          clear      ()            { return (impl).clear();}\
    INLINE Generator<ConstItemIterator>  items () const      { return (impl).items(); }\
    INLINE Generator<ItemIterator>       items ()            { return (impl).items(); }\
    INLINE Generator<ConstKeyIterator>   keys  () const      { return (impl).keys();}\
    INLINE Generator<KeyIterator>        keys  ()            { return (impl).keys();}\
    INLINE Generator<ConstValueIterator> values() const      { return (impl).values();}\
    INLINE Generator<ValueIterator>      values()            { return (impl).values();}\
    INLINE KeyIterator        begin ()            { return (impl).begin(); }\
    INLINE KeyIterator        end   ()            { return (impl).end();   }\
    INLINE ConstKeyIterator   begin ()      const { return (impl).begin(); }\
    INLINE ConstKeyIterator   end   ()      const { return (impl).end();   }\
    INLINE V const&      operator[] (K const& i)  const { return (impl)[i]; }\
    INLINE V&            operator[] (K const& i)        { return (impl)[i]; }\
    INLINE int           __len__     ()           const { return (impl).__len__(); }\
    INLINE String        __repr__     ()          const { return (impl).__repr__(); }\
    INLINE bool          __contains__(K const& k) const { return (impl).__contains__(k); }\
    template<typename Iterable>\
    INLINE void          update(Iterable const& iterable) { (impl).update(iterable); }\
    INLINE tuple<K, V>&  setitem(K const& k, V const& v) { (impl).setitem(k, v);   }

    DICT_METHODS(*reinterpret_cast<Impl*>(this))
};


// https://softwaremaniacs.org/blog/2020/02/05/dicts-ordered/en/
// Note that we cannot use std::map as it is a sorted map not an ordered map
// sorted  == used compare to insert a new key
// ordered == conserve insertion order
//
// Erasing elements using remove()/pop() in that DS has awful performance
// popitem() would be fine
template<typename K, typename V>
struct OrderedDict{
public:
    template<typename Impl>
    struct _KeyIterator{
        _KeyIterator(Impl iter):
            iter(iter)
        {}

        K& operator* () const {
            return std::get<0>(*iter);
        }

        bool operator != (_KeyIterator const& other) {
            return iter != other.iter;
        }

        _KeyIterator& operator++ () {
            ++iter;
            return *this;
        }

    private:
        Impl iter;
    };

    template<typename Impl>
    struct _ValueIterator{
        _ValueIterator(Impl iter):
            iter(iter)
        {}

        V& operator* () const {
            return std::get<1>(*iter);
        }

        bool operator != (_ValueIterator const& other) {
            return iter != other.iter;
        }

        _ValueIterator& operator++ () {
            ++iter;
            return *this;
        }

    private:
        Impl iter;
    };

    using ItemIterator = typename std::vector<tuple<K, V>>::iterator;
    using ConstItemIterator = typename std::vector<tuple<K, V>>::const_iterator;

    using KeyIterator = _KeyIterator<ItemIterator>;
    using ConstKeyIterator = _KeyIterator<ConstItemIterator>;

    using ValueIterator = _ValueIterator<ItemIterator>;
    using ConstValueIterator = _ValueIterator<ConstItemIterator>;

    tuple<K, V>& setitem(K const& k, V const& v) {
        auto s = _data.size();
        _data.push_back(std::make_tuple(k, v));
        _map[k] = s;
        return *_data.rbegin();
    }

    void setdefault(K const& k, V const& v) {
        if (!__contains__(k)) {
            set_item(k, v);
        }
    }

    V const& operator[] (K const& k) const {
        int i = _map.at(k);
        return std::get<1>(_data[i]);
    }

    String __repr__() const {
        std::stringstream ss;
        ss << "{";

        bool first = true;
        for (auto& item: this->items()){
            if (!first){
                ss << ", ";
            } else {
                first = false;
            }

            ss << "\"" << repr(std::get<0>(item)) << "\": " << repr(std::get<1>(item));
        }

        ss << "}";
        return ss.str();
    }

    V& operator[] (K const& k) {
        if (__contains__(k)) {
            int i = _map[k];
            return std::get<1>(_data[i]);
        }

        return std::get<1>(setitem(k, V()));
    }

    int __len__() const {
        return _data.size();
    }

    bool __contains__(K const& k) const {
        return _map.count(k) == 1;
    }

    void clear(){
        _data.clear();
        _map.clear();
    }

    void remove(K const& k) {
        int i = _map[k];

        _map.erase(k);
        _data.erase(std::begin(_data) + i);
    }

    tuple<K, V> _popitem(K const& k) {
        int i = _map[k];
        auto r = _data[i];

        _map.erase(k);
        _data.erase(std::begin(_data) + i);
        return r;
    }

    V pop(K const& k) {
        auto item = _popitem(k);
        return std::get<1>(item);
    }

    V pop(K const& k, V const& def) {
        if (__contains__(k)){
            return pop(k);
        }

        return def;
    }

    tuple<K, V> popitem() {
        auto k = std::get<0>(*_data.rbegin());
        return _popitem(k);
    }

    V get(K const& k, V const& v) noexcept {
        if (__contains__(k)) {
            return (*this)[k];
        }
        return v;
    }

    Generator<ItemIterator>      items     ()            {
        return Generator<ItemIterator>(std::begin(_data), std::end(_data));
    }
    Generator<ConstItemIterator> items     ()      const {
        return Generator<ConstItemIterator>(std::begin(_data), std::end(_data));
    }

    // return keys
    INLINE Generator<KeyIterator>       keys      ()            {
        return Generator<KeyIterator>(KeyIterator(std::begin(_data)), KeyIterator(std::end(_data)));
    }
    INLINE Generator<ConstKeyIterator>  keys      ()      const {
        return Generator<ConstKeyIterator>(ConstKeyIterator(std::begin(_data)), ConstKeyIterator(std::end(_data)));
    }

    // return values
    INLINE Generator<ValueIterator>      values    ()            {
        return Generator<ValueIterator>(ValueIterator(std::begin(_data)), ValueIterator(std::end(_data)));
    }
    INLINE Generator<ConstValueIterator> values    ()      const {
        return Generator<ConstValueIterator>(ConstValueIterator(std::begin(_data)), ConstValueIterator(std::end(_data)));
    }

private:
    std::vector<tuple<K, V>>   _data;
    std::unordered_map<K, int> _map;
};


// Python list like Object that behaves like a reference
// and not a value like VectorList
template<typename Impl, typename K, typename V>
struct DictRef {
    using KeyIterator = typename Impl::KeyIterator;
    using ConstKeyIterator = typename Impl::ConstKeyIterator;

    using ValueIterator = typename Impl::ValueIterator;
    using ConstValueIterator = typename Impl::ConstValueIterator;

    using ItemIterator = typename Impl::ItemIterator;
    using ConstItemIterator = typename Impl::ConstItemIterator;

    DictRef(): _data(std::make_shared<Impl>())
    {}

    DICT_METHODS(*_data)

    bool is_none() {
        return bool(_data);
    }

private:
    std::shared_ptr<Impl> _data;
};

template<typename K, typename V>
using dict = DictRef<OrderedDict<K, V>, K, V>;

#endif
