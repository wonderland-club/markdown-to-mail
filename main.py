from flask import Flask, request, jsonify
import pypandoc
from premailer import transform
import smtplib
import os
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import pytz
import re
from picture import making_tickets  # 新增导入 making_tickets

app = Flask(__name__)

def get_variables_from_request(data):
    """
    根据 POST 请求的 JSON 数据生成邮件模板替换用的变量字典。
    如果请求中未提供某变量，则使用预设默认值。
    """
    variables = {}
    # 使用请求数据中的变量，或使用默认值
    variables['spaceone_name'] = data.get('spaceone_name')
    variables['spaceone_phase'] = data.get('spaceone_phase')
    variables['spaceone_paragraph'] = data.get('spaceone_paragraph')
    # 这里注意：如果邮件模板中仅用一个段落占位符，请确保模板中使用的占位符名称与此处一致
    variables['spaceone_paragraph'] = data.get('spaceone_paragraph')
    variables['spaceone_offerings'] = data.get('spaceone_offerings')
    variables['spaceone_cost'] = data.get('spaceone_cost')
    variables['spaceone_current_time'] = datetime.now().strftime('%Y年%m月%d日')
    variables['spaceone_fees_Deadline'] = (datetime.now(pytz.timezone('Asia/Shanghai')) + timedelta(days=3)).strftime('%Y年%m月%d日')
    variables['spaceone_member_start'] = data.get('spaceone_member_start')
    print(variables['spaceone_member_start'])
    # 如果需要为“入场式第二天”提供变量，可以自动计算或设定默认值
    
    
    try:
        # 解析原始日期格式：例如 "2025/05/01"
        dt_member_start = datetime.strptime(variables['spaceone_member_start'], '%Y/%m/%d')
        # 将格式转换为 "YYYY年MM月DD日"
        variables['spaceone_member_start'] = dt_member_start.strftime('%Y年%m月%d日')
        # 计算 +1 天后的日期，并格式化
        dt_member_start_1 = dt_member_start + timedelta(days=1)
        variables['spaceone_member_start_1'] = dt_member_start_1.strftime('%Y年%m月%d日')
    except Exception as e:
        variables['spaceone_member_start'] = '0000年0月0日'
        variables['spaceone_member_start_1'] = '0000年0月0日'
    variables['spaceone_membership_end'] = data.get('spaceone_membership_end')
    return variables

def send_email(html_content, plain_text, mail_recipient, subject, extra_attachments=None):
    """
    根据生成的邮件内容，利用 SMTP 发送邮件。

    参数:
        html_content (str): 内嵌 CSS 样式的 HTML 邮件内容
        plain_text (str): 纯文本格式邮件内容
        mail_recipient (str): 收件人邮箱
        subject (str): 邮件主题
        extra_attachments (list): 额外的附件路径列表
    """
    # 从环境变量获取 SMTP 配置，如果环境变量中无配置则使用默认值
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.qq.com')
    SMTP_USER = os.getenv('SMTP_USER', 'space-one@qq.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'eudyjptmnvjffbec')
    
    # 构造多部分邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = mail_recipient

    # 添加纯文本和 HTML 内容
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 添加附件
    attachment_paths = ['./image/小助手企业微信.jpeg']
    if extra_attachments:
        attachment_paths += extra_attachments
    for attachment_path in attachment_paths:
        if os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", os.path.basename(attachment_path)))
            msg.attach(part)
        else:
            print(f"附件未找到: {attachment_path}")
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, mail_recipient, msg.as_string())
        server.quit()
        print("邮件发送成功!")
        return True, "邮件发送成功"
    except Exception as e:
        print("邮件发送错误:", str(e))
        return False, str(e)

