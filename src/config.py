# config.py
# 配置模块，用于管理SMTP设置和其他常量配置

import os

# SMTP配置
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.qq.com'),
    'user': os.getenv('SMTP_USER', 'space-one@qq.com'),
    'password': os.getenv('SMTP_PASSWORD', 'eudyjptmnvjffbec'),
    'port': 465
}

# 邮件相关配置
EMAIL_CONFIG = {
    'subject': '「一场+」Space One 视频沟通结果通知',
    'default_attachments': ['./resources/images/image/小助手企业微信.jpeg'],
    'template_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', '邮件内容.md')
}

# 图片相关配置
IMAGE_CONFIG = {
    'ticket_template_path': './resources/images/image/入场劵模版.png',
    'ticket_output_dir': './resources/images/学员入场券/',
    'font_path': './resources/fonts/HongLeiBanShuJianTi-2.ttf'
}

# 日期格式配置
DATE_FORMAT = {
    'input': '%Y/%m/%d',
    'output': '%Y年%m月%d日',
    'month_only': '%Y年%m月'
}