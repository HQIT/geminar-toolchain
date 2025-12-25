# RVM API - 非侵入式 RobustVideoMatting wrapper

ARG BASE_IMAGE=nvidia/cuda:11.7-runtime-ubuntu22.04
FROM ${BASE_IMAGE}

WORKDIR /app

# 安装依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 克隆 RobustVideoMatting（不修改源码）
RUN git clone https://github.com/PeterL1n/RobustVideoMatting.git /app/RobustVideoMatting

# 安装 RVM 依赖
WORKDIR /app/RobustVideoMatting
RUN pip3 install --no-cache-dir -r requirements_inference.txt

# 安装 API 依赖
WORKDIR /app/api
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制 API 代码
COPY rvm_api/ ./rvm_api/

# 创建输出目录
RUN mkdir -p /app/outputs

# 环境变量
ENV RVM_PATH=/app/RobustVideoMatting
ENV OUTPUT_DIR=/app/outputs
ENV MODEL_TYPE=mobilenetv3
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "rvm_api.app:app", "--host", "0.0.0.0", "--port", "8000"]

