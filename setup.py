from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="quanterraRsProject",
    version="1.0.0",
    author='Roberto Toapanta',
    author_email='robertocarlos.toapanta@gmail.com',
    description="Project for monitoring the health status of Quanterra devices",
    long_description="Retrieves station code, serial number, input voltage, system temperature, sat. used, "
                     "media.site1.space.occupied, media.site2.space.occupied, q330 serial, main current, and clock "
                     "quality values from the devices for comprehensive monitoring.",
    long_description_content_type="text/markdown",
    url="https://github.com/rotoapanta/quanterraProject.git",
    packages=find_packages(),
    install_requires=[
        "py-zabbix==1.1.7",  # List your dependencies here
        "requests~=2.31.0",
        "urllib3 == 2.0.4"
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)