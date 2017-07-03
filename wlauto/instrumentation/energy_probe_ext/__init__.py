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


# pylint: disable=W0613,E1101,access-member-before-definition,attribute-defined-outside-init
import os
import subprocess
import signal
import struct
import csv
import sys
try:
    import pandas
except ImportError:
    pandas = None

sys.path.append(os.path.dirname(sys.modules[__name__].__file__))
from parse_aep import AEP_parser
from collections import defaultdict, OrderedDict

from wlauto import Instrument, Parameter, Executable
from wlauto.exceptions import InstrumentError, ConfigError
from wlauto.utils.types import list_of_numbers


class ArmEnergyProbe(Instrument):

    name = 'energy_probe_ext'
    description = """Collects power traces using the ARM Energy Probe.

                     This instrument requires ``arm-probe`` utility to be installed in the workload automation
                     host and be in the PATH. arm-probe is available here ``https://git.linaro.org/tools/arm-probe.git`` .
                     ARM energy probe device can simultaneously collect power from up to 3 power rails and
                     arm-probe utility can record data from several devices simultaneously.

                     To connect the energy probe on a rail, connect the white wire to the pin that is closer to the
                     Voltage source and the black wire to the pin that is closer to the load (the SoC or the device
                     you are probing). Between the pins there should be a shunt resistor of known resistance in the
                     range of 5 to 500 mOhm but the voltage on the shunt resistor must stay smaller than 165mV.
                     The resistance of the shunt resistors is a mandatory parameter to be set in the ``config`` file.
                    """
    summary_metrics = [ 'Energy', 'Power' ]

    parameters = [
        Parameter('config', kind=str, default='./config',
                  description="""config file path"""),
    ]

    MAX_CHANNELS = 12 # 4 Arm Energy Probes

    def __init__(self, device, **kwargs):
        super(ArmEnergyProbe, self).__init__(device, **kwargs)

    def validate(self):
        if subprocess.call('which arm-probe', stdout=subprocess.PIPE, shell=True):
            raise InstrumentError('arm-probe not in PATH. Cannot enable energy probe ext instrument')
        if not self.config:
            raise ConfigError('a valid config file must be set')

    def setup(self, context):
        self.output_directory = os.path.join(context.output_directory, 'energy_probe')
        self.output_file_raw = os.path.join(self.output_directory, 'data_raw')
        self.output_file = os.path.join(self.output_directory, 'data')
        self.output_file_figure = os.path.join(self.output_directory, 'summary.txt')
        self.command = 'arm-probe --config {} > {}'.format(self.config, self.output_file_raw)
        os.makedirs(self.output_directory)

    def fast_start(self, context):
        self.logger.debug(self.command)
        self.armprobe = subprocess.Popen(self.command,
                                       stderr=subprocess.PIPE,
                                       preexec_fn=os.setpgrp,
                                       shell=True)

    def fast_stop(self, context):
       self.logger.debug("kill running arm-probe")
       os.killpg(self.armprobe.pid, signal.SIGTERM)

    def update_result(self, context):  # pylint: disable=too-many-locals
        self.logger.debug("Parse data and compute consumed energy")
        self.parser = AEP_parser(self.output_file_raw, self.output_file, self.output_file_figure)
        nrg, pwr = self.parser.parse_AEP()
        context.add_metric("Energy", nrg, "J")
        context.add_metric("Power", pwr, "mW (avg)")
