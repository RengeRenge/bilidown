# coding:utf-8
import os
import sys

import youtube_dl
import requests
import re
import shutil

video_base_url = 'https://www.bilibili.com/video/av'
video_keys = ['av', 'AV', 'BV', 'bv']

# 作者：mcfx
# 链接：https://www.zhihu.com/question/381784377/answer/1099438784
# 来源：知乎
# 著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。

table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {}
for i in range(58):
    tr[table[i]] = i
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608


def av_dec(x):
    r = 0
    for idx in range(6):
        r += tr[x[s[idx]]] * 58 ** idx
    return (r - add) ^ xor


def av_enc(x):
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for idx in range(6):
        r[s[idx]] = table[x // 58 ** idx % 58]
    return ''.join(r)


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
    read_path = False
    read_prefix = False
    for i in range(1, len(sys.argv)):
        param = sys.argv[i].strip()
        if read_path:
            output = param
            read_path = False
        elif read_prefix:
            prefix = param
            read_prefix = False
        elif param == '-o' or param == '-output':
            read_path = True
        elif param == '-p' or param == '-prefix':
            read_prefix = True
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
                param = 'av{}'.format(av_dec(param))
            if param.startswith('AV') or param.startswith('av'):
                av_number = ''.join(filter(lambda x: x.isdigit(), param))
                av.append(av_number)

    get_danmu_video(av_numbers=av, video=True, output_path=output, name_prefix=prefix, p=p)
