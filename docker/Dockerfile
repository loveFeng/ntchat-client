FROM chisbread/wine-box:latest

WORKDIR /home/app/

#ADD WeChat-3.6.0.18Setup.exe WeChatSetup.exe

ADD https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.6.0.18/WeChatSetup-3.6.0.18.exe WeChatSetup.exe

COPY install-wechat.sh install-wechat.sh

COPY ntchat-client/requirements.txt requirements.txt

RUN sudo chown app:app requirements.txt WeChatSetup.exe  install-wechat.sh

RUN bash -c 'nohup /entrypoint.sh 2>&1 &' &&  sleep 10 && bash install-wechat.sh

RUN bash -c 'rm WeChatSetup.exe install-wechat.sh'

USER app

COPY cmd.sh /cmd.sh
