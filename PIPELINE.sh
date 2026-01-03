#!/bin/bash
# 从 PPTX 到讲课视频的完整管线（调用容器内工具）
# 用法: ./PIPELINE.sh input.pptx portrait.jpg output.mp4

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="geminar-toolchain"

INPUT_PPTX="$1"
PORTRAIT="$2"
OUTPUT="$3"
WORKDIR="$SCRIPT_DIR/.pipeline_output"

if [ -z "$INPUT_PPTX" ] || [ -z "$PORTRAIT" ] || [ -z "$OUTPUT" ]; then
    echo "用法: $0 <input.pptx> <portrait.jpg> <output.mp4>"
    exit 1
fi

# 转为绝对路径
INPUT_PPTX="$(cd "$(dirname "$INPUT_PPTX")" && pwd)/$(basename "$INPUT_PPTX")"
PORTRAIT="$(cd "$(dirname "$PORTRAIT")" && pwd)/$(basename "$PORTRAIT")"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT")" && pwd)"
OUTPUT_NAME="$(basename "$OUTPUT")"

mkdir -p "$WORKDIR"

# Docker run 封装函数
run_tool() {
    docker run --rm \
        -v "$WORKDIR:/work" \
        -v "$(dirname "$INPUT_PPTX"):/input:ro" \
        -v "$(dirname "$PORTRAIT"):/portrait:ro" \
        -v "$OUTPUT_DIR:/output" \
        -e ECHOMIMIC_URL="${ECHOMIMIC_URL:-http://host.docker.internal:8000/a2v}" \
        "$IMAGE_NAME" \
        "$@"
}

echo "=== 1. PPT 转 PDF + 提取备注 ==="
run_tool python -m ppt_to_pdf "/input/$(basename "$INPUT_PPTX")" -o /work -v

echo "=== 2. PDF 转图片 ==="
PDF_NAME="$(basename "${INPUT_PPTX%.*}").pdf"
run_tool python -m ppt_to_images "/work/$PDF_NAME" -o /work/slides -v

# 获取页数
PAGE_COUNT=$(ls "$WORKDIR/slides"/*.png 2>/dev/null | wc -l)
echo "共 $PAGE_COUNT 页"

echo "=== 3. 逐页生成音频、课件视频、数字人视频 ==="
for i in $(seq 1 $PAGE_COUNT); do
    echo "--- 处理第 $i 页 ---"
    
    # 备注转语音
    if [ -f "$WORKDIR/$i.txt" ] && [ -s "$WORKDIR/$i.txt" ]; then
        run_tool python -m text_to_speech -i "/work/$i.txt" -o "/work/audio_$i.mp3"
    else
        echo "跳过第 $i 页（无备注）"
        continue
    fi
    
    # 图片+音频 → 课件视频
    run_tool python -m page_to_video "/work/slides/$i.png" "/work/audio_$i.mp3" -o "/work/slide_$i.mp4"
    
    # 肖像+音频 → 数字人视频
    run_tool python -m portrait_to_talking "/portrait/$(basename "$PORTRAIT")" -a "/work/audio_$i.mp3" -o "/work/talking_$i.mp4"
done

echo "=== 4. 合成画中画视频 ==="
for i in $(seq 1 $PAGE_COUNT); do
    if [ -f "$WORKDIR/slide_$i.mp4" ] && [ -f "$WORKDIR/talking_$i.mp4" ]; then
        run_tool python -m clip_add_talking "/work/slide_$i.mp4" "/work/talking_$i.mp4" -o "/work/combined_$i.mp4"
    fi
done

echo "=== 5. 拼接所有片段 ==="
ls "$WORKDIR"/combined_*.mp4 | sort -V | xargs -I {} basename {} | sed "s/^/file '\/work\//" | sed "s/$/'/" > "$WORKDIR/concat.txt"
run_tool ffmpeg -y -f concat -safe 0 -i /work/concat.txt -c copy "/output/$OUTPUT_NAME"

echo "=== 完成: $OUTPUT ==="
