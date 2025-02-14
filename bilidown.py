# coding:utf-8
import os
import sys

import yt_dlp
import requests
import re
from json import JSONDecodeError

api_biliplus_view = 'https://www.biliplus.com/api/view'
api_bilibili_view = 'https://api.bilibili.com/x/web-interface/view'

api_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/"
}
    
video_base_url = 'https://www.bilibili.com/video/av'
video_keys = ['av', 'AV', 'BV', 'bv']

def get_video_url(aid, p):
    return f"{video_base_url}{aid}?p={p}"

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


class PageInfo:
    def __init__(self, aid, p: int, title: str, dmlink: str):
        self.title = title
        self.dmlink = dmlink
        self.aid = aid
        self.videoUrl = get_video_url(aid, p)


def validate_filename(name):
    r_str = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_name = re.sub(r_str, " ", name)  # 替换为下划线
    return new_name


def get_av_info(aid, update=0, biliplus=True):
    if biliplus == True:
        url = f"{api_biliplus_view}?id={aid}&update={update}"
    else:
        url = f"{api_bilibili_view}?aid={aid}"

    json = {}
    error = False
    try:
        response = requests.get(url=url, headers=api_headers)
        response.raise_for_status()
        json = response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: ({response.status_code}): {http_err}")
        error = True
    except requests.exceptions.RequestException as req_err:
        print(f"Request Error: {req_err}")
        error = True
    except JSONDecodeError as e:
        print(f"JSON Error: {e}")
        print("Response Content:", response.text[:200])
        error = True
    except Exception as unexpected_err:  # 捕获其他所有异常
        print(f"Error: {unexpected_err.__class__.__name__} - {unexpected_err}")
        error = True

    if biliplus == True and (error or ('code' in json and json['code'] == -404)):
        return get_av_info(aid=aid, update=update, biliplus=False)

    if biliplus == True:
        if 'v2_app_api' in json:
            json = json['v2_app_api']
    else:
        json = json['data']

    title = validate_filename(json['title'])
    pages = None
    videos = 1

    if 'pages' in json:
        pages = json['pages']
    if 'videos' in json:
        videos = json['videos']
    return {'title': title, 'pages': pages, 'videos': videos}


def getPageInfo(aid, name_prefix='', p=1, update=0, damu=False) -> PageInfo:
    info = get_av_info(aid=aid, update=update, biliplus=damu)
    if info['pages'] is None:
        info = get_av_info(aid=aid, update=1, biliplus=damu)

    title = validate_filename(info['title'])
    pages = info['pages']

    dmlink = None
    part_name = None

    for page in pages:
        if page['page'] == p:
            if 'dmlink' in page:
                dmlink = page['dmlink']
            part_name = page['part']
            break

    if damu == True and dmlink is None and update == 0:
        return getPageInfo(aid=aid, name_prefix=name_prefix, p=p, update=1)
    if name_prefix and len(name_prefix):
        title = name_prefix + ' ' + title
    if len(pages) > 1:
        width = max(2, len(str(info['videos'])))
        title = f"{title} [P{p:0{width}d}][{part_name}]"
    return PageInfo(aid, p, title, dmlink)


def do_get_danmu_video(av_numbers, cookie_path, damu=False, video=False, output_path=None, name_prefix='', p=1):
    for aid in av_numbers:
        print(f"--------------------------------")
        info = getPageInfo(aid=aid, name_prefix=name_prefix, p=p, update=1, damu=damu)
        if damu:
            if info.dmlink is not None:
                print(f"Downloading danmuku xml av{aid}")
                req = requests.get(url=info.dmlink, headers=api_headers)
                try:
                    file_path = os.path.join(output_path, info.title + '.xml')
                    with open(file_path, "wb") as f:
                        f.write(req.content)
                    print(f"finished xml av{aid}")
                except Exception as e:
                    print(f"{e}\n")
            else:
                print(f"Error: dmlink not find for av{aid}")

        if video:
            video_path = os.path.join(output_path, info.title)
            downer = ytdlp(info.videoUrl, video_path, cookie_path)
            downer.download()
        print(f"--------------------------------")


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
        print(f"Download error: {e}\n")


if __name__ == '__main__':
    av = []
    output = None
    prefix = ''
    p = 1
    video = True
    damu = True
    cookie_path = None
    
    length = len(sys.argv)
    
    for i in range(1, length):
        key = sys.argv[i].strip()
        value = None

        if i+1 < length:
            value = sys.argv[i+1].strip()
        
        if key == '-o' or key == '-output':
            output = value
        elif key == '-p' or key == '-prefix':
            prefix = value
        elif key == '-v' or key == '-video':
            video = (int(value) > 0) if value.isdigit() else False
        elif key == '-d' or key == '-danmaku':
            damu = (int(value) > 0) if value.isdigit() else False
        elif key == '-c' or key == '-cookie':
            cookie_path = value
        elif len(key) > 3:
            if key.startswith('https://www.bilibili.com/video'):
                for item in key.split('/'):
                    flag = False
                    for key in video_keys:
                        if item.startswith(key):
                            key = item
                            flag = True
                            break
                    if flag:
                        break

            index = key.find('?')
            if index != -1:
                for find_p in key[index + 1:].split('&'):
                    if find_p.startswith('p='):
                        p = int(find_p[2:])
                key = key[:index]

            if key.startswith('BV') or key.startswith('bv'):
                key = 'av{}'.format(BilibiliCodec.bv2av(key))
            if key.startswith('AV') or key.startswith('av'):
                av_number = ''.join(filter(lambda x: x.isdigit(), key))
                av.append(av_number)
    get_danmu_video(av_numbers=av, cookie_path=cookie_path, damu=damu, video=video, output_path=output, name_prefix=prefix, p=p)
