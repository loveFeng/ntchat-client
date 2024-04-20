#!/usr/bin/env bash


install_py(){
wine pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
wine pip install -r requirements.txt
}

#!/usr/bin/env bash
## https://gitlab.com/cunidev/gestures/-/wikis/xdotool-list-of-key-codes
function install() {
    echo "install sleep 60"
    sleep 60
    while :
    do
        xdotool search '微信安装向导' && NOTFOUND=$? && echo $NOTFOUND
        if [ "$NOTFOUND" == "0" ]; then
            echo "xdotool choice"
            xdotool mousemove --screen 0 561 462 && xdotool click 1 
            sleep 1
            xdotool mousemove --screen 0 645 419 && xdotool click 1 
            echo "xdotool install"
            xdotool key Return
            sleep 16
            xdotool mousemove --screen 0 669 416 && xdotool click 1 
            break
        fi
        sleep 5
    done

}

echo "wine WeChatSetup.exe"
wine WeChatSetup.exe &

install &

install_py

wait
