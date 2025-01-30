# coding:utf-8
import os
import sys

import yt_dlp
import requests
import re
import shutil

video_base_url = 'https://www.bilibili.com/video/av'
video_keys = ['av', 'AV', 'BV', 'bv']

# @refer https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/bvid_desc.md
class BilibiliCodec:
    XOR_CODE = 23442827791579
    MASK_CODE = 2251799813685247
    MAX_AID = 1 << 51
    ALPHABET = "FcwAPNKTMug3GV5Lj7EJnHpWsx4tb8haYeviqBz6rkCy12mUSDQX9RdoZf"
    ENCODE_MAP = 8, 7, 0, 5, 1, 3, 2, 4, 6
    DECODE_MAP = tuple(reversed(ENCODE_MAP))

    BASE = len(ALPHABET)
    PREFIX = "BV1"
    PREFIX_LEN = len(PREFIX)
    CODE_LEN = len(ENCODE_MAP)
    
    @classmethod
    def av2bv(cls, aid: int) -> str:
        bvid = [""] * 9
        tmp = (cls.MAX_AID | aid) ^ cls.XOR_CODE
        for i in range(cls.CODE_LEN):
            bvid[cls.ENCODE_MAP[i]] = cls.ALPHABET[tmp % cls.BASE]
            tmp //= cls.BASE
        return cls.PREFIX + "".join(bvid)
    
    @classmethod
    def bv2av(cls, bvid: str) -> int:
        assert bvid[:3] == cls.PREFIX

        bvid = bvid[3:]
        tmp = 0
        for i in range(cls.CODE_LEN):
            idx = cls.ALPHABET.index(bvid[cls.DECODE_MAP[i]])
            tmp = tmp * cls.BASE + idx
        return (tmp & cls.MASK_CODE) ^ cls.XOR_CODE


class ytdlp:
    def __init__(self, url: str, path: str, cookiePath: str):
        self.urls = [url]
        self.ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # 最佳质量
            'outtmpl': f'{path}.%(ext)s',
            "merge_output_format": "mp4",  # 合并格式（需ffmpeg）
            'keepvideo': False,  # 合并后保留原始文件
            # "progress_hooks": [self.my_hook],  # 进度回调（需自定义函数）
            "noplaylist": True,  # 启用播放列表下载
            "writethumbnail": True,
            'postprocessors': [
                {'key': 'EmbedThumbnail'},  # 嵌入封面到视频文件
                {'key': 'FFmpegMetadata'},  # 添加元数据
            ],
        }
        if cookiePath is not None:
            self.ydl_opts['cookiefile'] = cookiePath


    # def my_hook(self, d):
    #     if d['status'] == 'downloading':
    #         print(f"downloading: {d['_percent_str']}\n")


    def download(self):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download(self.urls)
        except yt_dlp.utils.DownloadError as e:
            print(f"yt-dlp download error: {e}")


class pageInfo:
    def __init__(self, title: str, dmlink: str):
        self.title = title
        self.dmlink = dmlink
        

def getPageInfo(aid, name_prefix='', page=1, update=0) -> pageInfo:
    info = get_av_info(aid=aid, update=update)
    if info['pages'] is None:
        info = get_av_info(aid=aid, update=1)

    title = validate_filename(info['title'])
    pages = info['pages']

    dmlink = None
    part_name = None

    for page in pages:
        if page['page'] == p:
            dmlink = page['dmlink']
            part_name = page['part']
            break

    if dmlink is None and update == 0:
        return getPageInfo(aid=aid, name_prefix=name_prefix, page=page, update=1)
    if name_prefix and len(name_prefix):
        title = name_prefix + ' ' + title
    if len(pages) > 1:
        title = f"{title} [P{p}][{part_name}]"
    return pageInfo(title, dmlink)
    
        
def validate_filename(name):
    r_str = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_name = re.sub(r_str, " ", name)  # 替换为下划线
    return new_name


def get_danmu_video(av_numbers, cookie_path, damu=False, video=False, output_path=None, name_prefix='', p=1):
    if output_path is None:
        base_path = os.getcwd()
    else:
        base_path = output_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)
    try:
        do_get_danmu_video(av_numbers=av_numbers, cookie_path=cookie_path, damu=damu, video=video, output_path=base_path, name_prefix=name_prefix, p=p)
    except Exception as e:
        print(f"download error: {e}\n")


def do_get_danmu_video(av_numbers, cookie_path, damu=False, video=False, output_path=None, name_prefix='', p=1):
    for av_number in av_numbers:
        print(f"--------------------------------")
        info = getPageInfo(aid=av_number, name_prefix=name_prefix, page=p, update=1)
        if damu: 
            if info.dmlink is not None:
                print(f"downloading danmuku xml av{av_number}")
                req = requests.get(url=info.dmlink)
                try:
                    file_path = os.path.join(output_path, info.title + '.xml')
                    with open(file_path, "wb") as f:
                        f.write(req.content)
                    print(f"finished xml av{av_number}")
                except Exception as e:
                    print(f"{e}\n")
            else:
                print(f"error: dmlink not find for av{av_number}")

        if video:
            video_url = video_base_url + av_number
            video_path = os.path.join(output_path, info.title)
            
            downer = ytdlp(video_url, video_path, cookie_path)
            downer.download()
        print(f"--------------------------------")


def get_av_info(aid, update=0):
    api = 'https://www.biliplus.com/api/view?id={}&update={}'.format(aid, update)

    req = requests.get(url=api)
    json = req.json()

    title = validate_filename(json['title'])
    pages = None
    if 'v2_app_api' in json:
        pages = json['v2_app_api']
        if 'pages' in pages:
            pages = pages['pages']

    return {'title': title, 'pages': pages}


if __name__ == '__main__':
    av = []
    output = None
    prefix = ''
    p = 1
    video = True
    damu = True
    cookie_path = None
    prefix.isspace()

    read_path = False
    read_prefix = False
    read_video = False
    read_damu = False
    read_cookie = False

    for i in range(1, len(sys.argv)):
        param = sys.argv[i].strip()
        if read_path:
            output = param
            read_path = False
        elif read_prefix:
            prefix = param
            read_prefix = False
        elif read_video:
            video = (int(param) > 0) if param.isdigit() else False
            read_video = False
        elif read_damu:
            damu = (int(param) > 0) if param.isdigit() else False
            read_damu = False
        elif read_cookie:
            cookie_path = param
            read_cookie = False
        elif param == '-o' or param == '-output':
            read_path = True
        elif param == '-p' or param == '-prefix':
            read_prefix = True
        elif param == '-v' or param == '-video':
            read_video = True
        elif param == '-d' or param == '-danmaku':
            read_damu = True
        elif param == '-c' or param == '-cookie':
            read_cookie = True
        elif len(param) > 3:
            if param.startswith('https://www.bilibili.com/video'):
                index = param.find('?')
                if index != -1:
                    for find_p in param[index + 1:].split('&'):
                        if find_p.startswith('p='):
                            p = int(find_p[2:])
                for item in param.split('/'):
                    flag = False
                    for key in video_keys:
                        if item.startswith(key):
                            param = item
                            flag = True
                            break
                    if flag:
                        break

            if param.startswith('BV') or param.startswith('bv'):
                param = 'av{}'.format(BilibiliCodec.bv2av(param))
            if param.startswith('AV') or param.startswith('av'):
                av_number = ''.join(filter(lambda x: x.isdigit(), param))
                av.append(av_number)
    get_danmu_video(av_numbers=av, cookie_path=cookie_path, damu=damu, video=video, output_path=output, name_prefix=prefix, p=p)
