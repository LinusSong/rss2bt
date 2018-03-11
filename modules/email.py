import smtplib
from email.mime.text import MIMEText

import yaml

class EmailSender(object):
    """此模块的设计目的是为了在程序运行过程中收集需要发送的数据，并最终发送
    """
    def __init__(self, config):
        self.config = config
        self.mail = {}

    def add_text(self, item_key, entries=None, flag='update'):
        if not flag in self.mail:
            if flag == 'update':
                self.mail.update({flag:{}})
            else:
                self.mail.update({flag:[]})
        if flag == 'update':
            epis_string = ', '.join([str(i['episode']) for i in entries])
            self.mail[flag].update({item_key:epis_string})
        else:
            self.mail[flag].append(item_key)

    def compile_mail(self):
        email_text = yaml.safe_dump(self.mail,default_flow_style=False,allow_unicode=True)
        return email_text

    def send_mail(self,text):
        "Send mail"
        sender = self.config['email_username']
        smtpHost = 'smtp.' + sender[sender.find('@')+1:]
        msg =MIMEText(text)
        msg['Subject'] = '今日新番'
        msg['to'] = self.config['email_receiver']
        msg['From'] = sender
        smtp = smtplib.SMTP_SSL(smtpHost,'465')
        smtp.ehlo()
        smtp.login(sender, self.config['email_password'])
        smtp.sendmail(sender, self.config['email_receiver'], msg.as_string())
        smtp.quit()
