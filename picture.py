import re
from PIL import Image, ImageDraw, ImageFont

def draw_bold_text(draw, text, position, font, fill, offsets):
    # 封装加粗文字的绘制
    for offset in offsets:
        pos = (position[0] + offset[0], position[1] + offset[1])
        draw.text(pos, text, font=font, fill=fill)

def making_tickets(in_time, in_period, interviewer_name):
    # 加载图片
    image_path = r'./image/0.png'
    output_path = rf'./image/学员入场劵/{in_period}期入场券-{interviewer_name}.png'
    image = Image.open(image_path)

    # 设置字体
    font_path = r'./HongLeiBanShuJianTi-2.ttf'
    font_large = ImageFont.truetype(font_path, 63)
    font_small = ImageFont.truetype(font_path, 48)

    # 提取年份和月份
    year_match = re.search(r'(\d+)年', in_time)
    in_year = year_match.group(1) if year_match else None
    month_match = re.search(r'年(\d+)月', in_time)
    in_month = month_match.group(1) if month_match else None

    # 设置文字内容和位置
    texts = [
        {"text": interviewer_name, "position": (196, image.height - 1001), "font": font_large},
        {"text": in_period, "position": (283, image.height - 594), "font": font_large},
        {"text": in_year, "position": (810, image.height - 225), "font": font_small},
        {"text": in_month, "position": (1013, image.height - 207), "font": font_small}
    ]

    # 创建绘图对象及设置颜色与加粗偏移量
    draw = ImageDraw.Draw(image)
    text_color = (0, 0, 0)  # 纯黑
    offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]

    # 绘制文字
    for item in texts:
        pos = item["position"]
        # 如果是月份，则进行居中处理
        if item["text"] == in_month and in_month is not None:
            bbox = draw.textbbox((0, 0), item["text"], font=item["font"])
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            pos = (pos[0] - (text_width / 2), pos[1] - (text_height / 2))
        draw_bold_text(draw, item["text"], pos, item["font"], text_color, offsets)

    # 保存修改后的图片
    image.save(output_path)
    print("图片处理完成")
    
# making_tickets('2025年05月', '五', '曹文杰')