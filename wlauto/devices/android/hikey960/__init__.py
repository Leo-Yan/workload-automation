#    Copyright 2017 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import re
import time
import pexpect

from wlauto import AndroidDevice, Parameter
from wlauto.exceptions import TimeoutError
from wlauto.utils.serial_port import open_serial_connection, pulse_dtr
from wlauto.utils.android import adb_connect, adb_disconnect, adb_list_devices
from wlauto.utils.android import adb_shell


class Hikey960(AndroidDevice):

    name = "hikey960"
    description = """
    96boards Hisilicon Hikey960 big.LITTLE development platform.
    """

    core_modules = [
        'hikey960_fastboot',
    ]

    parameters = [
        Parameter('adb_name', default='270182BA020B1AA2', override=True),
        Parameter('working_directory', default='/data/wa-working', override=True),
        Parameter('core_names', default=['a53', 'a53', 'a53', 'a53', 'a73', 'a73', 'a73', 'a73'], override=True),
        Parameter('core_clusters', default=[0, 0, 0, 0, 1, 1, 1, 1], override=True),
        Parameter('port', default='/dev/ttyUSB0', kind=str,
                  description='Serial port on which the device is connected'),
        Parameter('baudrate', default=115200, kind=int, description='Serial connection baud rate'),
        Parameter('timeout', kind=int, default=300, description='Serial connection timeout.'),
    ]

    firmware_prompt = 'UEFI firmware'
    android_prompt = 'hikey960:/ $'

    def __init__(self, **kwargs):
        super(Hikey960, self).__init__(**kwargs)
        self._just_rebooted = False

    def initialize(self, context):
        self.execute('svc power stayon true', check_exit_code=False)

    def reset(self):
        super(Hikey960, self).reset()

        with open_serial_connection(port=self.port,
                                    baudrate=self.baudrate,
                                    timeout=self.timeout,
                                    init_dtr=0) as target:

            self.logger.debug('Waiting for board reboot...')

            try:
                target.expect(self.firmware_prompt, 30)
            except pexpect.TIMEOUT:
                self.logger.debug('Timeout: use hard reset method')
                self.hard_reset()
                pass
            except pexpect.EOF:
                self.logger.debug('EOF: use hard reset method to ensure reboot')
                self.hard_reset()
                pass

            target.close()

        self._just_rebooted = True

    def hard_reset(self):
        os.system('ssh 192.168.2.44 "echo "relay8 off" > /dev/ttyACM0"')
        time.sleep(3)
        os.system('ssh 192.168.2.44 "echo "relay8 on" > /dev/ttyACM0"')
        self._just_rebooted = True

    def connect(self):  # NOQA pylint: disable=R0912
        if not self.adb_name in adb_list_devices():
            self.hard_reset();
            time.sleep(60)

        super(Hikey960, self).connect()
        if self._just_rebooted:
            self.logger.debug('Waiting for boot to complete...')
            # adb connection gets reset after board rebooting and have no 'root'
            # permission for some testing case. To fix this, open a shell
            # session and wait for it to be killed. Once its killed, give adb
            # enough time to restart, and then the device should be ready.
            try:
                adb_shell(self.adb_name, '', timeout=20, as_root=True)
                time.sleep(5)  # give adb time to re-initialize
            except TimeoutError:
                pass  # timed out waiting for the session to be killed -- assume not going to be.

            self.logger.debug('Boot completed.')
            self._just_rebooted = False

    def disconnect(self):
        super(Hikey960, self).disconnect()

