# EchoMimic API - 非侵入式 wrapper
# 基于 CUDA 基础镜像，使用 EchoMimic V2

ARG BASE_IMAGE=nvidia/cuda:12.1-runtime-ubuntu22.04
FROM ${BASE_IMAGE}

WORKDIR /app

# 安装 Python 和基础依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制本地 echomimic_v2（不从远程克隆）
COPY echomimic_v2/ /app/echomimic_v2/

# 配置 pip 国内镜像
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 echomimic_v2 依赖
WORKDIR /app/echomimic_v2
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装 API wrapper 依赖
WORKDIR /app/api
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制 API 代码
COPY echomimic_api/ ./echomimic_api/

# 创建输出目录
RUN mkdir -p /app/outputs

# 环境变量
ENV ECHOMIMIC_PATH=/app/echomimic_v2
ENV PRETRAINED_WEIGHTS=/app/echomimic_v2/pretrained_weights
ENV OUTPUT_DIR=/app/outputs
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

EXPOSE 8000

# 启动服务
CMD ["python3", "-m", "uvicorn", "echomimic_api.app:app", "--host", "0.0.0.0", "--port", "8000"]

