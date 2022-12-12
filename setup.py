import setuptools
from distutils.command.build import build
from setuptools.dist import Distribution
from subprocess import call
import os
import shutil
import logging

logger = logging.getLogger(__name__)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

class SliQSimBuild(build):
    def run(self):
        super().run()
        curdir = os.getcwd()
        os.chdir("SliQSim/cudd")
        logger.info('[*]  Running configure for cudd package...')
        call(["./configure", "--enable-dddmp", "--enable-obj", "--enable-shared", "--enable-static"])
        os.chdir(curdir)
        os.chdir("SliQSim")
        logger.info('[*]  Running make for SliQSim and cudd...')
        call(["make","-j"])
        os.chdir(curdir)
        shutil.move("SliQSim/SliQSim", "build/lib/qiskit_sliqsim_provider/SliQSim")
# This is for creating wheel specific platforms
class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


setuptools.setup(
    name="qiskit-sliqsim-provider", # Replace with your own username
    version="0.0.7",
    author="Yuan-Hung Tsai, Jie-Hong R. Jiang, Chiao-Shan Jhang, Justin Chen",
    author_email="matthewyhtsai@gmail.com",
    description="SliQSim simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NTU-ALComLab/SliQSim-Qiskit-Interface",
    include_package_data=True,
    packages=setuptools.find_packages(exclude=['sample*','test*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    cmdclass={'build': SliQSimBuild},
    distclass=BinaryDistribution,
    python_requires='>=3.8'
)
