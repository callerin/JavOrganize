# JavOrganize

- ## 根据Emby刮削数据整理Video文件

- ## 目前支持Javscraper、JavTube刮削数据（EMBY设置勾选“将媒体图像保存到媒体文件夹中”）

> ### 使用方法
>
> 使用命令行直接运行脚本文件，命令格式 python ./organize_v.py -o src_dir -d dest_dir
>
> <u>说明：organize_v.py使用绝对路径或者加入path, src_dir dest_dir 为可选参数，分别为待处理文件夹路径，移动文件目录，无输入参数时默认为终端当前路径</u>

> ```python
>
> python organize_v.py -o src_dir -d dest_dir
>
> ```
>

> ### 效果
> 将目标目录的Jav视频文件整理到其他目录，根据演员名称建立文件夹存放；源文件名称修改为 “番号+标题+演员名”的形式，支持字幕文件移动(文件名需要有番号关键字)。
>
> 例子：hhd800.com@HMN-189.mp4 --> HMN-189 ぼっち×おじ散歩 アプリで出会ったクラスでぼっちの子の誘惑に負けた中年オヤジは ラブホテルで何度も、何度も、中出しセックスしてしまった… 由良かな.mp4
>
> 参考 Javscraper JavOrganize，由于改用javtube刮削影片后，JavOrganize对其刮削结果无作用，所以有了这个东西。



> **tips:**
>
> 多文件影片命名需包含 ‘-CD’关键字，例如 ‘STARS-685-cd1.mp4 STARS-685-cd2.mp4’，识别成功后创建番号文件夹单独存放多文件影片

> -l 1 选项不移动就，创建hardlink，避免干扰PT做种
>
> -m 1 选项将缺少图片文件的部分视频单独存放，慎用

***下载症患者、懒癌必备。[搭配MoveFile食用更佳](https://github.com/callerin/FileRename/blob/main/MoveFile.py)***

