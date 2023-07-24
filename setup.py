from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in bps/__init__.py
from bps import __version__ as version

setup(
	name="bps",
	version=version,
	description="BPS",
	author="Techfinite Systems",
	author_email="it-support@techfinite.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
