cmake_minimum_required(VERSION 3.16)
project(AudioProcessing LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(DCMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/libs_c")
set(DEPS_DIR   "${CMAKE_CURRENT_LIST_DIR}/libs_c/deps")

#python
set(PYBIND11_FINDPYTHON NEW)
# pybind11
add_subdirectory(${DEPS_DIR}/pybind11)

# Módulo Python
pybind11_add_module(leq_levels_oct_weighting_C
  ${SOURCE_DIR}/bindings.cpp
  ${SOURCE_DIR}/utils.cpp
)

# NumCpp: header-only
target_include_directories(leq_levels_oct_weighting_C PRIVATE
  ${DEPS_DIR}/NumCpp/include
)

# Evitar Boost (tamaño + dependencias)
target_compile_definitions(leq_levels_oct_weighting_C PRIVATE
  NUMCPP_NO_USE_BOOST
)

# Optimizar para tamaño
target_compile_options(leq_levels_oct_weighting_C PRIVATE
  -Os -ffunction-sections -fdata-sections
  -fvisibility=hidden -fvisibility-inlines-hidden
)

target_link_options(leq_levels_oct_weighting_C PRIVATE
  -Wl,--gc-sections
)
