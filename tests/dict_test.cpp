#include <catch2/catch.hpp>
#include <iterator>

#include <iostream>


#include "list.h"
#include "dict.h"

//#define TEST_LEXING(code)\
//    SECTION(#code){\
//        REQUIRE(strip(lex_it(code())) == strip(code()));\
//    }

void mutate_dict(dict<std::string, int> val){
    val["def"] = 3;
}

template<typename T>
void check_dict(){
    dict<std::string, T> data;

    data["abc"] = 1;
    data["def"] = 2;

    data["123"] = 2;

    REQUIRE(len(data) == 3);

    REQUIRE(contains(data, "123") == true);
    data.remove("123");
    REQUIRE(contains(data, "123") == false);

    mutate_dict(data);

    REQUIRE(data["def"] == T(3));
    REQUIRE(contains(data, "def") == true);

    {
        T val = data.pop("abc");
        REQUIRE(val == T(1));
    }

    {
        T val = data.pop("do-not-exist", 213);
        REQUIRE(val == T(213));
    }

    {
        data["new-key"] = 12;
        tuple<std::string, T> val = data.popitem();
        REQUIRE(std::get<1>(val) == T(12));
        REQUIRE(std::get<0>(val) == "new-key");
    }

    {
        T val = data.get("213", 2);
        REQUIRE(val == 2);
    }

    for (auto& item: data.items()){
        std::cout << std::get<0>(item) << " "
                  << std::get<1>(item) << "\n";
    }

    for (auto& val: data.values()){
        std::cout << val << "\n";
    }

    for (auto& val: data.keys()){
        std::cout << val << "\n";
    }

    std::cout << repr(data) << "\n";
}


TEST_CASE("dict"){
    check_dict<int>();
}
