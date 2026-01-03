FROM docker.1ms.run/python:3.10-slim

# 使用国内 apt 镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制工具模块
COPY ppt-to-pdf/setup.py ppt-to-pdf/
COPY ppt-to-pdf/ppt_to_pdf ppt-to-pdf/ppt_to_pdf
COPY ppt-to-images/setup.py ppt-to-images/
COPY ppt-to-images/ppt_to_images ppt-to-images/ppt_to_images
COPY text-to-speech/setup.py text-to-speech/
COPY text-to-speech/requirements.txt text-to-speech/
COPY text-to-speech/text_to_speech text-to-speech/text_to_speech
COPY page-to-video/setup.py page-to-video/
COPY page-to-video/page_to_video page-to-video/page_to_video
COPY portrait-to-talking/setup.py portrait-to-talking/
COPY portrait-to-talking/portrait_to_talking portrait-to-talking/portrait_to_talking
COPY clip-add-talking/setup.py clip-add-talking/
COPY clip-add-talking/clip_add_talking clip-add-talking/clip_add_talking

# 安装 Python 依赖（使用国内镜像）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    python-pptx \
    pdf2image \
    Pillow \
    edge-tts \
    requests \
    python-dotenv \
    moviepy

# 安装各工具
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e ppt-to-pdf/ \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e ppt-to-images/ \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e text-to-speech/ \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e page-to-video/ \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e portrait-to-talking/ \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e clip-add-talking/

# 创建共享目录
RUN mkdir -p /app/shared/inputs /app/shared/outputs

# 默认进入 bash
CMD ["/bin/bash"]
