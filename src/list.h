#include <vector>
#include <memory>
#include <algorithm>

#include "exception.h"

struct Slice {
    int start;
    int end;
    int step;

    Slice(int s = 0, int e = -1, int step=1):
        start(s), end(e), step(step)
   {}
};

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

// Python List Interface
template<typename Impl, typename T>
struct ListInterface {
public:
    using Iterator = typename Impl::Iterator;
    using ConstIterator = typename Impl::ConstIterator;

#define LIST_METHODS(impl)\
    void          remove     (T v)         { return (impl).remove(v); }\
    T             pop        ()            { return (impl).pop();}\
    T             pop        (int i)       { return (impl).pop(i);}\
    void          clear      ()            { return (impl).clear();}\
    void          insert     (int i, T v)  { return (impl).insert(i, v);}\
    int           count      (T x)   const { return (impl).count(x);}\
    void          sort       ()            { return (impl).sort(); }\
    void          reverse    ()            {        (impl).reverse();}\
    void          copy       ()            {        (impl).copy();}\
    Iterator      begin      ()            { return (impl).begin(); }\
    Iterator      end        ()            { return (impl).end();   }\
    ConstIterator begin      ()      const { return (impl).begin(); }\
    ConstIterator end        ()      const { return (impl).end();   }\
    Iterator      rbegin     ()            { return (impl).rbegin(); }\
    Iterator      rend       ()            { return (impl).rend();   }\
    ConstIterator rbegin     ()      const { return (impl).rbegin(); }\
    ConstIterator rend       ()      const { return (impl).rend();   }\
    void          append     (T v)         {        (impl).append(v);   }\
    T&            operator[] (int i) const { return (impl)[i]; }\
    T&            operator[] (int i)       { return (impl)[i]; }\
    int           __len__    ()      const { return (impl).__len__(); }\
    template<typename Iterable>\
    void          extend(Iterable const& iterable) { (impl).extend(iterable); }\
    int           index (T x, int start = 0, int end = 0) const {return (impl).index(x, start, end);}

    LIST_METHODS(*reinterpret_cast<Impl*>(this))
};

// Implementation of Python list using std::vector
template<typename T>
struct VectorList {
public:
    template<typename Iterable>
    void extend(Iterable const& iterable) {
        _data.insert(_data.end(), std::begin(iterable), std::end(iterable));
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

    void clear() {
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

    void insert(int i, T v) {
        _data.insert(std::begin(_data) + i, v);
    }

    int count(T x) const {
        return std::count(std::begin(_data), std::end(_data), x);
    }

    void sort() {
        std::sort(std::begin(_data), std::end(_data));
    }

    void reverse() {}

    void copy() {}

    using Iterator = typename std::vector<T>::iterator;
    Iterator begin() { return std::begin(_data); }
    Iterator end()   { return std::end(_data);   }

    using ConstIterator = typename std::vector<T>::const_iterator;
    ConstIterator begin() const { return std::begin(_data); }
    ConstIterator end()   const { return std::end(_data);   }

    Iterator rbegin() { return std::rbegin(_data); }
    Iterator rend()   { return std::rend(_data);   }

    ConstIterator rbegin() const { return std::rbegin(_data); }
    ConstIterator rend()   const { return std::rend(_data);   }

    void append     (T v)         { _data.push_back(v); }
    T&   operator[] (int i) const { return _data[i];     }
    T&   operator[] (int i)       { return _data[i];     }

    int __len__() const {
        return _data.size();
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

private:
    std::shared_ptr<Impl> _data;
};

// This is what the user should be interfacing with
// to get the Python experience
template<typename T>
using list = ListRef<VectorList<T>, T>;

