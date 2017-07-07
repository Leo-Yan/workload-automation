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

# pylint: disable=E1101,W0201,E0203

from __future__ import division
import os
import time
from copy import copy

from wlauto import ApkWorkload, Parameter, Alias
from wlauto.exceptions import WorkloadError, ConfigError
from wlauto.utils.types import list_or_string, numeric


class Uibench(ApkWorkload):

    name = 'uibench'
    description = """
    UiBench is a lightweight workload to test performance for Android UI pipeline;
    the testing is based on prebuilt UiBench.apk, this can be built in AOSP
    repository with command: make UiBench.

    In the package, there have many different activities can be choosed to run,
    based on the activity behaviour the workloads can be divided into three kinds:

    - 'swipe': input swipe operations for the activity;
    - 'sleep': after launch the activity, the activity has built-in animation or
               actions, so the workload program only need sleep for timeout;
    - 'click': input tap operations for the activity;

    UiBench has no its own performance statistics so the agenda needs enable
    instrument 'fps' to help capture GPU related metrics for performance profiling.

    """
    package = 'com.android.test.uibench'
    activity = ''

    activity_type = {
        'InflatingListActivity' : 'swipe',
        'TextCacheHighHitrateActivity': 'swipe',
        'FullscreenOverdrawActivity': 'sleep',
        'EditTextTypeActivity': 'sleep',
        'TrivialRecyclerViewActivity': 'swipe',
        'InvalidateActivity': 'sleep',
        'DialogListActivity': 'swipe',
        'ActivityTransition': 'click',
        'TextCacheLowHitrateActivity': 'swipe',
        'ScrollableWebViewActivity': 'swipe',
        'BitmapUploadActivity': 'sleep',
        'TrivialListActivity': 'swipe',
        'SlowBindRecyclerViewActivity': 'swipe',
        'TrivialAnimationActivity': 'sleep',
        'GlTextureViewActivity': 'sleep',
        'ActivityTransitionDetails': 'click',
        'ShadowGridActivity': 'swipe'
    }

    parameters = [
        Parameter('uibench_activity', default='TrivialAnimationActivity', kind=str,
                  allowed_values=list(activity_type.keys()),
                  description='which activity the Uibench test to be run.'),
        Parameter('swipe_time', kind=int, default=100,
                  description='Specifies swipe time.'),
        Parameter('interval', kind=int, default=2,
                  description='Specifies swipe interval time.'),
        Parameter('run_timeout', kind=int, default=10,
                  description="""
                  Run time for workload execution. There have some activities don't need
                  extra operations so sleep specific time for them.
                  """),
    ]

    supported_platforms = ['android']

    def setup(self, context):
        super(Uibench, self).setup(context)

        self.activity = self.uibench_activity
        self.device.ensure_screen_is_on()
        self.command = self._build_command()

    def launch_package(self):
        # Launch package so fps instrument can clear gfxinfo statistics for it
        result = self.device.execute('monkey --pct-syskeys 0 -p {} 1'.format(self.package))
        if 'FAILURE' in result:
            raise WorkloadError(result)
        else:
            self.logger.debug(result)

    def run(self, context):
        result = self.device.execute(self.command)
        if 'FAILURE' in result:
            raise WorkloadError(result)
        else:
            self.logger.debug(result)

        # Workload run for specific time
        start_time = time.time()
        while True:

            if self.activity_type[self.activity] == 'swipe':
                self.swipe_screen()
            elif self.activity_type[self.activity] == 'click':
                self.click_screen()
            else:
                self.device.sleep(self.interval)

            if (time.time() - start_time) > self.run_timeout:
                break

    def update_result(self, context):  # NOQA
        super(Uibench, self).update_result(context)

    def _build_command(self):
        return 'am start -W -S -n {}/.{}'.format(self.package, self.activity)

    def swipe_screen(self):
        width, height = self.device.get_screen_size()
        swipe_time = self.swipe_time

        swipe_middle = width / 2
        start = height * 2 / 3
        stop = height * 1 / 3

        # Firstly swipe up
        command = 'input swipe {} {} {} {} {}'.format(swipe_middle, start, swipe_middle, stop, swipe_time)
        self.device.execute(command)
        self.device.sleep(self.interval)
        # Swipe down so back to original position
        command = 'input swipe {} {} {} {} {}'.format(swipe_middle, stop, swipe_middle, start, swipe_time)
        self.device.execute(command)
        self.device.sleep(self.interval)

    def click_screen(self):
        width, height = self.device.get_screen_size()

        x_axis = width / 2
        y_axis = height / 2

        command = 'input tap {} {}'.format(x_axis, y_axis)
        self.device.execute(command)
        self.device.sleep(self.interval)
