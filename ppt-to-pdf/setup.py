from setuptools import setup, find_packages

setup(
    name="ppt-to-pdf",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-pptx",
    ],
    entry_points={
        "console_scripts": [
            "ppt-to-pdf=ppt_to_pdf.__main__:main",
        ],
    },
)

