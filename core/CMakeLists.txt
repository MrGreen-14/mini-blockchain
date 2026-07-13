cmake_minimum_required(VERSION 3.20)
project(mini_blockchain_core LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenSSL REQUIRED)

add_executable(blockchain_core
    src/main.cpp
 "include/block.h" "include/block.cpp")

target_include_directories(blockchain_core PRIVATE include)
target_link_libraries(blockchain_core PRIVATE OpenSSL::Crypto)