@app.route('/send_email', methods=['POST'])
def handle_send_email():
    """
    接收 POST 请求，解析 JSON 内容后：
      1. 根据数据生成变量字典。
      2. 读取 Markdown 模板文件并替换模板中的占位符。
      3. 将替换后的内容转换为 HTML（并内联 CSS），生成纯文本版本。
      4. 发送邮件。
    """
    step_status = {}

    # 获取 JSON 数据
    data = request.get_json()
    if not data:
        step_status['获取信息'] = '错误: 请求体为空或无效 JSON'
        return jsonify({"success": False, "message": "请求体为空或不是有效的 JSON", "step_status": step_status}), 400
    step_status['获取信息'] = '成功'
    
    # 检查必须的参数 mail_recipient
    mail_recipient = data.get("mail_recipient")
    if not mail_recipient:
        step_status['检查 mail_recipient'] = '错误: 缺少 mail_recipient 参数'
        return jsonify({"success": False, "message": "缺少 mail_recipient 参数", "step_status": step_status}), 400
    step_status['检查 mail_recipient'] = '成功'
    
    # 根据请求数据生成变量字典
    variables = get_variables_from_request(data)
    step_status['生成变量'] = '成功'
    
    # 读取 Markdown 邮件模板，并进行占位符替换
    try:
        with open('邮件内容.md', 'r', encoding='utf-8') as f:
            md_text = f.read()
        step_status['读取邮件模板'] = '成功'
    except Exception as e:
        step_status['读取邮件模板'] = f'错误: {e}'
        return jsonify({"success": False, "message": f"读取邮件模板失败: {str(e)}", "step_status": step_status}), 500

    # 替换模板中所有以 {{&key}} 格式的占位符
    for key, value in variables.items():
        md_text = md_text.replace('{{&' + key + '}}', str(value))
    step_status['模板替换'] = '成功'

    # Markdown 转换为 HTML
    try:
        html_content = pypandoc.convert_text(md_text, 'html', format='md')
        step_status['Markdown 转 HTML'] = '成功'
    except Exception as e:
        step_status['Markdown 转 HTML'] = f'错误: {e}'
        return jsonify({"success": False, "message": f"Markdown 转换失败: {str(e)}", "step_status": step_status}), 500

    # 内联 CSS 样式
    basic_css = """
    body {     font-family: Arial, sans-serif;     font-size: 14px;     line-height: 1.6;     color: black !important; } h1, h2, h3 {     color: black; } p {     margin: 10px 0; } ul, ol {     margin: 10px 0;     padding-left: 20px; } code {     padding: 2px 4px;     border-radius: 3px; } a:link, a:visited {     color: black;     text-decoration: none; } a:hover {     color: black; } .im {     color: black !important;     font-family: Arial, sans-serif;     font-size: 14px;     line-height: 1.6; }
    
    """
    html_with_css = f"<style>{basic_css}</style>{html_content}"
    inlined_html = transform(html_with_css)
    step_status['内联 CSS'] = '成功'

    # 调用 making_tickets 制作入场券图片，并构造附件路径
    ticket_in_time =  variables.get('spaceone_member_start')
    ticket_in_time_full = variables.get('spaceone_member_start')
    m = re.match(r'(\d+年\d+月)', ticket_in_time_full)
    ticket_in_time = m.group(1) if m else ticket_in_time_full
    ticket_in_period =  variables.get('spaceone_phase')[0]
    ticket_interviewer_name = variables.get('spaceone_name')
    making_tickets(ticket_in_time, ticket_in_period, ticket_interviewer_name)
    ticket_attachment = f'./image/学员入场劵/{ticket_in_period}期入场券-{ticket_interviewer_name}.png'

    # 附件预检查：检查附件是否存在（包含入场券图片）
    attachment_paths = ['./image/小助手企业微信.jpeg', ticket_attachment]
    missing_attachments = [path for path in attachment_paths if not os.path.exists(path)]
    if missing_attachments:
        step_status['附件检查'] = f"错误: 未找到附件 {missing_attachments}"
        return jsonify({"success": False, "message": f"附件检查失败: 未找到附件 {missing_attachments}", "step_status": step_status}), 500
    else:
        step_status['附件检查'] = '成功'
    
    # 对于纯文本版，可直接使用替换后的 Markdown 文本
    plain_text = md_text

    subject = '「一场+」Space One 视频沟通结果通知'
    
    # 调用 send_email 时传入入场券图片附件
    success, send_status = send_email(inlined_html, plain_text, mail_recipient, subject, extra_attachments=[ticket_attachment])
    step_status['邮件发送'] = '成功' if success else f'错误: {send_status}'

    if success:
        return jsonify({"success": True, "message": "邮件发送成功!", "step_status": step_status})
    else:
        return jsonify({"success": False, "message": f"邮件发送失败: {send_status}", "step_status": step_status}), 500

if __name__ == '__main__':
    # 启动 Flask 服务器，监听所有网卡 5000 端口
    app.run(host='0.0.0.0', port=5001)
