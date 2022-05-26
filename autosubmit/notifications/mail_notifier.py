#!/usr/bin/env python3

# Copyright 2015-2020 Earth Sciences Department, BSC-CNS

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.

import smtplib
import email.utils
from email.mime.text import MIMEText
from log.log import Log

class MailNotifier:
    def __init__(self, basic_config):
        self.config = basic_config

    def notify_experiment_status(self, exp_id,mail_to,platform):
        message_text = self._generate_message_experiment_status(exp_id, platform)
        message = MIMEText(message_text)
        message['From'] = email.utils.formataddr(('Autosubmit', self.config.MAIL_FROM))
        message['Subject'] = '[Autosubmit] Warning a remote platform is malfunctioning'
        for mail in mail_to:
            message['To'] = email.utils.formataddr((mail, mail))
            try:
                self._send_mail(self.config.MAIL_FROM, mail, message)
            except BaseException as e:
                Log.printlog('An error has occurred while sending a mail for warn about remote_platform', 6011)
    def notify_status_change(self, exp_id, job_name, prev_status, status, mail_to):
        message_text = self._generate_message_text(exp_id, job_name, prev_status, status)
        message = MIMEText(message_text)
        message['From'] = email.utils.formataddr(('Autosubmit', self.config.MAIL_FROM))
        message['Subject'] = '[Autosubmit] The job {0} status has changed to {1}'.format(job_name, str(status))
        for mail in mail_to:
            message['To'] = email.utils.formataddr((mail, mail))
            try:
                self._send_mail(self.config.MAIL_FROM, mail, message)
            except BaseException as e:
                Log.printlog('An error has occurred while sending a mail for the job {0}'.format(job_name), 6011)

    def _send_mail(self, mail_from, mail_to, message):
        server = smtplib.SMTP(self.config.SMTP_SERVER)
        server.sendmail(mail_from, mail_to, message.as_string())
        server.quit()

    @staticmethod
    def _generate_message_text(exp_id, job_name, prev_status, status):
        return 'Autosubmit notification\n' \
               '-------------------------\n\n' \
                'Experiment id:  ' + str(exp_id) + '\n\n' \
                + 'Job name:  ' + str(job_name) + '\n\n' \
                'The job status has changed from: ' + str(prev_status) + ' to ' + str(status) + '\n\n\n\n\n' \
                'INFO: This message was auto generated by Autosubmit, '\
                'remember that you can disable these messages on Autosubmit config file. \n'

    @staticmethod
    def _generate_message_experiment_status(exp_id, platform=""):
        return 'Autosubmit notification: Remote Platform issues\n' \
               '-------------------------\n\n' \
                'Experiment id:  ' + str(exp_id) + '\n\n' \
                + 'Platform affected:' + str(platform.name) + " using as host:" + str(platform.host) + '\n\n' \
                '[WARN] Autosubmit encountered an issue with an remote_platform.\n It will resume itself, whenever is possible\n If issue persist, you can change the host IP or put multiple hosts in the platform.yml' + '\n\n\n\n\n' \
                'INFO: This message was auto generated by Autosubmit, '\
                'remember that you can disable these messages on Autosubmit config file. \n'