import os
from conans import ConanFile, CMake, tools


class MongoCDriverConan(ConanFile):
    name = "mongo-c-driver"
    version = "1.16.1"
    description = "A high-performance MongoDB driver for C"
    topics = ("conan", "libmongoc", "mongodb")
    url = "http://github.com/bincrafters/conan-mongo-c-driver"
    homepage = "https://github.com/mongodb/mongo-c-driver"
    license = "Apache-2.0"
    exports_sources = ["Find*.cmake", "CMakeLists.txt"]
    generators = "cmake"

    settings = "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False], "fPIC": [
        True, False], "icu": [True, False]}
    default_options = {"shared": False, "fPIC": True, "icu": False}

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = 'zlib/1.2.11'

    def configure(self):
        # Because this is pure C
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        if not tools.os_info.is_macos and not tools.os_info.is_windows:
            self.requires("openssl/1.1.1h")

        if self.options.icu:
            self.requires("icu/64.2")

    def source(self):
        tools.get("https://github.com/mongodb/mongo-c-driver/releases/download/{0}/mongo-c-driver-{0}.tar.gz".format(self.version),
                  sha256="ad479a6d3499038ec19ca80a30dfa99277644bb884e424362935b06e2d5f7988")
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        # There are several options that would autodetect optional dependencies
        # and add them by default, need to disable all of those to ensure
        # consistent abi and dependencies

        cmake.definitions["ENABLE_TESTS"] = "OFF"
        cmake.definitions["ENABLE_EXAMPLES"] = "OFF"
        cmake.definitions["ENABLE_AUTOMATIC_INIT_AND_CLEANUP"] = "OFF"
        cmake.definitions["ENABLE_BSON"] = "ON"
        cmake.definitions["ENABLE_SASL"] = "OFF"
        cmake.definitions["ENABLE_STATIC"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["ENABLE_ICU"] = "ON" if self.options.icu else "OFF"
        cmake.definitions["ENABLE_SHM_COUNTERS"] = "OFF"
        cmake.definitions["ENABLE_SNAPPY"] = "OFF"
        cmake.definitions["ENABLE_SRV"] = "OFF"
        cmake.definitions["ENABLE_ZLIB"] = "BUNDLED"
        cmake.definitions["ENABLE_ZSTD"] = "OFF"

        if tools.os_info.is_linux:
            cmake.definitions["CMAKE_SHARED_LINKER_FLAGS"] = "-ldl"
            cmake.definitions["CMAKE_EXE_LINKER_FLAGS"] = "-ldl"

        cmake.configure(build_folder=self._build_subfolder)

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING*", dst="licenses", src=self._source_subfolder)
        self.copy("Find*.cmake", ".", ".")

        # cmake installs all the files
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ['mongoc-1.0', 'bson-1.0']
        else:
            self.cpp_info.libs = ['mongoc-static-1.0', 'bson-static-1.0']

        self.cpp_info.includedirs = [os.path.join("include", "libmongoc-1.0"),
                                     os.path.join("include", "libbson-1.0")]

        # If ICU dependency is explicitly set, propagate it
        if self.options.icu and not self.options.shared:
            self.cpp_info.libs.extend(self.deps_cpp_info["icu"].libs)

        if tools.os_info.is_macos:
            self.cpp_info.frameworks.extend(['CoreFoundation', 'Security'])

        if tools.os_info.is_linux:
            self.cpp_info.system_libs.extend(["rt", "pthread", "dl"])

        if not self.options.shared:
            self.cpp_info.defines.extend(['BSON_STATIC=1', 'MONGOC_STATIC=1'])

            if tools.os_info.is_linux or tools.os_info.is_macos:
                self.cpp_info.system_libs.append('resolv')

            if tools.os_info.is_windows:
                self.cpp_info.system_libs.extend(['ws2_32.lib', 'secur32.lib', 'crypt32.lib', 'BCrypt.lib', 'Dnsapi.lib'])
