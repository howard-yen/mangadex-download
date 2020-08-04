import os
import smtplib, ssl, email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass

# EmailDraft handles sending attachments in emails to
# minimize the total number of email sent
class EmailDraft:
    # the maximum size of attachment allowed by email in bytes
    # default is 25 mb for gmail
    MAX_ATTACHMENT_CAPACITY = 250000000

    # constructs an EmailDraft with the given information,
    # prompts for information is none given
    # could change to require valid info
    def __init__(self, title, sender_email='', receiver_email='', password='', bcc_emails=[]):
        self.__size = 0
        self.__title = title

        #TODO add email validation
        if sender_email == '':
            self.__sender_email = input('sender email: ')
        else:
            self.__sender_email = sender_email

        if receiver_email == '':
            self.__receiver_email = [input('receiver email: ')] + bcc_emails
        else:
            self.__receiver_email = [receiver_email] + bcc_emails

        if password == '':
            self.__password = getpass.getpass('email password: ')
        else:
            self.__password = password

        self.__message = self.__createMessage()
        # need to attach later
        self.__body = 'the following chapters are attached:\n'
        try:
            self.__context = ssl.create_default_context()
            self.__server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=self.__context)
            print(f'{self.__sender_email} || self.__password')
            self.__server.login(self.__sender_email, self.__password)
        except smtplib.SMTPAuthenticationError:
            print('authentication error occurred...')
        except:
            print('failed to connect to server and establish a connection...')

    # send the email and create a new message
    def __sendEmail(self, newMessage = True):
        self.__message.attach(MIMEText(self.__body, "plain"))
        if self.__size > 0:
            try:
                self.__server.sendmail(self.__sender_email, self.__receiver_email, self.__message.as_string())
                if newMessage:
                    self.__message = self.__createMessage()
                self.__size = 0
            except: # could raise error here instead
                print('an error occurred while sending email...')

    # create a basic message without any attachments
    def __createMessage(self):
        message = MIMEMultipart()

        subject = f'{self.__title} manga pdf'
        message["From"] = self.__sender_email
        message["To"] = self.__receiver_email
        message["Subject"] = subject

        return message

    # add an attachment filename to the email
    def addAttachment(self, filename):
        # check size, need to send first before adding if over capacity
        filesize = os.path.getsize(filename)
        if filesize + self.__size > self.MAX_ATTACHMENT_CAPACITY:
            __sendEmail()

        self.__body += f'{filename}\n'

        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        self.__message.attach(part)

    # send an entire directory of file as attachments
    def sendDir(self, dir):
        if not os.path.exists(dir):
            print(f'directory {dir} does not exist, could not send email...')
            return

        tempdir = os.getcwd()
        os.chdir(dir)
        for f in os.listdir():
            self.addAttachment(f)
        self.__sendEmail(newMessage=False)
        os.chdir(tempdir)

    # send remaining attachments and close connection to server
    def close(self):
        if self.__size > 0:
            self.__sendEmail(newMessage=False)
        server.quit()
