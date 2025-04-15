import pypandoc
from premailer import transform
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import ssl
from email.mime.base import MIMEBase
from email import encoders
import re
from datetime import datetime
import pytz
from datetime import timedelta

# 定义变量字典，用于替换邮件内容中的占位符
def get_variables():
    # 变量值
    variables = {
        'spaceone_name': '陈思怡',  # 收件人姓名
        'spaceone_phase': '三期',  # Space One期数
        'spaceone_paragraph_1': '特别赞。',  # 自定义段落1
        'spaceone_paragraph_2': '赞。',  # 自定义段落2
        'spaceone_paragraph_3': '赞。',  # 自定义段落3
        'spaceone_paragraph_4': '赞。',  # 自定义段落4
        'spaceone_paragraph_5': '赞。',  # 自定义段落5
        'spaceone_offerings': '「一场」Space One',  # 产品
        'spaceone_cost': '39999',  # 费用
        'spaceone_current_time': datetime.now().strftime('%Y年%m月%d日'),  # 当前时间
        'spaceone_fees_Deadline': (datetime.now(pytz.timezone('Asia/Shanghai')) + timedelta(days=3)).strftime('%Y年%m月%d日'),  # 付款截止时间（当前北京时间+3天）
        'spaceone_member_start': '2025年8月24日',  # 会员开始时间
        'spaceone_member_start_1': '2025年8月25日',  # 会员开始时间（入场式第二天）
        'spaceone_membership_end': '2026年8月24日',  # 会员结束时间
    }
    
    return variables

# 获取邮件变量
variables = get_variables()


# 读取 Markdown 文件并替换占位符
with open('邮件内容.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

# 替换所有占位符
for key, value in variables.items():
    md_text = md_text.replace('{{&' + key + '}}', str(value))

# 转换为带内联 CSS 的 HTML
html_content = pypandoc.convert_text(md_text, 'html', format='md')
basic_css = """body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333333; }
h1, h2, h3 { color: #222222; }
p { margin: 10px 0; }
ul, ol { margin: 10px 0; padding-left: 20px; }
code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }"""
html_with_css = f"<style>{basic_css}</style>{html_content}"
inlined_html = transform(html_with_css)

# 同样替换纯文本版本中的占位符
plain_text = md_text

# SMTP 配置
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.qq.com')
SMTP_USER = os.getenv('SMTP_USER', 'space-one@qq.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'eudyjptmnvjffbec')

# 邮件收件人和主题
mail_recipient = 'chenswonderland123@gmail.com'
subject = '「一场+」Space One 视频沟通结果通知'

def send_email(html_content, plain_text, mail_recipient, subject):
    """发送单个邮件
    
    Args:
        html_content (str): HTML格式的邮件内容
        plain_text (str): 纯文本格式的邮件内容
        mail_recipient (str): 收件人邮箱地址
        subject (str): 邮件主题
    """
    # 创建多部分邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = mail_recipient

    # 添加纯文本和HTML内容
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 添加附件：两张图片，中文文件名使用 RFC2231 编码
    for attachment_path in ['./image/小助手企业微信.jpeg', './image/邀请函.jpg']:
        if os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as att:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(att.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", os.path.basename(attachment_path)))
            msg.attach(part)
        else:
            print(f"附件未找到: {attachment_path}")

    # 发送邮件
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, mail_recipient, msg.as_string())
        server.quit()
        print("邮件发送成功!")
    except Exception as e:
        print("邮件发送错误:", str(e))

# 发送邮件
send_email(inlined_html, plain_text, mail_recipient, subject)
