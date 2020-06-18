#include <catch2/catch.hpp>
#include <iterator>

#include "list.h"

//#define TEST_LEXING(code)\
//    SECTION(#code){\
//        REQUIRE(strip(lex_it(code())) == strip(code()));\
//    }




template<typename T>
void check_append(){
    list<T> array;

    for(auto i = 9; i >= 0; --i){
        array.append(i);
    }
    auto idx = array.index(8);
    REQUIRE(array[idx] == 8);

    REQUIRE(len(array) == 10);

    // For range
    REQUIRE(sum(array) == T(45));

    // sort
    array.sort();
    for(auto i = 0; i < 10; ++i){
        REQUIRE(array[i] == T(i));
    }

    // Insert
    array.insert(0, 50);
    REQUIRE(array[0] == T(50));

    // Remove
    array.remove(9);
    REQUIRE(sum(array) == T(45 + 50 - 9));

    // Extend
    list<T> array2;
    for(auto i = 9; i >= 0; --i){
        array2.append(i);
    }
    array.extend(array2);
    REQUIRE(sum(array) == T(45 + 50 - 9 + 45));

    // pop X
    auto v = array.pop(0);
    REQUIRE(v == 50);
    REQUIRE(sum(array) == T(45 - 9 + 45));

    // pop last
    v = array.pop();
    REQUIRE(sum(array) == T(45 - 9 + 45 - v));

    // count
    REQUIRE(array.count(8) == 2);

    // clear
    array.clear();
    REQUIRE(len(array) == 0);
}


TEST_CASE("list"){
    check_append<int>();
}
