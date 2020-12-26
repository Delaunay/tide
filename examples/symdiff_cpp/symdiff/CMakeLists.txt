cmake_minimum_required(VERSION 3.1)

project(
  ModernCMakeExample
  VERSION 1.0
  LANGUAGES CXX)

SET(CMAKE_CXX_STANDARD 20)
SET(CXX_STANDARD_REQUIRED ON)

set(SOURCES
    __init__.cpp
    __init__.h
    CMakeLists.txt
    expression.cpp
    expression.h
    solve.cpp
    solve.h
    kiwi
)
add_library(symdiff ${SOURCES})

# add_executable(MyExample simple_example.cpp)
# target_link_libraries(MyExample PUBLIC MyLibExample)