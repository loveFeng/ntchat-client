# docker build -t joe-ntchat-wx -f ./Dockerfile .

# docker run --name=wechat -p 8080:8080 joe-ntchat-wx

# docker export wechat > wechat.tar

# docker import wechat.tar joe-ntchat-wx

docker run -d --name=wechat -w /home/app/ --user app -e DISPLAY=:0.0 -e DISPLAY_WIDTH=1280 -e DISPLAY_HEIGHT=720 -e LANG=zh_CN.UTF-8 -e LANGUAGE=zh_CN.UTF-8 -e LC_ALL=zh_CN.UTF-8 -e WINEPREFIX=/home/app/.wine --entrypoint="/cmd.sh" -v /work/ntchat-client:/home/app/api -v /work/wechat_data:'/home/app/WeChat Files' -p="8080:8080" -v /etc/timezone:/etc/timezone -v /etc/localtime:/etc/localtime --add-host=dldir1.qq.com:127.0.0.1 joe-ntchat-wx

