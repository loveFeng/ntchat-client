ROOT_PATH=$(cd "$(dirname "$0")"; pwd)

start_wx(){
    wine 'C:\Program Files (x86)\Tencent\WeChat\WeChat.exe' &
    sleep 10 
    xdotool mousemove --screen 0 645 447 && xdotool click 1 &
}

pushd $ROOT_PATH
while true; do

# 检测 WeChat.exe 进程是否存在
if ! pgrep -x "WeChat.exe" > /dev/null; then
    echo "WeChat.exe 进程未运行，日志记录..."
    start_wx &
fi

# 检测 python.exe 进程是否存在
if ! pgrep -x "python.exe" > /dev/null; then
    echo "python.exe 进程未运行，日志记录..."
    wine main.py &
fi

sleep 10

done
popd
