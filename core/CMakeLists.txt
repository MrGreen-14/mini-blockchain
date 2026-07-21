cmake_minimum_required(VERSION 3.20)
project(mini_blockchain_core LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenSSL REQUIRED)

set(CORE_SOURCES
    include/block.h
    src/block.cpp
    include/sha256.h
    src/sha256.cpp
    include/blockchain.h
    src/blockchain.cpp
    include/mining.h
    src/mining.cpp
    include/transaction.h
    src/transaction.cpp
    include/merkle.h
    src/merkle.cpp
    include/persistence.h
    src/persistence.cpp
    include/export.h 
    include/bridge_test.h 
    src/bridge_test.cpp
    include/wallet.h
    src/wallet.cpp
)

add_executable(blockchain_core
    src/main.cpp
    ${CORE_SOURCES}
  )
target_include_directories(blockchain_core PRIVATE include)
target_link_libraries(blockchain_core PRIVATE OpenSSL::Crypto)

add_library(blockchain_shared SHARED
    ${CORE_SOURCES}
 )
target_include_directories(blockchain_shared PRIVATE include)
target_link_libraries(blockchain_shared PRIVATE OpenSSL::Crypto)
target_compile_definitions(blockchain_shared PRIVATE BUILDING_SHARED_LIB)

set_target_properties(blockchain_shared PROPERTIES
    OUTPUT_NAME "blockchain_core"
)