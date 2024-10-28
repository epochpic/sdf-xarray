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

add_subdirectory(externals/sdf_c)

target_include_directories(sdfc PUBLIC
  $<TARGET_FILE_DIR:sdfc>)

find_package(Python COMPONENTS Interpreter Development.Module NumPy REQUIRED)

set(_sdf_module_dir "${CMAKE_CURRENT_SOURCE_DIR}/src/sdf_xarray")
set(_sdf_input "${_sdf_module_dir}/sdf_interface.pyx")
set(_sdf_output "sdf_interface.c")
add_custom_command(
  OUTPUT ${_sdf_output}
  COMMENT
    "Making ${CMAKE_CURRENT_BINARY_DIR}/${_sdf_output} from ${_sdf_input}"
  COMMAND Python::Interpreter -m cython
          "${_sdf_input}" --output-file ${_sdf_output}
          "-I${_sdf_module_dir}"
          -3
  DEPENDS "${_sdf_input}"
  VERBATIM)

python_add_library(sdf_interface MODULE ${_sdf_output} WITH_SOABI)
target_link_libraries(sdf_interface PRIVATE sdfc Python::NumPy)
target_compile_definitions(sdf_interface PRIVATE "NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION")

install(TARGETS sdf_interface DESTINATION ${SKBUILD_PROJECT_NAME})
