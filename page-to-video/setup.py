from setuptools import setup, find_packages

setup(
    name="page-to-video",
    version="0.1.0",
    description="将图片和音频合成为视频",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "page-to-video=page_to_video.cli:main",
        ],
    },
)

