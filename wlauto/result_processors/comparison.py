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
        'idle'                                      : [ 'Power' ],
        'audio'                                     : [ 'Power' ],
        'video'                                     : [ 'Power' ],
        'rt_app'                                    : [ 'Power' ],
        'hackbench'                                 : [ 'Power' ],
        'geekbench'                                 : [ 'Power' ],
        'linpack'                                   : [ 'Power' ],
        'quadrant'                                  : [ 'Power' ],
        'smartbench'                                : [ 'Power' ],
        'nenamark'                                  : [ 'Power' ],
    }

    power_interactive_scenarios = {
        'recentfling'                               : [ 'Power' ],
        'galleryfling'                              : [ 'Power' ],
        'browserfling'                              : [ 'Power' ],
        'uibench'                                   : [ 'Power' ],
        'uibench_InflatingListActivity'             : [ 'Power' ],
        'uibench_TextCacheHighHitrateActivity'      : [ 'Power' ],
        'uibench_FullscreenOverdrawActivity'        : [ 'Power' ],
        'uibench_EditTextTypeActivity'              : [ 'Power' ],
        'uibench_TrivialRecyclerViewActivity'       : [ 'Power' ],
        'uibench_InvalidateActivity'                : [ 'Power' ],
        'uibench_DialogListActivity'                : [ 'Power' ],
        'uibench_ActivityTransition'                : [ 'Power' ],
        'uibench_TextCacheLowHitrateActivity'       : [ 'Power' ],
        'uibench_ScrollableWebViewActivity'         : [ 'Power' ],
        'uibench_BitmapUploadActivity'              : [ 'Power' ],
        'uibench_TrivialListActivity'               : [ 'Power' ],
        'uibench_SlowBindRecyclerViewActivity'      : [ 'Power' ],
        'uibench_TrivialAnimationActivity'          : [ 'Power' ],
        'uibench_GlTextureViewActivity'             : [ 'Power' ],
        'uibench_ActivityTransitionDetails'         : [ 'Power' ],
        'uibench_ShadowGridActivity'                : [ 'Power' ]
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
        'nenamark'     : [ 'nenamark score' ]
    }

    perf_interactive_scenarios = {
        'recentfling'  : [ 'Average Jank%' ],
        'galleryfling' : [ 'Average Jank%' ],
        'browserfling' : [ 'Average Jank%' ],
        'emailfling'   : [ 'Average Jank%' ],
        'uibench'                              : [ 'janks%' ],
        'uibench_InflatingListActivity'        : [ 'janks%' ],
        'uibench_TextCacheHighHitrateActivity' : [ 'janks%' ],
        'uibench_FullscreenOverdrawActivity'   : [ 'janks%' ],
        'uibench_EditTextTypeActivity'         : [ 'janks%' ],
        'uibench_TrivialRecyclerViewActivity'  : [ 'janks%' ],
        'uibench_InvalidateActivity'           : [ 'janks%' ],
        'uibench_DialogListActivity'           : [ 'janks%' ],
        'uibench_ActivityTransition'           : [ 'janks%' ],
        'uibench_TextCacheLowHitrateActivity'  : [ 'janks%' ],
        'uibench_ScrollableWebViewActivity'    : [ 'janks%' ],
        'uibench_BitmapUploadActivity'         : [ 'janks%' ],
        'uibench_TrivialListActivity'          : [ 'janks%' ],
        'uibench_SlowBindRecyclerViewActivity' : [ 'janks%' ],
        'uibench_TrivialAnimationActivity'     : [ 'janks%' ],
        'uibench_GlTextureViewActivity'        : [ 'janks%' ],
        'uibench_ActivityTransitionDetails'    : [ 'janks%' ],
        'uibench_ShadowGridActivity'           : [ 'janks%' ],
    }

    sched_scenarios = {
        'idle' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'audio' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'video' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'rt_app' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'hackbench' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'geekbench' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'linpack' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
         'quadrant' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
         'smartbench' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
         'nenamark' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ]
    }

    sched_interactive_scenarios = {
         'recentfling' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
           'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
           'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
           'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
           'sched_secb_nrg_sav', 'sched_secb_count',
           'sched_fbt_attempts', 'sched_fbt_no_cpu',
           'sched_fbt_no_sd', 'sched_fbt_pref_idle',
           'sched_fbt_count', 'sched_cas_attempts',
           'sched_tob', 'sched_tol' ],
         'galleryfling' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
           'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
           'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
           'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
           'sched_secb_nrg_sav', 'sched_secb_count',
           'sched_fbt_attempts', 'sched_fbt_no_cpu',
           'sched_fbt_no_sd', 'sched_fbt_pref_idle',
           'sched_fbt_count', 'sched_cas_attempts',
           'sched_tob', 'sched_tol' ],
         'browserfling' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
           'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
           'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
           'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
           'sched_secb_nrg_sav', 'sched_secb_count',
           'sched_fbt_attempts', 'sched_fbt_no_cpu',
           'sched_fbt_no_sd', 'sched_fbt_pref_idle',
           'sched_fbt_count', 'sched_cas_attempts',
           'sched_tob', 'sched_tol' ],
         'uibench' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
           'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
           'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
           'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
           'sched_secb_nrg_sav', 'sched_secb_count',
           'sched_fbt_attempts', 'sched_fbt_no_cpu',
           'sched_fbt_no_sd', 'sched_fbt_pref_idle',
           'sched_fbt_count', 'sched_cas_attempts',
           'sched_tob', 'sched_tol' ],
         'uibench_InflatingListActivity' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
           'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
           'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
           'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
           'sched_secb_nrg_sav', 'sched_secb_count',
           'sched_fbt_attempts', 'sched_fbt_no_cpu',
           'sched_fbt_no_sd', 'sched_fbt_pref_idle',
           'sched_fbt_count', 'sched_cas_attempts',
           'sched_tob', 'sched_tol' ],
         'uibench_TextCacheHighHitrateActivity' :
         [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
         'uibench_FullscreenOverdrawActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_EditTextTypeActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_TrivialRecyclerViewActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_InvalidateActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_DialogListActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_ActivityTransition' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_TextCacheLowHitrateActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_ScrollableWebViewActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_BitmapUploadActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_TrivialListActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_SlowBindRecyclerViewActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_TrivialAnimationActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_GlTextureViewActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_ActivityTransitionDetails' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
        'uibench_ShadowGridActivity' :
        [ 'sched_sis_attempts', 'sched_sis_idle', 'sched_sis_cache_affine',
          'sched_sis_suff_cap', 'sched_sis_idle_cpu', 'sched_sis_count',
          'sched_secb_attempts', 'sched_secb_sync', 'sched_secb_idle_bt',
          'sched_secb_insuff_cap', 'sched_secb_no_nrg_sav',
          'sched_secb_nrg_sav', 'sched_secb_count',
          'sched_fbt_attempts', 'sched_fbt_no_cpu',
          'sched_fbt_no_sd', 'sched_fbt_pref_idle',
          'sched_fbt_count', 'sched_cas_attempts',
          'sched_tob', 'sched_tol' ],
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

            if m is None:
                section = 'general_section'
            else:
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
        temp_f.write("set boxwidth 0.4 absolute\n")
        temp_f.write("set style fill solid 1.00 border lt -1\n")
        temp_f.write("set key outside right\n")
        temp_f.write("set style histogram clustered gap 1 title  offset character 0, 0, 0\n")
        temp_f.write("set datafile missing '-'\n")
        temp_f.write("set style data histograms\n")
        temp_f.write("set xtics rotate by -45\n")
        temp_f.write("set xtics ()\n")
        temp_f.write("set style line 1 lc rgb 'orange'\n")
        temp_f.write("set style line 2 lc rgb 'pink'\n")
        temp_f.write("set style line 3 lc rgb 'blue'\n")
        temp_f.write("set style line 4 lc rgb 'seagreen'\n")
        temp_f.write("set style line 5 lc rgb 'yellow'\n")
        temp_f.write("set style line 6 lc rgb 'green'\n")
        temp_f.write("set style line 7 lc rgb 'brown'\n")
        temp_f.write("set style line 8 lc rgb 'red'\n")
        temp_f.write("set style line 9 lc rgb 'cyan'\n")
        temp_f.write("plot for [i=2:"+str(sec_num)+"] filename using i:xtic(1) ti col ls i-1;\n")
        temp_f.write("set terminal wxt noenhanced font 'Ubuntu,9'\n")
        temp_f.close()

        outfile = os.path.join(self.outdir, comp_type + '_plot.txt')
        os.system('gnuplot -e "filename=\'' + outfile + '\''+'" /tmp/plot_template')

    def plot_schedstats_pie_chart(self, name):

        pic_file = os.path.join(self.outdir, name + '.png')

        temp_f = open('/tmp/plot_schedstats_pie_chart_template', "w+")
        temp_f.write("set terminal pngcairo noenhanced size 400,300 font 'Ubuntu,9'\n")
        temp_f.write("set output '"+ pic_file + "'\n")
        temp_f.write("set title " + "\"" + name + "\\n statistics (%)\"\n")
        #temp_f.write("filename = " + "'" + name + ".txt'\n")
        temp_f.write("rowi = 1\n")
        temp_f.write("rowf = 100\n")

        # obtain sum(column(2)) from rows `rowi` to `rowf`
        temp_f.write("set datafile separator ' '\n")
        temp_f.write("stats filename u 2 every ::rowi::rowf noout prefix \"A\"\n")

        # rowf should not be greater than length of file
        temp_f.write("rowf = (rowf-rowi > A_records - 1 ? A_records + rowi - 1 : rowf)\n")

        temp_f.write("angle(x)=x*360/A_sum\n")
        temp_f.write("percentage(x)=x*100/A_sum\n")

        # circumference dimensions for pie-chart
        temp_f.write("centerX=0\n")
        temp_f.write("centerY=0\n")
        temp_f.write("radius=0.3\n")

        # label positions
        temp_f.write("yposmin = 0.0\n")
        temp_f.write("yposmax = 0.95*radius\n")
        temp_f.write("xpos = 1.3*radius\n")
        temp_f.write("ypos(i) = yposmax - i*(yposmax-yposmin)/(1.0*rowf-rowi)\n")

        #-------------------------------------------------------------------
        # now we can configure the canvas
        temp_f.write("set style fill solid 1     # filled pie-chart\n")
        temp_f.write("unset key                  # no automatic labels\n")
        temp_f.write("unset tics                 # remove tics\n")
        temp_f.write("unset border               # remove borders; if some label is missing, comment to see what is happening\n")

        temp_f.write("set size ratio -1              # equal scale length\n")
        temp_f.write("set xrange [-radius:3*radius]  # [-1:2] leaves space for labels\n")
        temp_f.write("set yrange [-radius:radius]    # [-1:1]\n")

        #-------------------------------------------------------------------
        temp_f.write("pos = 0             # init angle\n")
        temp_f.write("colour = 0          # init colour\n")

        temp_f.write("set style line 1 lc rgb 'orange'\n")
        temp_f.write("set style line 2 lc rgb 'pink'\n")
        temp_f.write("set style line 3 lc rgb 'blue'\n")
        temp_f.write("set style line 4 lc rgb 'seagreen'\n")
        temp_f.write("set style line 5 lc rgb 'yellow'\n")
        temp_f.write("set style line 6 lc rgb 'green'\n")
        temp_f.write("set style line 7 lc rgb 'brown'\n")
        temp_f.write("set style line 8 lc rgb 'red'\n")
        temp_f.write("set style line 9 lc rgb 'cyan'\n")

        # 1st line: plot pie-chart
        # 2nd line: draw colored boxes at (xpos):(ypos)
        # 3rd line: place labels at (xpos+offset):(ypos)
        temp_f.write("plot filename u (centerX):(centerY):(radius):(pos):(pos=pos+angle($2)):(colour=colour+1) every ::rowi::rowf w circle lc var,\\\n")
        temp_f.write("    for [i=0:rowf-rowi] '+' u (xpos):(ypos(i)) w p pt 5 ps 4 lc i+1,\\\n")
        temp_f.write("    for [i=0:rowf-rowi] filename u (xpos):(ypos(i)):(sprintf('%05.2f%% %s', percentage($2), stringcolumn(1))) every ::i+rowi::i+rowi w labels left offset 3,0\n")
        temp_f.write("set terminal wxt noenhanced font 'Ubuntu,9'\n")
        temp_f.close()

        outfile = os.path.join(self.outdir, name + '.txt')
        os.system('gnuplot -e "filename=\'' + outfile + '\''+'" /tmp/plot_schedstats_pie_chart_template')

    def plot_schedstats_comparison(self, name):

        temp_f = open('/tmp/plot_schedstats_comparison_template', "w+")

        pic_file = os.path.join(self.outdir, name + '.png')

        temp_f.write("set terminal pngcairo noenhanced size 1280,600 font 'Ubuntu,10'\n")
        temp_f.write("set output '"+ pic_file + "'\n")
        temp_f.write("set multiplot layout 1,3 title \"Scheduler Statistics\\n\" font \',12\'\n")

        temp_f.write("set key spacing 1.1\n")
        temp_f.write("unset yrange\n")
        temp_f.write("set grid\n")

        temp_f.write("set xtics rotate by -45\n")
        temp_f.write("set xtics ()\n")
        temp_f.write("set style fill solid 1.00 border -1\n")
        temp_f.write("set boxwidth 0.4 absolute\n")
        temp_f.write("set key outside center top\n")

        temp_f.write("set style line 1 lc rgb 'orange'\n")
        temp_f.write("set style line 2 lc rgb 'pink'\n")
        temp_f.write("set style line 3 lc rgb 'blue'\n")
        temp_f.write("set style line 4 lc rgb 'seagreen'\n")
        temp_f.write("set style line 5 lc rgb 'yellow'\n")
        temp_f.write("set style line 6 lc rgb 'green'\n")
        temp_f.write("set style line 7 lc rgb 'brown'\n")
        temp_f.write("set style line 8 lc rgb 'red'\n")
        temp_f.write("set style line 9 lc rgb 'cyan'\n")

        temp_f.write("set style data histogram\n")
        temp_f.write("set style histogram rowstacked\n")

        temp_f.write("set title \"Waken balance path comparison\"\n")
        temp_f.write("set ylabel \"total\"\n")

        temp_f.write("plot filename using 2:xticlabels(1) ls 2 ti columnheader,  \\\n")
        temp_f.write("    '' using 3 ls 3 ti col, \\\n")
        temp_f.write("    '' using 4 ls 4 ti col\n")

        temp_f.write("set title \"Waken balance path comparison (%)\"\n")
        temp_f.write("set ylabel \"% of total\"\n")
        temp_f.write("set yrange [0:110]\n")

        temp_f.write("plot filename using (100*$2/($2+$3+$4)):xticlabels(1) ls 2 ti columnhead(2), \\\n")
        temp_f.write("    '' using (100*$3/($2+$3+$4)) ls 3 ti columnhead(3), \\\n")
        temp_f.write("    '' using (100*$4/($2+$3+$4)) ls 4 ti columnhead(4)\n")

        temp_f.write("set title \"Task placement in waken balance\\n(big vs LITTLE)\"\n")
        temp_f.write("set ylabel \"% of total\"\n")
        temp_f.write("set yrange [0:110]\n")

        temp_f.write("plot filename using (100*$20/($20+$21)):xticlabels(1) ls 2 ti columnhead(20), \\\n")
        temp_f.write("    '' using (100*$21/($20+$21)) ls 3 ti columnhead(21)\n")

        temp_f.close()

        outfile = os.path.join(self.outdir, name + '.txt')
        os.system('gnuplot -e "filename=\'' + outfile + '\''+'" /tmp/plot_schedstats_comparison_template')

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

                if m is not None:
                    section = m.group(1)
                else:
                    section = 'general_section'

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

    def parse_sched_scenarios(self, scenarios, comp_str):

        for s in scenarios:
            print s
            value = self.parse_scenario(s, scenarios)
            if bool(value) == False:
                continue

            print '\n'
            print value
            print '\n'

            outfile = os.path.join(self.outdir, comp_str + '_' + s + '.txt')
            self.fo = open(outfile, "w+")
            self.fo.write('section ')

            self.fo.write('secb_attempts ')
            self.fo.write('sis_attempts ')
            self.fo.write('cas_attempts ')

            self.fo.write('sis_idle ')
            self.fo.write('sis_cache_affine ')
            self.fo.write('sis_suff_cap ')
            self.fo.write('sis_idle_cpu ')
            self.fo.write('sis_count ')

            self.fo.write('secb_sync ')
            self.fo.write('secb_idle_bt ')
            self.fo.write('secb_insuff_cap ')
            self.fo.write('secb_no_nrg_sav ')
            self.fo.write('secb_nrg_sav ')
            self.fo.write('secb_count ')

            self.fo.write('fbt_no_cpu ')
            self.fo.write('fbt_no_sd ')
            self.fo.write('fbt_pref_idle ')
            self.fo.write('fbt_count ')

            self.fo.write('tasks_on_big_CPU ')
            self.fo.write('tasks_on_LITTLE_CPU\n')

            for kern in self.sections:
                self.fo.write(kern + ' ')

                stats_result = {}

                collectValue = value[kern]

                values = collectValue['sched_secb_attempts']
                stats_result['sched_secb_attempts'] = int(sum(values) / len(values))
                values = collectValue['sched_sis_attempts']
                stats_result['sched_sis_attempts'] = int(sum(values) / len(values))
                values = collectValue['sched_cas_attempts']
                stats_result['sched_cas_attempts'] = int(sum(values) / len(values))

                self.fo.write(' ' + str(stats_result['sched_secb_attempts']))
                self.fo.write(' ' + str(stats_result['sched_sis_attempts']))
                self.fo.write(' ' + str(stats_result['sched_cas_attempts']))

                values = collectValue['sched_sis_idle']
                stats_result['sched_sis_idle'] = int(sum(values) / len(values))
                values = collectValue['sched_sis_cache_affine']
                stats_result['sched_sis_cache_affine'] = int(sum(values) / len(values))
                values = collectValue['sched_sis_suff_cap']
                stats_result['sched_sis_suff_cap'] = int(sum(values) / len(values))
                values = collectValue['sched_sis_idle_cpu']
                stats_result['sched_sis_idle_cpu'] = int(sum(values) / len(values))
                values = collectValue['sched_sis_count']
                stats_result['sched_sis_count'] = int(sum(values) / len(values))

                self.fo.write(' ' + str(stats_result['sched_sis_idle']))
                self.fo.write(' ' + str(stats_result['sched_sis_cache_affine']))
                self.fo.write(' ' + str(stats_result['sched_sis_suff_cap']))
                self.fo.write(' ' + str(stats_result['sched_sis_idle_cpu']))
                self.fo.write(' ' + str(stats_result['sched_sis_count']))

                outfile = os.path.join(self.outdir, comp_str + '_' + kern + '_' + s + '_sis.txt')
                self.sis_fo = open(outfile, "w+")
                self.sis_fo.write('path count\n')
                self.sis_fo.write('sis_idle ')
                self.sis_fo.write(str(stats_result['sched_sis_idle']) + '\n')
                self.sis_fo.write('sis_cache_affine ')
                self.sis_fo.write(str(stats_result['sched_sis_cache_affine']) + '\n')
                self.sis_fo.write('sis_suff_cap ')
                self.sis_fo.write(str(stats_result['sched_sis_suff_cap']) + '\n')
                self.sis_fo.write('sis_idle_cpu ')
                self.sis_fo.write(str(stats_result['sched_sis_idle_cpu']) + '\n')
                self.sis_fo.write('sis_count ')
                self.sis_fo.write(str(stats_result['sched_sis_count']) + '\n')
                self.sis_fo.close()

                self.plot_schedstats_pie_chart(comp_str + '_' + kern + '_' + s + '_sis')

                values = collectValue['sched_secb_sync']
                stats_result['sched_secb_sync'] = int(sum(values) / len(values))
                values = collectValue['sched_secb_idle_bt']
                stats_result['sched_secb_idle_bt'] = int(sum(values) / len(values))
                values = collectValue['sched_secb_insuff_cap']
                stats_result['sched_secb_insuff_cap'] = int(sum(values) / len(values))
                values = collectValue['sched_secb_no_nrg_sav']
                stats_result['sched_secb_no_nrg_sav'] = int(sum(values) / len(values))
                values = collectValue['sched_secb_nrg_sav']
                stats_result['sched_secb_nrg_sav'] = int(sum(values) / len(values))
                values = collectValue['sched_secb_count']
                stats_result['sched_secb_count'] = int(sum(values) / len(values))

                self.fo.write(' ' + str(stats_result['sched_secb_sync']))
                self.fo.write(' ' + str(stats_result['sched_secb_idle_bt']))
                self.fo.write(' ' + str(stats_result['sched_secb_insuff_cap']))
                self.fo.write(' ' + str(stats_result['sched_secb_no_nrg_sav']))
                self.fo.write(' ' + str(stats_result['sched_secb_nrg_sav']))
                self.fo.write(' ' + str(stats_result['sched_secb_count']))

                outfile = os.path.join(self.outdir, comp_str + '_' + kern + '_' + s + '_secb.txt')
                self.secb_fo = open(outfile, "w+")
                self.secb_fo.write('path count\n')
                self.secb_fo.write('secb_sync ')
                self.secb_fo.write(str(stats_result['sched_secb_sync']) + '\n')
                self.secb_fo.write('secb_idle_bt ')
                self.secb_fo.write(str(stats_result['sched_secb_idle_bt']) + '\n')
                self.secb_fo.write('secb_insuff_cap ')
                self.secb_fo.write(str(stats_result['sched_secb_insuff_cap']) + '\n')
                self.secb_fo.write('secb_no_nrg_sav ')
                self.secb_fo.write(str(stats_result['sched_secb_no_nrg_sav']) + '\n')
                self.secb_fo.write('secb_nrg_sav ')
                self.secb_fo.write(str(stats_result['sched_secb_nrg_sav']) + '\n')
                self.secb_fo.write('secb_count ')
                self.secb_fo.write(str(stats_result['sched_secb_count']) + '\n')
                self.secb_fo.close()

                self.plot_schedstats_pie_chart(comp_str + '_' + kern + '_' + s + '_secb')

                values = collectValue['sched_fbt_no_cpu']
                stats_result['sched_fbt_no_cpu'] = int(sum(values) / len(values))
                values = collectValue['sched_fbt_no_sd']
                stats_result['sched_fbt_no_sd'] = int(sum(values) / len(values))
                values = collectValue['sched_fbt_pref_idle']
                stats_result['sched_fbt_pref_idle'] = int(sum(values) / len(values))
                values = collectValue['sched_fbt_count']
                stats_result['sched_fbt_count'] = int(sum(values) / len(values))

                self.fo.write(' ' + str(stats_result['sched_fbt_no_cpu']))
                self.fo.write(' ' + str(stats_result['sched_fbt_no_sd']))
                self.fo.write(' ' + str(stats_result['sched_fbt_pref_idle']))
                self.fo.write(' ' + str(stats_result['sched_fbt_count']))

                outfile = os.path.join(self.outdir, comp_str + '_' + kern + '_' + s + '_fbt.txt')
                self.fbt_fo = open(outfile, "w+")
                self.fbt_fo.write('path count\n')
                self.fbt_fo.write('fbt_no_cpu ')
                self.fbt_fo.write(str(stats_result['sched_fbt_no_cpu']) + '\n')
                self.fbt_fo.write('fbt_no_sd ')
                self.fbt_fo.write(str(stats_result['sched_fbt_no_sd']) + '\n')
                self.fbt_fo.write('fbt_pref_idle ')
                self.fbt_fo.write(str(stats_result['sched_fbt_pref_idle']) + '\n')
                self.fbt_fo.write('fbt_count ')
                self.fbt_fo.write(str(stats_result['sched_fbt_count']) + '\n')
                self.fbt_fo.close()

                self.plot_schedstats_pie_chart(comp_str + '_' + kern + '_' + s + '_fbt')

                values = collectValue['sched_tob']
                stats_result['sched_tob'] = int(sum(values) / len(values))
                values = collectValue['sched_tol']
                stats_result['sched_tol'] = int(sum(values) / len(values))

                self.fo.write(' ' + str(stats_result['sched_tob']))
                self.fo.write(' ' + str(stats_result['sched_tol']))

                self.fo.write('\n')

            self.fo.close()

            self.plot_schedstats_comparison(comp_str + '_' + s)

    def parse_power(self):
        self.parse_scenarios(self.power_scenarios, 'power')
        self.parse_scenarios(self.power_scenarios, 'power_delta', self.baseline)
        self.parse_scenarios(self.power_interactive_scenarios, 'power_interactive')
        self.parse_scenarios(self.power_interactive_scenarios, 'power_delta_interactive', self.baseline)

    def parse_perf(self):
        self.parse_scenarios(self.perf_scenarios, 'performance')
        self.parse_scenarios(self.perf_scenarios, 'performance_delta', self.baseline)
        self.parse_scenarios(self.perf_interactive_scenarios, 'performance_interactive')
        self.parse_scenarios(self.perf_interactive_scenarios, 'performance_delta_interactive', self.baseline)

    def parse_schedstats(self):
        self.parse_sched_scenarios(self.sched_scenarios, 'schedstats')
        self.parse_sched_scenarios(self.sched_interactive_scenarios, 'schedstats')

    def parse_file(self):
        self.sections = self.parse_sections()
        self.parse_power()
        self.parse_perf()
        self.parse_schedstats()

    def process_run_result(self, result, context):

        infile = os.path.join(context.run_output_directory, 'results.csv')
        self.logger.info('Status available in {}'.format(infile))

        if not os.path.isfile(infile):
            print "file don't exists:"
            return

        self.infile = infile
        self.outdir = context.run_output_directory
        self.parse_file()
