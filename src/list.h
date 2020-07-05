#ifndef KIWI_LIST_HEADER
#define KIWI_LIST_HEADER
#include <vector>
#include <memory>
#include <algorithm>
#include <string>
#include <sstream>

#include "exception.h"

struct Slice {
    int start;
    int end;
    int step;

    Slice(int s = 0, int e = -1, int step=1):
        start(s), end(e), step(step)
   {}
};

using String = std::string;

template<typename Iterable>
using IteratorValue = typename Iterable::Iterator::value_type;

template<typename Iterable>
IteratorValue<Iterable> sum(Iterable const& iterable) {
    IteratorValue<Iterable> sum = 0;
    for(auto& v: iterable){
        sum += v;
    }
    return sum;
}

template<typename Iterable>
int len(Iterable const& iter) {
    return iter.__len__();
}

template<typename Iterable, typename K>
int contains(Iterable const& iter, K const& k) {
    return iter.__contains__(k);
}

template<typename T>
String repr(T const& obj){
    return obj.__repr__();
}

template<>
String repr(int const& obj){
    return std::to_string(obj);
}

template<>
String repr(float const& obj){
    return std::to_string(obj);
}

template<>
String repr(String const& obj){
    return obj;
}

// Python like Generator that can be used in a for range loop
//template<typename T>
//struct Generator {
//    using Iterator = typename T::iterator;
//
//    Iterator begin() { return std::begin(data); }
//    Iterator end()   { return std::end(data);   }
//
//    T& data;
//};

// Python List Interface
template<typename Impl, typename T>
struct ListInterface {
public:
    using Iterator = typename Impl::Iterator;
    using ConstIterator = typename Impl::ConstIterator;

#define LIST_METHODS(impl)\
    INLINE void          remove     (T v)         { return (impl).remove(v);}\
    INLINE T             pop        ()            { return (impl).pop();    }\
    INLINE T             pop        (int i)       { return (impl).pop(i);   }\
    INLINE void          clear      ()            { return (impl).clear();  }\
    INLINE void          insert     (int i, T v)  { return (impl).insert(i, v);}\
    INLINE int           count      (T x)   const { return (impl).count(x); }\
    INLINE void          sort       ()            { return (impl).sort();   }\
    INLINE void          reverse    ()            {        (impl).reverse();}\
    INLINE void          copy       ()            {        (impl).copy();   }\
    INLINE Iterator      begin      ()            { return (impl).begin();  }\
    INLINE Iterator      end        ()            { return (impl).end();    }\
    INLINE ConstIterator begin      ()      const { return (impl).begin();  }\
    INLINE ConstIterator end        ()      const { return (impl).end();    }\
    INLINE Iterator      rbegin     ()            { return (impl).rbegin(); }\
    INLINE Iterator      rend       ()            { return (impl).rend();   }\
    INLINE ConstIterator rbegin     ()      const { return (impl).rbegin(); }\
    INLINE ConstIterator rend       ()      const { return (impl).rend();   }\
    INLINE void          append     (T v)         {        (impl).append(v);}\
    INLINE T&            operator[] (int i) const { return (impl)[i];       }\
    INLINE T&            operator[] (int i)       { return (impl)[i];       }\
    INLINE String        __repr__   ()      const { return (impl).__repr__(); }\
    INLINE int           __len__    ()      const { return (impl).__len__(); }\
    template<typename Iterable>\
    INLINE void          extend(Iterable const& iterable) { (impl).extend(iterable); }\
    INLINE int           index (T x, int start = 0, int end = 0) const {return (impl).index(x, start, end);}

    LIST_METHODS(*reinterpret_cast<Impl*>(this))
};

// Implementation of Python list using std::vector
template<typename T>
struct VectorList {
public:
    template<typename Iterable>
    INLINE void extend(Iterable const& iterable) {
        _data.insert(_data.end(), std::begin(iterable), std::end(iterable));
    }

    String        __repr__   ()      const {
        std::stringstream ss;
        ss << "[";
        bool first = true;
        for (auto& item: *this){
            if (!first){
                ss << ", ";
            } else {
                first = false;
            }

            ss << repr(item);
        }
        ss << "]";
        return ss.str();
    }

    void remove(T v) {
        auto iter = std::begin(_data);
        while (iter != std::end(_data)) {
            if (v == *iter) {
                _data.erase(iter);
                return;
            }
            iter += 1;
        }

        throw ValueError("Value {} not found", v);
    }

    T pop() {
        T val = *std::rbegin(_data);
        _data.pop_back();
        return val;
    }

    T pop(int i) {
        auto pos = std::begin(_data) + i;
        T val = *(pos);
        _data.erase(pos);
        return val;
    }

    INLINE void clear() {
        _data.clear();
    }

    int index(T x, int start = 0, int end = 0) const {
        auto begin = std::begin(_data) + start;
        if (end == 0){
        }
        auto finish = std::begin(_data) + end;
        if (end == 0){
            finish = std::end(_data);
        }

        auto it = std::find(begin, finish, x);

        if (it == std::end(_data)){
            throw ValueError("Value {} not found", x);
        }
        return it - std::begin(_data);
    }

    INLINE void insert(int i, T v) {
        _data.insert(std::begin(_data) + i, v);
    }

    INLINE int count(T x) const {
        return std::count(std::begin(_data), std::end(_data), x);
    }

    INLINE void sort() {
        std::sort(std::begin(_data), std::end(_data));
    }

    void reverse() {}

    void copy() {}

    using Iterator = typename std::vector<T>::iterator;
    INLINE Iterator begin() { return std::begin(_data); }
    INLINE Iterator end()   { return std::end(_data);   }

    using ConstIterator = typename std::vector<T>::const_iterator;
    INLINE ConstIterator begin() const { return std::begin(_data); }
    INLINE ConstIterator end()   const { return std::end(_data);   }

    INLINE Iterator rbegin() { return std::rbegin(_data); }
    INLINE Iterator rend()   { return std::rend(_data);   }

    INLINE ConstIterator rbegin() const { return std::rbegin(_data); }
    INLINE ConstIterator rend()   const { return std::rend(_data);   }

    INLINE void append     (T v)         { _data.push_back(v); }
    INLINE T&   operator[] (int i) const { return _data[i];     }
    INLINE T&   operator[] (int i)       { return _data[i];     }

    INLINE int __len__() const {
        return _data.size();
    }

    bool is_none() {
        return bool(_data);
    }
private:
    std::vector<T> _data;
};


// Python list like Object that behaves like a reference
// and not a value like VectorList
template<typename Impl, typename T>
struct ListRef {
    using Iterator = typename Impl::Iterator;
    using ConstIterator = typename Impl::ConstIterator;

    ListRef(): _data(std::make_shared<Impl>())
    {}

    LIST_METHODS(*_data)

    bool is_none() {
        return bool(_data);
    }

private:
    std::shared_ptr<Impl> _data;
};

// This is what the user should be interfacing with
// to get the Python experience
template<typename T>
using list = ListRef<VectorList<T>, T>;

#endif
