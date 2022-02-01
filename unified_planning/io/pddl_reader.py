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

import unified_planning
import typing
from unified_planning.environment import Environment, get_env
from pyparsing import Word, alphanums, alphas, ZeroOrMore, OneOrMore # type: ignore
from pyparsing import Optional, one_of, Suppress, nestedExpr, Group, restOfLine # type: ignore
from pyparsing.results import ParseResults # type: ignore
from collections import OrderedDict
from fractions import Fraction
from typing import Dict, Union, Callable, List


class PDDLGrammar:
    def __init__(self):
        name = Word(alphas, alphanums+'_'+'-')
        variable = Suppress('?') + name

        require_def = Suppress('(') + ':requirements' + \
            OneOrMore(one_of(':strips :typing :negative-preconditions :disjunctive-preconditions :equality :existential-preconditions :universal-preconditions :quantified-preconditions :conditional-effects :fluents :numeric-fluents :adl :durative-actions :duration-inequalities :timed-initial-literals')) \
            + Suppress(')')

        types_def = Suppress('(') + ':types' + \
            OneOrMore(Group(Group(OneOrMore(name)) + \
                            Optional(Suppress('-') + name))).setResultsName('types') \
                            + Suppress(')')

        constants_def = Suppress('(') + ':constants' + \
            OneOrMore(Group(Group(OneOrMore(name)) + \
                            Optional(Suppress('-') + name))).setResultsName('constants') \
                            + Suppress(')')

        predicate = Suppress('(') + \
            Group(name + Group(ZeroOrMore(Group(Group(OneOrMore(variable)) + \
                                                Optional(Suppress('-') + name))))) \
                                                + Suppress(')')

        predicates_def = Suppress('(') + ':predicates' + \
            Group(OneOrMore(predicate)).setResultsName('predicates') \
            + Suppress(')')

        functions_def = Suppress('(') + ':functions' + \
            Group(OneOrMore(predicate)).setResultsName('functions') \
            + Suppress(')')

        parameters = ZeroOrMore(Group(Group(OneOrMore(variable)) \
                                     + Optional(Suppress('-') + name))).setResultsName('params')
        action_def = Group(Suppress('(') + ':action' + name.setResultsName('name') \
                           + ':parameters' + Suppress('(') + parameters + Suppress(')') \
                           + Optional(':precondition' + nestedExpr().setResultsName('pre')) \
                           + Optional(':effect' + nestedExpr().setResultsName('eff')) \
                           + Suppress(')'))

        dur_action_def = Group(Suppress('(') + ':durative-action' + name.setResultsName('name') \
                               + ':parameters' + Suppress('(') + parameters + Suppress(')') \
                               + ':duration' + nestedExpr().setResultsName('duration') \
                               + ':condition' + nestedExpr().setResultsName('cond') \
                               + ':effect' + nestedExpr().setResultsName('eff') \
                               + Suppress(')'))

        domain = Suppress('(') + 'define' \
            + Suppress('(') + 'domain' + name.setResultsName('name') + Suppress(')') \
            + Optional(require_def) + Optional(types_def) + Optional(constants_def) \
            + Optional(predicates_def) + Optional(functions_def) \
            + Group(ZeroOrMore(action_def | dur_action_def)).setResultsName('actions') + Suppress(')')

        objects = OneOrMore(Group(Group(OneOrMore(name)) \
                                  + Optional(Suppress('-') + name))).setResultsName('objects')
        problem = Suppress('(') + 'define' \
            + Suppress('(') + 'problem' + name.setResultsName('name') + Suppress(')') \
            + Suppress('(') + ':domain' + name + Suppress(')') + Optional(require_def) \
            + Optional(Suppress('(') + ':objects' + objects + Suppress(')')) \
            + Suppress('(') + ':init' + ZeroOrMore(nestedExpr()).setResultsName('init') + Suppress(')') \
            + Suppress('(') + ':goal' + nestedExpr().setResultsName('goal') + Suppress(')') \
            + Suppress(')')

        domain.ignore(';' + restOfLine)
        problem.ignore(';' + restOfLine)

        self._domain = domain
        self._problem = problem
        self._parameters = parameters

    @property
    def domain(self):
        return self._domain

    @property
    def problem(self):
        return self._problem

    @property
    def parameters(self):
        return self._parameters
      

