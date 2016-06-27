#    Copyright 2013-2015 ARM Limited
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
# Steve Muckle, smuckle@linaro.org: This file is based on the recentfling
# workload by ARM.

#pylint: disable=E1101,W0201

import os
import re
from collections import defaultdict

from wlauto import Workload, Parameter, File
from wlauto.utils.types import caseless_string
from wlauto.exceptions import WorkloadError, DeviceError


class Emailfling(Workload):

    name = 'emailfling'
    description = """
    Tests UI jank on android devices.
    """
    supported_platforms = ['android']

    parameters = [
        Parameter('loops', kind=int, default=3,
                  description="The number of test iterations."),
    ]

    def initialise(self, context):  # pylint: disable=no-self-use
        if context.device.get_sdk_version() < 23:
            raise WorkloadError("This workload relies on ``dumpsys gfxinfo`` \
                                 only present in Android M and onwards")

    def setup(self, context):
        self.testdir = '/'.join([self.device.working_directory, 'emailfling'])
        self.testscript_target = self.testdir + "/emailfling.sh"
        self.testdefs_target = self.testdir + "/defs.sh"

        if not self.device.file_exists(self.testdir):
            self.device.execute('mkdir -p {}'.format(self.testdir))

        if not self.device.file_exists(self.testscript_target):
            self.testscript_host = context.resolver.get(File(self, "emailfling.sh"))
            self.device.push_file(self.testscript_host, self.testscript_target)

        if not self.device.file_exists(self.testdefs_target):
            self.testdefs_host = context.resolver.get(File(self, "defs.sh"))
            self.device.push_file(self.testdefs_host, self.testdefs_target)

        self._kill_emailfling()
        self.device.ensure_screen_is_on()

    def run(self, context):
        args = '-i {} '.format(self.loops)
        cmd = "echo $$>{dir}/pidfile; cd {bindir}; exec ./emailfling.sh {args}; rm {dir}/pidfile"
        cmd = cmd.format(args=args, dir=self.device.working_directory, bindir=self.testdir)
        try:
            self.output = self.device.execute(cmd, timeout=120)
        except KeyboardInterrupt:
            self._kill_emailfling()
            raise

    def update_result(self, context):
        group_names = ["90th Percentile", "95th Percentile", "99th Percentile", "Jank", "Jank%"]
        count = 0
        for line in self.output.strip().splitlines():
            p = re.compile("Frames: \d+ latency: (?P<pct90>\d+)/(?P<pct95>\d+)/(?P<pct99>\d+) Janks: (?P<jank>\d+)\((?P<jank_pct>\d+)%\)")
            match = p.search(line)
            if match:
                count += 1
                if line.startswith("AVE: "):
                    group_names = ["Average " + g for g in group_names]
                    count = 0
                for metric in zip(group_names, match.groups()):
                    context.result.add_metric(metric[0],
                                              metric[1],
                                              None,
                                              classifiers={"loop": count or "Average"})

    def teardown(self, context):
        print "Leaving emailfling files on target..."
#        self.device.uninstall_executable(self.emailfling_target)
#        self.device.uninstall_executable(self.defs_target)

    def _kill_emailfling(self):
        command = 'cat {}/pidfile'.format(self.device.working_directory)
        try:
            pid = self.device.execute(command)
            if pid.strip():
                self.device.kill(pid.strip(), signal='SIGKILL')
        except DeviceError:
            pass  # may have already been deleted
