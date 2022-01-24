from PIL import Image as IMG
from PIL import ImageOps
from moviepy.editor import ImageSequenceClip as imageclip
import numpy
import requests
from io import BytesIO
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91)
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0)
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple([f'./PetPetFrames/frame{i}.png' for i in range(5)])


async def save_gif(gif_frames, dest, fps=10):
    """生成 gif

    将输入的帧数据合并成视频并输出为 gif

    参数
    gif_frames: list<numpy.ndarray>
    为每一帧的数据
    dest: str
    为输出路径
    fps: int, float
    为输出 gif 每秒显示的帧数

    返回
    None
    但是会输出一个符合参数的 gif
    """
    clip = imageclip(gif_frames, fps=fps)
    clip.write_gif(dest)  # 使用 imageio
    clip.close()


# 生成函数（非数学意味）
async def make_frame(avatar, i, squish=0, flip=False):
    """生成帧

    将输入的头像转变为参数指定的帧，以供 make_gif() 处理

    参数
    avatar: PIL.Image.Image
    为头像
    i: int
    为指定帧数
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    flip: bool
    为是否横向反转头像

    返回
    numpy.ndarray
    为处理完的帧的数据
    """
    # 读入位置
    spec = list(frame_spec[i])
    # 将位置添加偏移量
    for j, s in enumerate(spec):
        spec[j] = int(s + squish_factor[i][j] * squish)
    # 读取手
    hand = IMG.open(frames[i])
    # 反转
    if flip:
        avatar = ImageOps.mirror(avatar)
    # 将头像放缩成所需大小
    avatar = avatar.resize((int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)), IMG.ANTIALIAS)
    # 并贴到空图像上
    gif_frame = IMG.new('RGB', (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖（包括偏移量）
    gif_frame.paste(hand, (0, int(squish * squish_translation_factor[i])), hand)
    # 返回
    return numpy.array(gif_frame)

async def get_avatar(member_id):
    url = f'https://q2.qlogo.cn/headimg_dl?dst_uin={str(member_id)}&spec=100'
    img_content = requests.get(url).content
    return img_content

async def petpet(member_id, flip=False, squish=0, fps=20) -> None:
    """生成PetPet

    将输入的头像生成为所需的 PetPet 并输出

    参数
    path: str
    为头像路径
    flip: bool
    为是否横向反转头像
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    fps: int
    为输出 gif 每秒显示的帧数

    返回
    bool
    但是会输出一个符合参数的 gif
    """

    gif_frames = []
    img_content = await get_avatar(member_id)
    avatar = IMG.open(BytesIO(img_content))

    # 生成每一帧
    for i in range(5):
        gif_frames.append(await make_frame(avatar, i, squish=squish, flip=flip))
    # 输出
    await save_gif(gif_frames, f'./temp/tempPetPet-{member_id}.gif', fps=fps)
    avatar.close()

def make(member_id):
    try:
        petpet(member_id).send((None))
    except StopIteration as e:
        print(e)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        req_datas = self.rfile.read(int(self.headers['content-length']))
        print("get--")
        res = req_datas.decode('utf-8')
        print(res)
        member_id = res.split("=")[1]
        make(int(member_id))
        print("finish---")

        self.send_response(200)
        self.send_header('Content_type', 'application/json;charset=utf-8')
        self.end_headers()
        path = os.getcwd() + f"/temp/tempPetPet-{member_id}.gif"
        data = json.dumps({'msg': 200, 'path': path})
        self.wfile.write(data.encode('utf-8'))

if not os.path.exists("./temp"):
    os.mkdir("./temp")

host = ('0.0.0.0', 8888)
server = HTTPServer(host, Handler)
print("Starting server, listen at: %s:%s" % host)
server.serve_forever()

