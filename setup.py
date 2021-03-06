import os
from setuptools import setup
from elshelves.version import __version__

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "elshelves",
    version = __version__,
    author = "Martin Sivak",
    author_email = "mars@montik.net",
    description = ("Electronic warehouse tracking app."),
    license = "GPLv2+",
    keywords = "electronics parts database tracking project",
    url = "http://github.com/MarSik/elshelves",
    packages=['elshelves'],
    package_data={
        "": ["*.sql"]
    },
    long_description=read('README'),
    classifiers=[
        "Environment :: Console :: Curses",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities"
    ],
)
