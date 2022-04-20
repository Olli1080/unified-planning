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
# limitations under the License.


import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple
from unified_planning.model.agent import Agent
from unified_planning.model.ma_problem import MultiAgentProblem
from realistic import get_example_problems
from unified_planning.model.environment_ma import Environment_ma

from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.io.pddl_writer_ma import PDDLWriter_MA
from unified_planning.io.pddl_reader import PDDLReader
from unified_planning.transformers import NegativeConditionsRemover


Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
examples = get_example_problems()

def ma_example():
    problem = examples['depot'].problem

    # examples['...'].problem supported:
    # Yes: robot                                 PDDL:Yes
    # Yes: robot_fluent_of_user_type             PDDL:No (PDDL supports only boolean and numerical fluents)
    # Yes: robot_no_negative_preconditions       PDDL:Yes    OneShotPlanner:Yes
    # Yes: robot_decrease                        PDDL:Yes
    # Yes: robot_loader                          PDDL:Yes
    # Yes: robot_loader_mod                      PDDL:Yes
    # Yes: robot_loader_adv                      PDDL:Ye
    # Yes: robot_locations_connected             PDDL:Yes
    # Yes: robot_locations_visited               PDDL:Yes
    # Yes: charge_discharge                      PDDL:Yes
    # No: matchcellar
    # No: timed_connected_locations

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment_ma()

    '''print(fluents_problem, init_values_problem, "weeeeeeeeeeeeeeee",init_values_problem.keys())
    cargo_flu = fluents_problem[1]
    #cargo_flu2 = fluents_problem[2]
    key = 'cargo_at(l1)'
    if key in init_values_problem.keys():
        init_flu = init_values_problem[key]
    else:
        init_flu = None

    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l1)':
            print(i[1])
            init_flu_key = i[1][0]
            init_flu_value = i[1][1]
    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l2)':
            print(i[1])
            init_flu_key2 = i[1][0]
            init_flu_value2 = i[1][1]
    print(init_flu_key, cargo_flu)
    environment.add_fluent(cargo_flu)
    #environment.add_fluent(cargo_flu2)
    environment.set_initial_value(init_flu_key, init_flu_value)
    environment.set_initial_value(init_flu_key2, init_flu_value2)
    print(environment.get_initial_values(), environment.get_fluents())'''


    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('robots')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_environment_(environment)
    ma_problem.add_objects(objects_problem)
    #problem = ma_problem.compile()
    problem = ma_problem.compile_ma()
    print(problem)

    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan, "\n")
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    #w = PDDLWriter(problem)
    #print(w.get_domain())
    #print(w.get_problem())

    w = PDDLWriter_MA(problem)
    print(w.get_domain())
    print(w.get_problem())

    #ma_problem.pddl_writer()


    #KeyError di Location ("Usertype")
    #with OneshotPlanner(name='tamer') as planner:
    #    solve_plan = planner.solve(problem)
    #    print("Pyperplan returned: %s" % solve_plan)

    #unified_planning.exceptions.UPExpressionDefinitionError: Expression: (not (l_from == l_to)) is not in NNF.
    #npr = NegativeConditionsRemover(problem)
    #positive_problem = npr.get_rewritten_problem()
    #print("positive_problem", positive_problem)



#ma_example()


def ma_example_2():
    problem = examples['depot'].problem

    # examples['...'].problem supported:
    # Yes: robot                                 PDDL:Yes
    # Yes: robot_fluent_of_user_type             PDDL:No (PDDL supports only boolean and numerical fluents)
    # Yes: robot_no_negative_preconditions       PDDL:Yes    OneShotPlanner:Yes
    # Yes: robot_decrease                        PDDL:Yes
    # Yes: robot_loader                          PDDL:Yes
    # Yes: robot_loader_mod                      PDDL:Yes
    # Yes: robot_loader_adv                      PDDL:Ye
    # Yes: robot_locations_connected             PDDL:Yes
    # Yes: robot_locations_visited               PDDL:Yes
    # Yes: charge_discharge                      PDDL:Yes
    # No: matchcellar
    # No: timed_connected_locations

    fluents_problem = problem.fluents()
    actions_problem = problem.actions()
    init_values_problem = problem.initial_values()
    goals_problem = problem.goals()
    objects_problem = problem.all_objects()
    plan = examples['robot'].plan
    robot1 = Agent()
    robot2 = Agent()
    environment = Environment_ma()

    '''print(fluents_problem, init_values_problem, "weeeeeeeeeeeeeeee",init_values_problem.keys())
    cargo_flu = fluents_problem[1]
    #cargo_flu2 = fluents_problem[2]
    key = 'cargo_at(l1)'
    if key in init_values_problem.keys():
        init_flu = init_values_problem[key]
    else:
        init_flu = None

    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l1)':
            print(i[1])
            init_flu_key = i[1][0]
            init_flu_value = i[1][1]
    for i in enumerate(init_values_problem.items()):
        if str(i[1][0]) == 'cargo_at(l2)':
            print(i[1])
            init_flu_key2 = i[1][0]
            init_flu_value2 = i[1][1]
    print(init_flu_key, cargo_flu)
    environment.add_fluent(cargo_flu)
    #environment.add_fluent(cargo_flu2)
    environment.set_initial_value(init_flu_key, init_flu_value)
    environment.set_initial_value(init_flu_key2, init_flu_value2)
    print(environment.get_initial_values(), environment.get_fluents())'''

    robot1.add_fluents(fluents_problem)
    robot2.add_fluents(fluents_problem)
    robot1.add_actions(actions_problem)
    robot2.add_actions(actions_problem)
    robot1.set_initial_values(init_values_problem)
    robot2.set_initial_values(init_values_problem)
    robot1.add_goals(goals_problem)
    robot2.add_goals(goals_problem)

    ma_problem = MultiAgentProblem('robots')
    ma_problem.add_agent(robot1)
    ma_problem.add_agent(robot2)
    ma_problem.add_environment_(environment)
    ma_problem.add_objects(objects_problem)







    #Add shared data
    #problem = ma_problem.compile()
    problem = ma_problem.compile_ma('truck')
    print(ma_problem.fluents())
    ma_problem.add_shared_data(ma_problem.fluent('clear'))
    ma_problem.add_shared_data(ma_problem.fluent('clear_s'))
    ma_problem.add_shared_data(ma_problem.fluent('at'))
    ma_problem.add_shared_data(ma_problem.fluent('pos'))
    ma_problem.add_shared_data(ma_problem.fluent('pos_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on'))
    ma_problem.add_shared_data(ma_problem.fluent('on_u'))
    ma_problem.add_shared_data(ma_problem.fluent('on_s'))


    #Add fucntions
    ma_problem.add_flu_function(ma_problem.fluent('located'))
    ma_problem.add_flu_function(ma_problem.fluent('at'))
    ma_problem.add_flu_function(ma_problem.fluent('placed'))
    ma_problem.add_flu_function(ma_problem.fluent('pos'))
    ma_problem.add_flu_function(ma_problem.fluent('pos_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on'))
    ma_problem.add_flu_function(ma_problem.fluent('on_u'))
    ma_problem.add_flu_function(ma_problem.fluent('on_s'))

    print(problem)

    print("Single agent plan:\n ", plan)
    plan = ma_problem.extract_plans(plan)
    print("Multi agent plan:\n ", plan, "\n")
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    w = PDDLWriter_MA(problem)
    print(w.get_domain())
    print(w.get_problem())

ma_example_2()