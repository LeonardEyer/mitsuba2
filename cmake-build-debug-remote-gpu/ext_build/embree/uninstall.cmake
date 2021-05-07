## Copyright 2009-2020 Intel Corporation
## SPDX-License-Identifier: Apache-2.0

IF(NOT EXISTS "/home/leonard/mitsuba2/cmake-build-debug-remote-gpu/ext_build/embree/install_manifest.txt")
  MESSAGE(FATAL_ERROR "Cannot find install manifest: /home/leonard/mitsuba2/cmake-build-debug-remote-gpu/ext_build/embree/install_manifest.txt")
ENDIF(NOT EXISTS "/home/leonard/mitsuba2/cmake-build-debug-remote-gpu/ext_build/embree/install_manifest.txt")

FILE(READ "/home/leonard/mitsuba2/cmake-build-debug-remote-gpu/ext_build/embree/install_manifest.txt" files)
STRING(REGEX REPLACE "\n" ";" files "${files}")
FOREACH(file ${files})
  MESSAGE(STATUS "Uninstalling $ENV{DESTDIR}${file}")
  IF(IS_SYMLINK "$ENV{DESTDIR}${file}" OR EXISTS "$ENV{DESTDIR}${file}")
    EXEC_PROGRAM(
      "/usr/bin/cmake" ARGS "-E remove \"$ENV{DESTDIR}${file}\""
      OUTPUT_VARIABLE rm_out
      RETURN_VALUE rm_retval
      )
    IF(NOT "${rm_retval}" STREQUAL 0)
      MESSAGE(FATAL_ERROR "Problem when removing $ENV{DESTDIR}${file}")
    ENDIF(NOT "${rm_retval}" STREQUAL 0)
  ELSE(IS_SYMLINK "$ENV{DESTDIR}${file}" OR EXISTS "$ENV{DESTDIR}${file}")
    MESSAGE(STATUS "File $ENV{DESTDIR}${file} does not exist.")
  ENDIF(IS_SYMLINK "$ENV{DESTDIR}${file}" OR EXISTS "$ENV{DESTDIR}${file}")
ENDFOREACH(file)
