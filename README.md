# download_video_gui

#### 介绍
爬取视频python工具

pyrcc5 res.qrc -o res_rc.py
#### 依赖管理
    1.  导出依赖 pip freeze > requirements.txt
        报错解决：https://blog.csdn.net/weixin_44546342/article/details/105229575
    2.  安装依赖 pip install -r requirements.txt

#### 发布说明
    1.  在项目主目录运行 pip install pyinstaller 安装打包工具
    2.1.  打包单文件:在项目主目录运行 pyinstaller -Fw -i favicon.ico main.py
    2.2.  打包程序: pyinstaller -FwD -i favicon.ico main.py
    3.  main.exe 即可执行文件

#### 后续功能
|序号|功能点|进度|
|:----:|:----:|:----:|
|1|进度条展示|未开始|
|2|全局异常控制|未开始|
|3|单个下载任务重试|未开始|