class PDDLReader:
    """
    Parse a PDDL problem and generate a unified_planning problem.
    """
    def __init__(self, env: Environment = None):
        self._env = get_env(env)
        self._em = self._env.expression_manager
        self._tm = self._env.type_manager
        self._operators: Dict[str, Callable] = {
            'and' : self._em.And,
            'or' : self._em.Or,
            'not' : self._em.Not,
            'imply' : self._em.Implies,
            '>=' : self._em.GE,
            '<=' : self._em.LE,
            '>' : self._em.GT,
            '<' : self._em.LT,
            '=' : self._em.Equals,
            '+' : self._em.Plus,
            '-' : self._em.Minus,
            '/' : self._em.Div,
            '*' : self._em.Times
        }
        grammar = PDDLGrammar()
        self._pp_domain = grammar.domain
        self._pp_problem = grammar.problem
        self._pp_parameters = grammar.parameters

    def _parse_exp(self, problem: unified_planning.model.Problem, act: typing.Optional[unified_planning.model.Action],
                   var: Dict[str, unified_planning.model.Variable], exp: Union[ParseResults, str]) -> unified_planning.model.FNode:
        stack = [(var, exp, False)]
        solved: List[unified_planning.model.FNode] = []
        while len(stack) > 0:
            var, exp, status = stack.pop()
            if status:
                if exp[0] == '-' and len(exp) == 2: # unary minus
                    solved.append(self._em.Times(-1, solved.pop()))
                elif exp[0] in self._operators: # n-ary operators
                    op: Callable = self._operators[exp[0]]
                    solved.append(op(*[solved.pop() for _ in exp[1:]]))
                elif exp[0] in ['exists', 'forall']: # quantifier operators
                    q_op: Callable = self._em.Exists if exp[0] == 'exists' else self._em.Forall
                    solved.append(q_op(solved.pop(), *var.values()))
                elif problem.has_fluent(exp[0]): # fluent reference
                    f = problem.fluent(exp[0])
                    args = [solved.pop() for _ in exp[1:]]
                    solved.append(self._em.FluentExp(f, tuple(args)))
                else:
                    raise unified_planning.exceptions.UPUnreachableCodeError
            else:
                if isinstance(exp, ParseResults):
                    if len(exp) == 0: # empty precodition
                        solved.append(self._em.TRUE())
                    elif exp[0] == '-' and len(exp) == 2: # unary minus
                        stack.append((var, exp, True))
                        stack.append((var, exp[1], False))
                    elif exp[0] in self._operators: # n-ary operators
                        stack.append((var, exp, True))
                        for e in exp[1:]:
                            stack.append((var, e, False))
                    elif exp[0] in ['exists', 'forall']: # quantifier operators
                        vars_string = ' '.join(exp[1])
                        vars_res = self._pp_parameters.parseString(vars_string)
                        vars = {}
                        for g in vars_res['params']:
                            t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                            for o in g[0]:
                                vars[o] = unified_planning.model.Variable(o, t)
                        stack.append((vars, exp, True))
                        stack.append((vars, exp[2], False))
                    elif problem.has_fluent(exp[0]): # fluent reference
                        stack.append((var, exp, True))
                        for e in exp[1:]:
                            stack.append((var, e, False))
                    elif len(exp) == 1: # expand an element inside brackets
                        stack.append((var, exp[0], False))
                    else:
                        raise SyntaxError(f'Not able to handle: {exp}')
                elif isinstance(exp, str):
                    if exp[0] == '?' and exp[1:] in var: # variable in a quantifier expression
                        solved.append(self._em.VariableExp(var[exp[1:]]))
                    elif exp[0] == '?': # action parameter
                        assert act is not None
                        solved.append(self._em.ParameterExp(act.parameter(exp[1:])))
                    elif problem.has_fluent(exp): # fluent
                        solved.append(self._em.FluentExp(problem.fluent(exp)))
                    elif problem.has_object(exp): # object
                        solved.append(self._em.ObjectExp(problem.object(exp)))
                    else: # number
                        n = Fraction(exp)
                        if n.denominator == 1:
                            solved.append(self._em.Int(n.numerator))
                        else:
                            solved.append(self._em.Real(n))
                else:
                    raise SyntaxError(f'Not able to handle: {exp}')
        assert len(solved) == 1 #sanity check
        return solved.pop()

    def _add_effect(self, problem: unified_planning.model.Problem,
                    act: Union[unified_planning.model.InstantaneousAction, unified_planning.model.DurativeAction],
                    exp: Union[ParseResults, str],
                    cond: Union[unified_planning.model.FNode, bool] = True,
                    timing: typing.Optional[unified_planning.model.Timing] = None):
        to_add = [(exp, cond)]
        while to_add:
            exp, cond = to_add.pop(0)
            op = exp[0]
            if op == 'and':
                exp = exp[1:]
                for e in exp:
                    to_add.append((e, cond))
            elif op == 'when':
                cond = self._parse_exp(problem, act, {}, exp[1])
                to_add.append((exp[2], cond))
            elif op == 'not':
                exp = exp[1]
                eff = (self._parse_exp(problem, act, {}, exp), self._em.FALSE(), cond)
                act.add_effect(*eff if timing is None else (timing, *eff)) # type: ignore
            elif op == 'assign':
                eff = (self._parse_exp(problem, act, {}, exp[1]),
                       self._parse_exp(problem, act, {}, exp[2]), cond)
                act.add_effect(*eff if timing is None else (timing, *eff)) # type: ignore
            elif op == 'increase':
                eff = (self._parse_exp(problem, act, {}, exp[1]),
                       self._parse_exp(problem, act, {}, exp[2]), cond)
                act.add_increase_effect(*eff if timing is None else (timing, *eff)) # type: ignore
            elif op == 'decrease':
                eff = (self._parse_exp(problem, act, {}, exp[1]),
                       self._parse_exp(problem, act, {}, exp[2]), cond)
                act.add_decrease_effect(*eff if timing is None else (timing, *eff)) # type: ignore
            else:
                eff = (self._parse_exp(problem, act, {}, exp), self._em.TRUE(), cond)
                act.add_effect(*eff if timing is None else (timing, *eff)) # type: ignore

    def _add_condition(self, problem: unified_planning.model.Problem, act: unified_planning.model.DurativeAction,
                       exp: Union[ParseResults, str],
                       vars: typing.Optional[Dict[str, unified_planning.model.Variable]] = None):
        to_add = [(exp, vars)]
        while to_add:
            exp, vars = to_add.pop(0)
            op = exp[0]
            if op == 'and':
                for e in exp[1:]:
                    to_add.append((e, vars))
            elif op == 'forall':
                vars_string = ' '.join(exp[1])
                vars_res = self._pp_parameters.parseString(vars_string)
                if vars is None:
                    vars = {}
                for g in vars_res['params']:
                    t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                    for o in g[0]:
                        vars[o] = unified_planning.model.Variable(o, t)
                to_add.append((exp[2], vars))
            elif len(exp) == 3 and op == 'at' and exp[1] == 'start':
                cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_condition(unified_planning.model.StartTiming(), cond)
            elif len(exp) == 3 and op == 'at' and exp[1] == 'end':
                cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_condition(unified_planning.model.EndTiming(), cond)
            elif len(exp) == 3 and op == 'over' and exp[1] == 'all':
                t_all = unified_planning.model.OpenInterval(unified_planning.model.StartTiming(), unified_planning.model.EndTiming())
                cond = self._parse_exp(problem, act, {} if vars is None else vars, exp[2])
                if vars is not None:
                    cond = self._em.Forall(cond, *vars.values())
                act.add_durative_condition(t_all, cond)
            else:
                raise SyntaxError(f'Not able to handle: {exp}')

    def _add_timed_effects(self, problem: unified_planning.model.Problem,
                           act: unified_planning.model.DurativeAction,
                           eff: ParseResults):
        to_add = [eff]
        while to_add:
            eff = to_add.pop(0)
            op = eff[0]
            if op == 'and':
                for e in eff[1:]:
                    to_add.append(e)
            elif len(eff) == 3 and op == 'at' and eff[1] == 'start':
                self._add_effect(problem, act, eff[2], timing=unified_planning.model.StartTiming())
            elif len(eff) == 3 and op == 'at' and eff[1] == 'end':
                self._add_effect(problem, act, eff[2], timing=unified_planning.model.EndTiming())
            else:
                raise SyntaxError(f'Not able to handle: {eff}')


    def parse_problem(self, domain_filename: str,
                      problem_filename: typing.Optional[str] = None) -> 'unified_planning.model.Problem':
        domain_res = self._pp_domain.parseFile(domain_filename)

        problem = unified_planning.model.Problem(domain_res['name'], self._env,
                                    initial_defaults={self._tm.BoolType(): self._em.FALSE()})

        for p in domain_res.get('predicates', []):
            n = p[0]
            params = []
            for g in p[1]:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                params.extend([t for i in range(len(g[0]))])
            f = unified_planning.model.Fluent(n, self._tm.BoolType(), params, self._env)
            problem.add_fluent(f)

        for p in domain_res.get('functions', []):
            n = p[0]
            params = []
            for g in p[1]:
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                params.extend([t for i in range(len(g[0]))])
            f = unified_planning.model.Fluent(n, self._tm.RealType(), params, self._env)
            problem.add_fluent(f)

        for g in domain_res.get('constants', []):
            t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
            for o in g[0]:
                problem.add_object(unified_planning.model.Object(o, t))

        for a in domain_res.get('actions', []):
            n = a['name']
            a_params = OrderedDict()
            for g in a.get('params', []):
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for p in g[0]:
                    a_params[p] = t
            if 'duration' in a:
                dur_act = unified_planning.model.DurativeAction(n, a_params, self._env)
                dur = a['duration'][0]
                if dur[0] == '=':
                    dur_act.set_fixed_duration(self._parse_exp(problem, dur_act,
                                                               {}, dur[2]))
                elif dur[0] == 'and':
                    upper = None
                    lower = None
                    for j in range(1, len(dur)):
                        v = Fraction(dur[j][2])
                        if dur[j][0] == '>=':
                            if lower is None or v > lower:
                                lower = v
                        elif dur[j][0] == '<=':
                            if upper is None or v < upper:
                                upper = v
                        else:
                            raise SyntaxError(f'Not able to handle duration constraint of action {n}')
                    if lower is None or upper is None:
                        raise SyntaxError(f'Not able to handle duration constraint of action {n}')
                    d = unified_planning.model.ClosedIntervalDuration(self._em.Real(lower),
                                                         self._em.Real(upper))
                    dur_act.set_duration_constraint(d)
                else:
                    raise SyntaxError(f'Not able to handle duration constraint of action {n}')
                cond = a['cond'][0]
                self._add_condition(problem, dur_act, cond)
                eff = a['eff'][0]
                self._add_timed_effects(problem, dur_act, eff)
                problem.add_action(dur_act)
            else:
                act = unified_planning.model.InstantaneousAction(n, a_params, self._env)
                if 'pre' in a:
                    act.add_precondition(self._parse_exp(problem, act, {}, a['pre'][0]))
                if 'eff' in a:
                    self._add_effect(problem, act, a['eff'][0])
                problem.add_action(act)

        if problem_filename is not None:
            problem_res = self._pp_problem.parseFile(problem_filename)

            problem.name = problem_res['name']

            for g in problem_res.get('objects', []):
                t = self._tm.UserType(g[1] if len(g) > 1 else 'object')
                for o in g[0]:
                    problem.add_object(unified_planning.model.Object(o, t))

            for i in problem_res.get('init', []):
                if i[0] == '=':
                    problem.set_initial_value(self._parse_exp(problem, None, {}, i[1]),
                                              self._parse_exp(problem, None, {}, i[2]))
                elif len(i) == 3 and i[0] == 'at' and i[1].replace('.','',1).isdigit():
                    ti = unified_planning.model.StartTiming(Fraction(i[1]))
                    va = self._parse_exp(problem, None, {}, i[2])
                    if va.is_fluent_exp():
                        problem.add_timed_effect(ti, va, self._em.TRUE())
                    elif va.is_not():
                        problem.add_timed_effect(ti, va.arg(0), self._em.FALSE())
                    elif va.is_equals():
                        problem.add_timed_effect(ti, va.arg(0), va.arg(1))
                    else:
                        raise SyntaxError(f'Not able to handle this TIL {i}')
                else:
                    problem.set_initial_value(self._parse_exp(problem, None, {}, i), self._em.TRUE())

            problem.add_goal(self._parse_exp(problem, None, {}, problem_res['goal'][0]))

        return problem
