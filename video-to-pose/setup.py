from setuptools import setup, find_packages

setup(
    name="video-to-pose",
    version="0.1.0",
    description="从视频中提取pose数据",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "opencv-python",
        "decord",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "video-to-pose=video_to_pose.cli:main",
        ],
    },
)

