python generates.py
sleep 5

if [ -f "results.txt" ]; then
    echo "检测到 results.txt 存在，生成超时，停止执行"
    exit 1
fi

python evaluate.py