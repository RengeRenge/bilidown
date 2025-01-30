# bilidown
批量下载哔哩哔哩视频和弹幕的工具

## 安装依赖

- 需要有 python 环境
- 如果没有安装 pip，自行搜索各个平台的安装方法

### 安装 yt-dlp

脚本依赖 yt-dlp 下载视频

```bash
pip install yt-dlp
```

### 安装 ffmpeg

yt-dlp 依赖 ffmpeg 将下载的视频和音频合并在一起

#### Linux/Ubuntu
```bash
sudo apt install ffmpeg
``` 
#### Windows

[ffmpeg.exe 可执行文件下载地址](https://ffmpeg.org/download.html#build-windows)

将 ffmpeg.exe 添加进系统的环境变量 path 里

## 参数

- -prefix (-p) 下载的视频名字添加前缀
- -output (-o) 指定下载的路径，如果不指定，则下载到当前 cd 的目录
- -video (-v) 是否下载视频，传递参数1或者0，默认是1。
- -danmuku (-d) 是否下载弹幕，传递参数1或者0，默认是1。
- -cookie (-c) 指定浏览器 cookie 的路径，有 cookie 能下载当前登录账号可观看的最高质量的视频

### cookie 获取

- 浏览器添加扩展插件 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- 打开 [bilibili](https://www.bilibili.com/) 确保已登录账号
- 点击扩展-插件-Export，下载当前的 cookie


## 用例

#### 用例1

- 单个视频下载
- 下载完成后添加前缀 20200704
- 保存到路径 ~/desktop/video
- 指定 cookie 的路径 ~/download/cookies.txt

```bash
python3 bilidown.py av1830060 -p 20200704 -o ~/desktop/video -c ~/download/cookies.txt
```

#### 用例2

- 多个视频下载 `av号` `网页地址` `bv号`
  - av170001
  - https://www.bilibili.com/video/BV1Es411j7AE
  - BV15x411N7tu

- 其他参数对所有视频生效

```bash
python3 bilidown.py av170001 https://www.bilibili.com/video/BV1Es411j7AE BV15x411N7tu -p 20200704 -o ~/desktop/video
```

## 更方便的用法

#### 将 bilidown 定义为终端自定义命令

mac 去修改 `~/.bash_profile`

Linux/Ubuntu 去修改 `~/.bashrc`

以下是我的自定义 shell 内容，提供参考，可将其添加在文件末尾

`./bilidown.py `需要替换为脚本的路径

```bash
function download_video_danmu() {
		sudo python3 ./bilidown.py -c ~/download/cookies.txt $*
	}

function download_video_danmu_to_default() {
		sudo python3 ./bilidown.py -o '/Users/renge/Desktop/bilidown/' -c ~/download/cookies.txt $*
	}

alias bilidown='download_video_danmu'

alias bilidown_default="download_video_danmu_to_default"

```

修改完成后执行 ```source .bashxxx``` 使其立刻生效 .bashxxx 为刚刚修改的文件

现在我们可以使用自定义的命令 bilidown 下载视频了

```bash
cd ~/bilidown
bilidown av1830060 -p 安达可爱
```

下载视频到默认的目录

```bash
bilidown_default av1830060 -p 岛村可爱
```

#### 结果展示

```bash
Renge@RengedeMacBook-Pro ~ %  bilidown_default av1830060 -p 岛村可爱
--------------------------------
downloading danmuku xml av1830060
finished xml av1830060
[BiliBili] Extracting URL: https://www.bilibili.com/video/av1830060
[BiliBili] 1830060: Downloading webpage
[BiliBili] BV15x411N7tu: Extracting videos in anthology
[BiliBili] BV15x411N7tu: Downloading wbi sign
[BiliBili] BV15x411N7tu: Downloading video formats for cid 2814198
[BiliBili] 1830060: Extracting chapters
[info] BV15x411N7tu: Downloading 1 format(s): 100111+30280
[info] Downloading video thumbnail 0 ...
[info] Writing video thumbnail 0 to: /Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.jpg
[download] Destination: /Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.f100111.mp4
[download] 100% of    3.85MiB in 00:00:00 at 8.97MiB/s
[download] Destination: /Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.f30280.m4a
[download] 100% of    1.44MiB in 00:00:00 at 3.34MiB/s
[Merger] Merging formats into "/Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.mp4"
Deleting original file /Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.f100111.mp4 (pass -k to keep)
Deleting original file /Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.f30280.m4a (pass -k to keep)
[EmbedThumbnail] Neither mutagen nor AtomicParsley was found. Falling back to ffmpeg
[EmbedThumbnail] ffmpeg: Adding thumbnail to "/Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.mp4"
[Metadata] Adding metadata to "/Users/renge/Desktop/bilidown/岛村可爱 【静止系MAD】Waiting for The Moon.mp4"
--------------------------------
Renge@RengedeMacBook-Pro ~ % 
```

#### Windows 的一些建议

- Windows 需要编写 .bat 脚本，然后去 `我的电脑-右击-属性-高级系统设置-环境变量-系统变量-Path-编辑-新建-粘贴目录 `添加环境变量

- Win10 用户可以去安装 Ubuntu 子系统，然后将下载路径指定为 `/mnt/d/bilidown`其中mnt 为 window 的根目录，d当然就是d盘
