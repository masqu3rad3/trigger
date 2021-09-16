cmake_minimum_required(VERSION 2.8)

include(RezBuild)

file(GLOB_RECURSE py_files "python/*.py")
rez_install_files(
    ${py_files}
    DESTINATION .
)


file(GLOB_RECURSE mod_files "python/*.mod")
rez_install_files(
    ${mod_files}
    DESTINATION .
)


file(GLOB_RECURSE json_files "python/*.json")
rez_install_files(
    ${json_files}
    DESTINATION .
)

file(GLOB_RECURSE mel_files "python/*.mel")
rez_install_files(
    ${mel_files}
    DESTINATION .
)

file(GLOB_RECURSE png_files "python/*.png")
rez_install_files(
    ${png_files}
    DESTINATION .
)
