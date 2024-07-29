cmake_minimum_required(VERSION 3.15...3.27)

project(${SKBUILD_PROJECT_NAME}
  LANGUAGES C
  VERSION ${SKBUILD_PROJECT_VERSION}
)

add_subdirectory(SDF/C)

target_include_directories(sdfc PUBLIC
  $<TARGET_FILE_DIR:sdfc>)

find_package(Python COMPONENTS Interpreter Development.Module NumPy REQUIRED)

python_add_library(sdf MODULE SDF/utilities/sdf_python.c WITH_SOABI)
target_link_libraries(sdf PRIVATE sdfc Python::NumPy)

install(TARGETS sdf DESTINATION ${SKBUILD_PROJECT_NAME})
