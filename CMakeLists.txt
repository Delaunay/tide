﻿CMAKE_MINIMUM_REQUIRED(VERSION 3.9)

# project name + language used
PROJECT(tide CXX)

# debug/release
SET(CMAKE_RELEASE_POSTFIX "")
SET(CMAKE_DEBUG_POSTFIX "-debug")

# Compiler-flag
IF(${CMAKE_BUILD_TYPE} MATCHES "Debug")
    MESSAGE(STATUS "Building Debug Version")
    ADD_DEFINITIONS(-O0)
    IF(UNIX)
        ADD_LINK_OPTIONS(-rdynamic)
    ENDIF(UNIX)
ELSE()
    MESSAGE(STATUS "Building Release Version")
    #  causes: nvcc fatal   : redefinition of argument 'optimize'
    # ADD_DEFINITIONS(-O2)
ENDIF()

# specify where compiled files must go
SET(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
SET(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
SET(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# add cmake FindXXX script to find pre-compiled libraries if any
LIST(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

# Project's Options
# ====================================

OPTION(BUILD_TESTING        "Enable tests"       ON)
OPTION(BUILD_BENCHMARK      "Build Benchmarks"   ON)
OPTION(BUILD_DOCUMENTATION  "Build docs"         OFF)
OPTION(BUILD_DOXYGEN        "Build Doxygen docs" ON)
OPTION(BUILD_SPHINX         "Build Sphinx docs"  ON)

# Binary/pre-compiled Dependencies
# ====================================
SET(CMAKE_CXX_STANDARD 20)
SET(CXX_STANDARD_REQUIRED ON)

# FIND_PACKAGE(Boost REQUIRED)
FIND_PACKAGE(Git REQUIRED)

# CMake Exentions
# ====================================

# Find revision ID and hash of the sourcetree
INCLUDE_DIRECTORIES(${CMAKE_BINARY_DIR})
INCLUDE(genrev)
IF(UNIX)
    INCLUDE(CodeCoverage)
    append_coverage_compiler_flags()
    SET(COVERAGE_EXCLUDES "${PROJECT_SOURCE_DIR}/dependencies/*")
ENDIF (UNIX)
# Subdirectories
# ====================================

# Dependencies to be compiled
ADD_SUBDIRECTORY(dependencies)

# How to compile main libs
ADD_SUBDIRECTORY(src)

# Tests and Coverage
IF(BUILD_TESTING)
    ENABLE_TESTING()
    MESSAGE(STATUS "Building tests")
    ADD_SUBDIRECTORY(tests)
ENDIF(BUILD_TESTING)

#IF (BUILD_BENCHMARK)
#    MESSAGE(STATUS "Building Benchmarks")
#    ADD_SUBDIRECTORY(benchmark)
#ENDIF(BUILD_BENCHMARK)

# Gen doc ?
#IF (BUILD_DOCUMENTATION)
#    MESSAGE(STATUS "Documentation building is enabled")
#    ADD_SUBDIRECTORY(docs)
#ENDIF (BUILD_DOCUMENTATION)


# Helper commands
# ====================================
# so you do not have to leave the command line
# or remember the exact arguments

ADD_CUSTOM_TARGET(enable-examples
    cmake -DBUILD_EXAMPLES=ON ${CMAKE_SOURCE_DIR})

ADD_CUSTOM_TARGET(disable-examples
    cmake -DBUILD_EXAMPLES=OFF ${CMAKE_SOURCE_DIR})

ADD_CUSTOM_TARGET(enable-release
    cmake -DCMAKE_BUILD_TYPE=Release ${CMAKE_SOURCE_DIR})

ADD_CUSTOM_TARGET(enable-debug
    cmake -DCMAKE_BUILD_TYPE=Debug ${CMAKE_SOURCE_DIR})

ADD_CUSTOM_TARGET(enable-test
    cmake -DBUILD_TESTING=ON ${CMAKE_SOURCE_DIR})

# Resource Files
# ====================================
# Some IDEs need the files to be inside a cmake target to be displayed

ADD_CUSTOM_TARGET(zothers ALL SOURCES
    README.rst
    .travis.yml
    .gitignore
    .gitmodules
)


