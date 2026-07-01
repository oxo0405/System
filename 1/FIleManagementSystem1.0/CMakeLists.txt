cmake_minimum_required(VERSION 3.10)
project(filesystem_core)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release)

# 查找Python
find_package(PythonLibs REQUIRED)
find_package(PythonInterp REQUIRED)

# 下载pybind11
include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.10.0
)
FetchContent_MakeAvailable(pybind11)

# 源文件
set(SOURCES
    src/core/FCB.cpp
    src/core/Directory.cpp
    src/core/User.cpp
    src/core/FileSystem.cpp
    src/binding/pybind_wrapper.cpp
)

# 创建共享库
pybind11_add_module(filesystem_core ${SOURCES})

target_include_directories(filesystem_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${PYTHON_INCLUDE_DIRS}
)

target_compile_options(filesystem_core PRIVATE -Wall -Wextra -O3)

target_link_libraries(filesystem_core PRIVATE ${PYTHON_LIBRARIES})

# 设置输出目录
set_target_properties(filesystem_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)
