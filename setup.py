#!/usr/bin/env python3

import os
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tarfile

from setuptools import setup
from setuptools.command.build_ext import build_ext
from os import environ
from setuptools.command.install import install as _install
from urllib.request import urlretrieve


PGVERSION = environ.get('PGVERSION', '17.4')
PGVERSION_UNDERSCORE = PGVERSION.replace('.', '_')


def _path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))


def _dep_source_path(relative_path):
    return os.path.join(_path_in_dir("deps"), relative_path)


def _dep_build_path(relative_path):
    return os.path.join(_path_in_dir("_deps/build"), relative_path)


def _read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


postgres_tarball_path = _dep_source_path(f"REL_{PGVERSION_UNDERSCORE}.tar.gz")
postgres_src_dir = _dep_build_path(f"postgres-REL_{PGVERSION_UNDERSCORE}")
postgres_install_prefix = os.path.abspath(os.path.join(sys.executable, "..", ".."))


class BuildPostgres(build_ext):
    def finalize_options(self):
        build_ext.finalize_options(self)
        if os.name == "nt":
            self.compiler = "mingw32"

    def run(self):
        if not os.path.exists(_dep_build_path(".")):
            os.makedirs(_dep_build_path("."))
        self._build_postgres()
        # No extensions to build, but keep the base behavior
        build_ext.run(self)

    def _build_postgres(self):
        # Download tarball if missing
        if not os.path.exists(postgres_tarball_path):
            os.makedirs("deps", exist_ok=True)
            url = f"https://github.com/postgres/postgres/archive/refs/tags/REL_{PGVERSION_UNDERSCORE}.tar.gz"
            print(f"Downloading PostgreSQL from {url} ...")
            urlretrieve(url, postgres_tarball_path)

        self._build_lib(
            tarball_path=postgres_tarball_path,
            lib_dir=postgres_src_dir,
            commands=[
                ["./configure",
                 f"--prefix={postgres_install_prefix}",
                 *environ.get("PGCONFIGUREFLAGS", "").split(),
                 ],
                ["make", "-j"],
                ["make", "install"],
            ]
        )

    def _build_lib(self, tarball_path, lib_dir, commands):
        self._extract_tarball(tarball_path, lib_dir)

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = str(macosx_deployment_target)

        def run_command(args):
            print("Executing: %s" % ' '.join(args))
            if os.name == "nt":
                command = ["msys2.cmd", "-c", " ".join(shlex.quote(arg) for arg in args)]
            else:
                command = args

            subprocess.run(command, cwd=lib_dir, check=True, stdout=sys.stdout, stderr=sys.stderr)

        for command in commands:
            run_command(command)

    def _extract_tarball(self, tarball_path, lib_dir):
        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(_dep_build_path("."))


from setuptools.command.install import install as _install


class PostInstallBuildPostgres(_install):
    def run(self):
        self.run_command("build_ext")
        super().run()


setup(
    name='pgvenv',
    version="0.1.1",
    description='pip install pgvenv',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author='Florents Tselai',
    author_email="florents.tselai@gmail.com",
    url='https://github.com/Florents-Tselai/pgvenv',
    python_requires='>=3.7',
    license=open("LICENSE").read(),
    ext_modules=[],
    cmdclass={"build_ext": BuildPostgres,
              "install": PostInstallBuildPostgres},
)
