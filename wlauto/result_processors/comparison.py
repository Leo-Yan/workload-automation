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

import array
import argparse
import collections
import csv
import os
import re
import sys
import sys, getopt
from collections import Counter
from os import system, remove
from collections import defaultdict
from wlauto import ResultProcessor
from wlauto.utils.misc import write_table

class ComparisionReporter(ResultProcessor):

    name = 'comparison'
    description = """
    Outputs txt files and png pictures for result comparison

    """

    power_scenarios = {
        'idle'         : [ 'Power' ],
        'audio'        : [ 'Power' ],
        'video'        : [ 'Power' ],
        'hackbench'    : [ 'Power' ],
        'geekbench'    : [ 'Power' ],
        'linpack'      : [ 'Power' ],
        'quadrant'     : [ 'Power' ],
        'smartbench'   : [ 'Power' ],
        'nenamark'     : [ 'Power' ],
        'recentfling'  : [ 'Power' ],
        'galleryfling' : [ 'Power' ],
        'browserfling' : [ 'Power' ],
    }

    perf_scenarios = {
        'hackbench'    : [ 'test_time' ],
        'geekbench'    : [ 'score',
                           'multicore_score' ],
        'linpack'      : [ 'Linpack ST',
                           'Linpack MT' ],
        'quadrant'     : [ 'benchmark_score' ],
        'smartbench'   : [ 'Smartbench: valueProd',
                           'Smartbench: valueGame' ],
        'nenamark'     : [ 'nenamark score' ],
        'recentfling'  : [ 'Average 90th Percentile',
                           'Average 95th Percentile',
                           'Average 99th Percentile',
                           'Average Jank',
                           'Average Jank%' ],
        'galleryfling' : [ 'Average 90th Percentile',
                           'Average 95th Percentile',
                           'Average 99th Percentile',
                           'Average Jank',
                           'Average Jank%' ],
        'browserfling' : [ 'Average 90th Percentile',
                           'Average 95th Percentile',
                           'Average 99th Percentile',
                           'Average Jank',
                           'Average Jank%' ],
        'emailfling'   : [ 'Average 90th Percentile',
                           'Average 95th Percentile',
                           'Average 99th Percentile',
                           'Average Jank',
                           'Average Jank%' ],
    }

    # Parse the testing sections, every section is corresponding to one
    # kernel image or one set configurations
    sections = []

    baseline = None

    def parse_sections(self):

        sec = []

        self.fr = open(self.infile, "r")
        in_line = csv.reader(self.fr)
        next(in_line, None)

        # Abstract the section id
        p = re.compile(r'(.*)_\d', re.I)

        for row in in_line:
            m = re.match(p, row[0])
            section = m.group(1)

            if not section in sec:
                sec.append(section)

        sec.sort()

        self.baseline = sec[0]
        return sec

    def plot_comparison(self, comp_type):

        sec_num = len(self.sections)
        sec_num += 1

        pic_file = os.path.join(self.outdir, comp_type + '_comparison.png')

        temp_f = open('/tmp/plot_template', "w+")
        temp_f.write("set terminal pngcairo noenhanced size 1024,600 font 'Ubuntu,9'\n")
        temp_f.write("set output '"+ pic_file + "'\n")
        temp_f.write("set grid\n")
        temp_f.write("set title " + "'" + comp_type + " Comparision'\n")
        temp_f.write("set ylabel " + "'" + comp_type + " Result'\n")
        temp_f.write("set boxwidth 0.9 absolute\n")
        temp_f.write("set style fill solid 1.00 border lt -1\n")
        temp_f.write("set key outside right\n")
        temp_f.write("set style histogram clustered gap 1 title  offset character 0, 0, 0\n")
        temp_f.write("set datafile missing '-'\n")
        temp_f.write("set style data histograms\n")
        temp_f.write("set xtics rotate by -45\n")
        temp_f.write("set xtics ()\n")
        temp_f.write("plot for [i=2:"+str(sec_num)+"] filename using i:xtic(1) ti col ls i-1;\n")
        temp_f.write("set terminal wxt noenhanced font 'Ubuntu,9'\n")
        temp_f.close()

        outfile = os.path.join(self.outdir, comp_type + '_plot.txt')
        os.system('gnuplot -e "filename=\'' + outfile + '\''+'" /tmp/plot_template')

    def write_scenario(self, scene, metric, value, baseline=None):

        self.fo.write(scene.replace(" ", "_") + '_' + metric.replace(" ", "_"))

        if not baseline is None:
            for m, values in sorted(value[baseline].items()):
                if m == metric:
                    base = sum(values) / len(values)
                    break
        else:
            base = 0

        for kern in self.sections:
            collectValue = sorted(value[kern].items())
            for m, values in collectValue:
                if m == metric:
                    self.fo.write(' ' + str(sum(values) / len(values) - base))

        self.fo.write('\n')

    def parse_scenario(self, scene, scenarios):

        l1_Value = dict()

        p = re.compile(r'(.*)_\d', re.I)

        for kern in self.sections:

            l2_Value = defaultdict(list)

            self.fr = open(self.infile, "r")
            in_line = csv.reader(self.fr)
            next(in_line, None)

            for row in in_line:

                m = re.match(p, row[0])

                if row[1] not in scene:
                    continue

                section   = m.group(1)
                condition = row[3]
                value     = row[4]

                if condition not in scenarios[scene]:
                    continue

                if section != kern:
                    continue

                l2_Value[condition].append(float(value))
                l1_Value[section] = l2_Value

        return l1_Value

    def parse_scenarios(self, scenarios, comp_str, baseline=None):

        outfile = os.path.join(self.outdir, comp_str + '_plot.txt')
        self.fo = open(outfile, "w+")
        self.fo.write('test')

        for kern in self.sections:
            self.fo.write(' ' + kern)
        self.fo.write('\n')

        has_data = False

        for s in scenarios:
            value = self.parse_scenario(s, scenarios)
            if bool(value) == False:
                continue
            has_data = True

            for metric in scenarios[s]:
                self.write_scenario(s, metric, value, baseline)
        self.fo.close()

        # Skip comparison when scenario data is empty
        if has_data is False:
            self.logger.info("{}: data is empty".format(comp_str))
            return

        self.plot_comparison(comp_str)

    def parse_power(self):
        self.parse_scenarios(self.power_scenarios, 'power')
        self.parse_scenarios(self.power_scenarios, 'power_delta', self.baseline)

    def parse_perf(self):
        self.parse_scenarios(self.perf_scenarios, 'performance')
        self.parse_scenarios(self.perf_scenarios, 'performance_delta', self.baseline)

    def parse_file(self):
        self.sections = self.parse_sections()
        self.parse_power()
        self.parse_perf()

    def process_run_result(self, result, context):

        infile = os.path.join(context.run_output_directory, 'results.csv')
        self.logger.info('Status available in {}'.format(infile))

        if not os.path.isfile(infile):
            print "file don't exists:"
            return

        self.infile = infile
        self.outdir = context.run_output_directory
        self.parse_file()
