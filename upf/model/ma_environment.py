# Copyright 2021 AIPlan4EU project
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
'''This module defines the MultiAgentProblem class.'''

import upf
from upf.shortcuts import *

class ma_environment:
    def __init__(
            self,
            obs_fluents = None,
            actions = None,
    ):
        if obs_fluents is None:
            self.obs_fluents = []
        if actions is None:
            self.actions = []


    def add_fluent(self, Fluent):
        self.obs_fluents.append(Fluent)

    def get_fluent(self):
        return self.obs_fluents

    def add_actions(self, Action):
        self.actions.append(Action)

    def get_actions(self):
        return self.actions