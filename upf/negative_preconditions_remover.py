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
"""This module defines the negative preconditions remover class."""

from collections import OrderedDict
from upf.fluent import Fluent
from upf.plan import SequentialPlan, ActionInstance
from upf.problem import Problem
from upf.action import Action
from upf.fnode import FNode
from upf.walkers.identitydag import IdentityDagWalker
from upf.exceptions import UPFExpressionDefinitionError, UPFProblemDefinitionError
from typing import List, Dict

class NegativeFluentRemover(IdentityDagWalker):
    def __init__(self, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env)
        self._fluent_mapping: Dict[Fluent, Fluent] = {}

    def remove_negative_fluents(self, expression:FNode) -> FNode:
        return self.walk(expression)

    def walk_not(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 1
        if not args[0].is_fluent_exp():
            raise UPFExpressionDefinitionError(f"Expression: {expression} is not in NNF.")
        neg_fluent = self._fluent_mapping.get(args[0].fluent(), None)
        if neg_fluent is not None:
            return self._env.expression_manager.FluentExp(neg_fluent, tuple(args[0].args()))
        f = args[0].fluent()
        nf = Fluent(f.name()+"__negated__", f.type(), f.signature(), f._env)
        self._fluent_mapping[f] = nf
        return self._env.expression_manager.FluentExp(nf, tuple(args[0].args()))


class NegativePreconditionsRemover():
    '''Negative preconditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with negative preconditions into one
    without negative preconditions.

    This is done by substituting every fluent that appears with a Not into the preconditions
    with different fluent representing  his negation.'''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._env = problem.env
        self._positive_problem = None
        self._count = 0
        #NOTE no simplification are made. But it's possible to add them in key points
        self._fluent_remover = NegativeFluentRemover(self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every ngeative fluent into action preconditions or overall
        goal is replaced by the fluent representing his negative.'''
        if self._positive_problem is not None:
            return self._positive_problem
        #NOTE that a different environment might be needed when multy-threading
        new_problem = self._create_problem_copy_without_fluents_actions_init_and_goals()
        self._modify_actions_and_goals(new_problem)
        self._positive_problem = new_problem
        return new_problem

    def _modify_actions_and_goals(self, new_problem):
        name_action_map: Dict[str, Action] = {}

        for name, action in self._problem.actions().items():
            new_action = Action(name, OrderedDict((ap.name(), ap.type()) for ap in action.parameters()), self._env)
            for p in action.preconditions():
                np = self._fluent_remover.remove_negative_fluents(p)
                new_action.add_precondition(np)
            name_action_map[name] = new_action

        for g in self._problem.goals():
            ng = self._fluent_remover.remove_negative_fluents(g)
            new_problem.add_goal(ng)

        fluent_mapping = self._fluent_remover._fluent_mapping
        for f in self._problem.fluents().values():
            new_problem.add_fluent(f)
            fneg = fluent_mapping.get(f, None)
            if fneg is not None:
                new_problem.add_fluent(fneg)

        for fl, v in self._problem.initial_values().items():
            fneg = fluent_mapping.get(fl.fluent(), None)
            if v.is_bool_constant():
                new_problem.set_initial_value(fl, v)
                if fneg is not None:
                    if v.bool_constant_value():
                        new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                        tuple(fl.args())), self._env.expression_manager.FALSE())
                    else:
                        new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                        tuple(fl.args())), self._env.expression_manager.TRUE())
            else:
                raise UPFProblemDefinitionError(f"Initial value: {v} of fluent: {fl} is not a boolean constant. An initial value MUST be a Boolean constant.")

        for name, action in self._problem.actions().items():
            new_action = name_action_map[name]
            for e in action.effects():
                if e.is_conditional():
                    raise UPFProblemDefinitionError(f"Effect: {e} of action: {action} is conditional. Try using the ConditionalEffectsRemover before the NegativePreconditionsRemover.")
                fl, v = e.fluent(), e.value()
                fneg = fluent_mapping.get(fl.fluent(), None)
                if v.is_bool_constant():
                    new_action.add_effect(fl, v)
                    if fneg is not None:
                        if v.bool_constant_value():
                            new_action.add_effect(self._env.expression_manager.FluentExp(fneg,
                            tuple(fl.args())), self._env.expression_manager.FALSE())
                        else:
                            new_action.add_effect(self._env.expression_manager.FluentExp(fneg,
                            tuple(fl.args())), self._env.expression_manager.TRUE())
                else:
                    raise UPFProblemDefinitionError(f"Effect; {e} assigns value: {v} to fluent: {fl}, but value is not a boolean constant.")
            new_problem.add_action(new_action)

    def _create_problem_copy_without_fluents_actions_init_and_goals(self):
        '''Creates the shallow copy of a problem, without adding the actions
        with quantifiers and by pushing them to the stack
        '''
        new_problem: Problem = Problem("no_negative_preconditions_" + str(self._problem.name()), self._env)
        for o in self._problem.all_objects():
            new_problem.add_object(o)
        return new_problem

    def rewrite_back_plan(self, unquantified_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        quantified_actions = [ActionInstance(self._problem.action(ai.action().name()), ai.actual_parameters()) for ai in unquantified_sequential_plan.actions()]
        return SequentialPlan(quantified_actions)
