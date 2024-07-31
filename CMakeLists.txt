cmake_minimum_required(VERSION 3.15...3.27)

project(${SKBUILD_PROJECT_NAME}
  LANGUAGES C
  VERSION ${SKBUILD_PROJECT_VERSION}
)

option(SDF_XARRAY_UPDATE_GIT_SUBMODULE "Check submodules are up-to-date during build" ON)
# Adapted from https://cliutils.gitlab.io/modern-cmake/chapters/projects/submodule.html
# Update submodules as needed
if(SDF_XARRAY_UPDATE_GIT_SUBMODULE)
  find_package(Git QUIET)
  if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
    message(STATUS "Submodule update")
    execute_process(COMMAND ${GIT_EXECUTABLE} -c submodule.recurse=false submodule update --init --recursive
      WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
      RESULT_VARIABLE GIT_SUBMOD_RESULT)
    if(NOT GIT_SUBMOD_RESULT EQUAL "0")
      message(FATAL_ERROR "git submodule update --init failed with ${GIT_SUBMOD_RESULT}, please checkout submodules")
    endif()
  endif()
endif()

add_subdirectory(SDF/C)

target_include_directories(sdfc PUBLIC
  $<TARGET_FILE_DIR:sdfc>)

find_package(Python COMPONENTS Interpreter Development.Module NumPy REQUIRED)

python_add_library(sdf MODULE SDF/utilities/sdf_python.c WITH_SOABI)
target_link_libraries(sdf PRIVATE sdfc Python::NumPy)

install(TARGETS sdf DESTINATION ${SKBUILD_PROJECT_NAME})
