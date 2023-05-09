from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='aptos-brownie',
    version='3.0.6',
    description='Aptos Package Tool',
    long_description="This is an aptos python tool to quickly implement aptos calls",
    # The project's main homepage.
    url='https://github.com/OmniBTC/OmniSwap/blob/main/utils',
    # Author details
    author='DaiWei',
    author_email='dw1253464613@gmail.com',
    # Choose your license
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: System :: Logging',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires=">=3.6",
    py_modules=["aptos_brownie"],
    install_requires=['aptos_sdk', "pyyaml", "toml"]
)
