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

import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.environment import get_env
from upf.test.examples import get_example_problems



class TestPyperplan(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.env = get_env()
        self.problems = get_example_problems()
        self.env.factory.add_solver('pyperplan', 'upf_pyperplan', 'SolverImpl')

    def test_pyperplan(self):
        problem, plan = self.problems['robot_no_negative_preconditions'].problem, self.problems['robot_no_negative_preconditions'].plan
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))

    def test_pyperplan_2(self):
        problem, plan = self.problems['basic_pyperplan_test'].problem, self.problems['basic_pyperplan_test'].plan
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))
