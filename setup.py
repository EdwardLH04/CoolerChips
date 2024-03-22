from pathlib import Path
from setuptools import setup

from MOSTcool import VERSION, NAME
readme_file = Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()


# Function to read the contents of the requirements file
def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


setup(
    name=NAME,
    version=VERSION,
    packages=[NAME],
    description="A Most Cool Tool",
    package_data={},
    include_package_data=True,  # use /MANIFEST.in file for declaring package data
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author='MOSTcool Team',
    url='https://github.com/jmythms/Mostcool_GUI',
    license='NoneForNow',
    install_requires=read_requirements(),
    entry_points={
        'gui_scripts': ['mostcool_gui=MOSTcool.main:main_gui'],
        'console_scripts': []},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Utilities',
    ],
    platforms=[
        'Linux (Tested on Ubuntu)',
        #'MacOSX', 'Windows'  # TODO: Update
    ],
    keywords=[
        'Simulation',
    ]
)
