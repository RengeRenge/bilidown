# coding:utf-8
import os
import sys

import youtube_dl
import requests
import re
import shutil

video_base_url = 'https://www.bilibili.com/video/av'
video_keys = ['av', 'AV', 'BV', 'bv']

# @refer https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/bvid_desc.md

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

def av2bv(aid: int) -> str:
    bvid = [""] * 9
    tmp = (MAX_AID | aid) ^ XOR_CODE
    for i in range(CODE_LEN):
        bvid[ENCODE_MAP[i]] = ALPHABET[tmp % BASE]
        tmp //= BASE
    return PREFIX + "".join(bvid)

def bv2av(bvid: str) -> int:
    assert bvid[:3] == PREFIX

    bvid = bvid[3:]
    tmp = 0
    for i in range(CODE_LEN):
        idx = ALPHABET.index(bvid[DECODE_MAP[i]])
        tmp = tmp * BASE + idx
    return (tmp & MASK_CODE) ^ XOR_CODE


class YoutubeDowner(object):
    def __init__(self, name):
        self.name = name

    # def rename_hook(self, d):
    # 重命名下载的视频名称的钩子
    # if d['status'] == 'finished':
    #     os.rename(d['filename'], self.name)
    #     print('下载完成{}'.format(self.name))

    def download(self, youtube_url):
        # 定义某些下载参数
        ydl_opts = {
            # 'progress_hooks': [self.rename_hook],
            # 格式化下载后的文件名，避免默认文件名太长无法保存
            # 'outtmpl': '%(id)s%(ext)s',
            'outtmpl': self.name,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # 下载给定的URL列表
            result = ydl.download([youtube_url])


def validate_filename(name):
    r_str = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_name = re.sub(r_str, " ", name)  # 替换为下划线
    return new_name


def get_danmu_video(av_numbers, video=False, output_path=None, name_prefix='', p=1):
    if output_path is None:
        base_path = os.getcwd()
    else:
        base_path = output_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)
    try:
        do_get_danmu_video(av_numbers=av_numbers, video=video, output_path=base_path, name_prefix=name_prefix, p=p)
    except Exception as e:
        print(e)


def do_get_danmu_video(av_numbers, video=False, output_path=None, name_prefix='', p=1):
    for av_number in av_numbers:
        print("\n----------------\ndownloading xml av" + av_number)
        info = get_av_info(aid=av_number, update=0)
        if info['pages'] is None:
            info = get_av_info(aid=av_number, update=1)

        title = validate_filename(info['title'])
        pages = info['pages']

        dmlink = None
        part_name = None

        for page in pages:
            if page['page'] == p:
                dmlink = page['dmlink']
                part_name = page['part']
                break

        if name_prefix and len(name_prefix):
            title = name_prefix + ' ' + title

        if dmlink is not None:
            if len(pages) > 1:
                title = title + (' [P%s][%s]' % (p, part_name))

            req = requests.get(url=dmlink)
            try:
                file_path = os.path.join(output_path, title + '.xml')
                with open(file_path, "wb") as f:
                    f.write(req.content)
                print("finished xml av" + av_number)
            except Exception as e:
                print(e)
        else:
            print("error: dmlink not find for av" + av_number)

        if video:
            video_url = video_base_url + av_number
            video_name = title + '.flv'
            downer = YoutubeDowner(video_name)
            downer.download(video_url)

            new_file = os.path.join(output_path, video_name)
            if output_path != os.getcwd():
                old_file = os.path.join(os.getcwd(), video_name)
                shutil.move(old_file, new_file)

            print("finished at:\n{}\n----------------\n".format(new_file))


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
    prefix.isspace()

    read_path = False
    read_prefix = False
    read_video = False

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
        elif param == '-o' or param == '-output':
            read_path = True
        elif param == '-p' or param == '-prefix':
            read_prefix = True
        elif param == '-v' or param == '-video':
            read_video = True
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
                param = 'av{}'.format(bv2av(param))
            if param.startswith('AV') or param.startswith('av'):
                av_number = ''.join(filter(lambda x: x.isdigit(), param))
                av.append(av_number)
    get_danmu_video(av_numbers=av, video=video, output_path=output, name_prefix=prefix, p=p)
