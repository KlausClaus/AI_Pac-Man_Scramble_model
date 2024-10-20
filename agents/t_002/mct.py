# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from collections import deque

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'Agent1', second = 'Agent2'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

# max food eaten before returning
MAX_CAPACITY = 5

# max food eaten when eating capsule with MCT
MCT_MAX_CAPACITY = 10

# max distance from potential enemy (need escape)
ALERT_DISTANCE = 3

# capsule effective in 5 moves only
CAPSULE_EFFECT_REMAINING = 5

# MCT available execution time
MCT_EXECUTION_TIME = 0.9

# MCT epsilon for e-greedy algorithm
MCT_EPSILON = 0.5

# MCT discount factor
MCT_DISCOUNT_FACTOR = 0.9

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    '''
    Copied from baslineTeam.py
    '''
    self.carrying = 0
    self.current_target = None
    self.boundary = self.getBoundary(gameState)
    self.capsule_time = 0
    self.step_moved = 0


  def chooseAction(self, gameState):
    # step 1 determine a target
    agent_state = gameState.getAgentState(self.index)
    agent_pos = agent_state.getPosition()
    enemy_location_list = []
    max_space_away = 0
    temp_wall_boundary = [] # cannot cross a single wall block
    temp_wall_list = [] # cannot cross an area around enemy
    enemy_list = self.getOpponents(gameState)
    food_list = self.getFood(gameState).asList()
    capsule_list = self.getCapsules(gameState)
    self.step_moved += 1
    apply_MCT = False 
    
    # determine capsule remaining effect
    prior_game_state = self.getPreviousObservation()
    if prior_game_state != None:
      prior_capsule_list = self.getCapsules(prior_game_state)
      if capsule_list != None and capsule_list != []:
        if len(prior_capsule_list) > len(capsule_list):
          self.capsule_time = 40
        else:
          if self.capsule_time > 0:
            self.capsule_time -= 1
      else:
        capsule_list = []

    # agent is on own land as a ghost
    if not agent_state.isPacman:
      if not agent_pos in self.boundary: # not on boundary, no target
        for enemy_index in enemy_list: # check enemy ghost on own side
          enemy_state = gameState.getAgentState(enemy_index)
          enemy_pos = enemy_state.getPosition()
          if enemy_pos != None:
            if enemy_state.isPacman and agent_state.scaredTimer > 0: # meet ghost 
              if self.getMazeDistance(agent_pos, enemy_pos) <= ALERT_DISTANCE:
                enemy_location_list.append(enemy_pos)
                max_space_away = 2
        if self.current_target == None: 
          self.current_target = self.getClosestPos(gameState, self.boundary) # then go to boundary

      else: # on boundary
        for enemy_index in enemy_list: # check enemy ghost on other side
          enemy_state = gameState.getAgentState(enemy_index)
          enemy_pos = enemy_state.getPosition()
          if enemy_pos != None:
            if self.getMazeDistance(agent_pos, enemy_pos) <= ALERT_DISTANCE: # close
              if enemy_state.isPacman: # meet capsule-eating enemy 
                if agent_state.scaredTimer > 0: 
                    enemy_location_list.append(enemy_pos)
                    max_space_away = 2
              else: # meet ghost
                x_now, y_now = agent_pos
                if self.red:
                  x_now += 1
                else:
                  x_now -= 1
                temp_wall_boundary.append((x_now, y_now))

        if len(enemy_location_list) > 0: # ghost is close, change target
          boundary_set = set(self.boundary.copy())
          top_boundary = self.boundary[0]
          bottom_boundary = self.boundary[0]
          top_boundary_y = self.boundary[0][1]
          bottom_boundary_y = self.boundary[0][1]
          for item in boundary_set:
            now_boundary_y = item[1]
            if now_boundary_y > top_boundary_y:
              top_boundary = item
              top_boundary_y = now_boundary_y
            if now_boundary_y < bottom_boundary_y:
              bottom_boundary = item
              bottom_boundary_y = now_boundary_y
          potential_boundary_break_in = [top_boundary, bottom_boundary]
          if self.current_target == None:
            self.current_target = random.choice(potential_boundary_break_in)
          elif not self.current_target in potential_boundary_break_in:
              self.current_target = random.choice(potential_boundary_break_in)
            
        else: # no ghost, food/capsule becomes new target
          self.current_target = self.getClosestPos(gameState, food_list + capsule_list)    
    
    # agent is on enemy land as a pacman
    else:
      stay_with_capsule = True
      for enemy_index in enemy_list:
        enemy_state = gameState.getAgentState(enemy_index)
        enemy_pos = enemy_state.getPosition()
        if not enemy_state.isPacman and enemy_pos != None: # ghost is close
          if self.getMazeDistance(agent_pos, enemy_pos) <= ALERT_DISTANCE:
            if int(enemy_state.scaredTimer) == 0: # capsule ineffective, must hide
              enemy_location_list.append(enemy_pos)
              max_space_away = 2
            elif enemy_state.scaredTimer <= CAPSULE_EFFECT_REMAINING: # capsule will end, must return (change h)
              if self.carrying >= MAX_CAPACITY:
                stay_with_capsule = False

          else: # use MCT only when ghost is far from us
            if self.capsule_time > CAPSULE_EFFECT_REMAINING:
              apply_MCT = True 

      # use A* when ghost is close:     
      if not apply_MCT:
        if len(food_list) <= 2: # will win
          self.current_target = self.getClosestPos(gameState, self.boundary)
        else: # not win soon
          if self.capsule_time > 0: # eaten capsule
            if stay_with_capsule: # capsule lasts long (or expires with little food)
              if self.current_target == None: 
                self.current_target = self.getClosestPos(gameState, food_list)
            else: # capsule expire soon with many food
              self.current_target = self.getClosestPos(gameState, self.boundary + capsule_list)

          else: # no capsule consumed
            if self.carrying >= MAX_CAPACITY: # many food
              self.current_target = self.getClosestPos(gameState, self.boundary + capsule_list)
            else: # little food
              self.current_target = self.getClosestPos(gameState, food_list + capsule_list)            
    
    # step 2 model the problem, use a* to solve
    if not apply_MCT: # use A*
      temp_wall_list = self.createTempWall(gameState, enemy_location_list, max_space_away)
      problem = PositionSearchProblem(gameState, self.current_target, self.index, tempWall=temp_wall_list+temp_wall_boundary)
      path  = self.aStarSearch(problem)
    else: # use MCT
      mct_action = self.monte_carlo_tree_search(gameState)
      path = [mct_action]

    # step 3 choose action, update status
    # step 3.1 if no path is found, then stop (no status update)
    '''
    Copied from baslineTeam.py
    '''
    if path == []: 
      actions = gameState.getLegalActions(self.index)
      action_picked = random.choice(actions)
      # avoid go to enemy
      if (agent_state.isPacman and len(enemy_location_list) > 0) or ((not agent_state.isPacman) and agent_state.scaredTimer > 0):
        dx_temp,dy_temp = game.Actions.directionToVector(action_picked) 
        x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
        while (x_temp, y_temp) in temp_wall_list and len(actions) > 1:
          actions.remove(action_picked)
          action_picked = random.choice(actions)
          dx_temp,dy_temp = game.Actions.directionToVector(action_picked)
          x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
        if len(actions) == 0:
          action_picked = Directions.STOP
      return action_picked
    
    # step 3.2 if found a path, then find next position + update status
    else: 
      action = path[0]
      dx,dy = game.Actions.directionToVector(action)
      x,y = gameState.getAgentState(self.index).getPosition()
      new_x,new_y = int(x+dx),int(y+dy)
      
      if (new_x,new_y) == self.current_target: # update target reached, food reached/deposited
        self.current_target = None
      if self.getFood(gameState)[new_x][new_y]:
        self.carrying +=1
      elif (new_x,new_y) in self.boundary:
        self.carrying = 0
      return path[0]

  def getClosestPos(self,gameState,pos_list):
    '''
    Copied from baslineTeam.py
    '''
    min_length = 9999
    min_pos = None
    my_local_state = gameState.getAgentState(self.index)
    my_pos = my_local_state.getPosition()
    for pos in pos_list:
      temp_length = self.getMazeDistance(my_pos,pos)
      if temp_length < min_length:
        min_length = temp_length
        min_pos = pos
    return min_pos
  
  def getBoundary(self,gameState):
    '''
    Copied from baslineTeam.py
    '''
    boundary_location = []
    height = gameState.data.layout.height
    width = gameState.data.layout.width
    for i in range(height):
      if self.red:
        j = int(width/2)-1
      else:
        j = int(width/2)
      if not gameState.hasWall(j,i):
        boundary_location.append((j,i))
    return boundary_location
  
  def createTempWall(self, gameState, enemy_location_list=[], max_distance=0):
    '''
    created temporary walls to be far from enemy
    '''
    maze_matrix = gameState.getWalls().copy()
    maze_width = maze_matrix.width
    maze_height = maze_matrix.height
    
    for x_enemy, y_enemy in enemy_location_list:
      for x_coordinate in range(maze_width):
        for y_coordinate in range(maze_height):
          if not maze_matrix[x_coordinate][y_coordinate]:
            if self.getMazeDistance((x_coordinate, y_coordinate), (x_enemy, y_enemy)) <= max_distance:
              maze_matrix[x_coordinate][y_coordinate] = True

    wall_list = maze_matrix.asList()
    return wall_list


  def aStarSearch(self, problem):
    '''
    Copied from baslineTeam.py
    '''
    from util import PriorityQueue
    myPQ = util.PriorityQueue()
    startState = problem.getStartState()
    # print(f"start states {startState}")
    startNode = (startState, '',0, [])
    heuristic = problem._manhattanDistance
    myPQ.push(startNode,heuristic(startState))
    visited = set()
    best_g = dict()
    while not myPQ.isEmpty():
        node = myPQ.pop()
        state, action, cost, path = node
        # print(cost)
        # print(f"visited list is {visited}")
        # print(f"best_g list is {best_g}")
        if (not state in visited) or cost < best_g.get(str(state)):
            visited.add(state)
            best_g[str(state)]=cost
            if problem.isGoalState(state):
                path = path + [(state, action)]
                actions = [action[1] for action in path]
                del actions[0]
                return actions
            for succ in problem.getSuccessors(state):
                succState, succAction, succCost = succ
                newNode = (succState, succAction, cost + succCost, path + [(node, action)])
                myPQ.push(newNode,heuristic(succState)+cost+succCost)
    return []
  
  def monte_carlo_tree_search(self, gameState): # return a list of single action, or []
    start_execution_time = time.time()
    available_actions = gameState.getLegalActions(self.index)
    available_actions.remove(Directions.STOP)
    game_score_before_mct = self.getScore(gameState) # if new score increase, then stop mct

    mct_chosen_action = random.choice(available_actions) # in case time is up before MCT finishes iteration
    mct_iterations_count = 0 # count number of iterating over MCT
    mct_root_node = "I" # starting point of MCT
    mct_expanded_branch_list = dict() # check whether node is fullly expanded (key = action sequence, value = all the expanded actions object)
    mct_best_branch = dict() # store the best actions sequence for expanded node (key = action sequence, value = best actions object)
    mct_value_record = dict() # stores the discounted value for simulation of MCT (key = action sequence, value = simulated, discounted values)
    mct_node_backprop_count = dict() # stores the number of visiting same node in backprop of MCT (key = action sequence, value = #times visited)
    
    def convert_direction_to_string(direction):
      """converts a direction to a one-character string, used for expression of node in MCT dictionary

      parameter
      -----------------
      direction = a given Directions object

      return
      ------------
      direction_string = a string representing a direction
      """
      if direction == Directions.NORTH:
        return 'N'
      elif direction == Directions.SOUTH:
        return 'S'
      elif direction == Directions.WEST:
        return 'W'
      elif direction == Directions.EAST:
        return 'E'
      else: # all other directions such as STOP, LEFT, RIGHT, not used in MCT
        return '-'

    def convert_string_to_direction(direction_string):
      """converts a direction string to a directions object, used for checking duplicate moves

      parameter
      -----------------
      direction_string = a given one-character string representing a direction

      return
      ------------
      direction = a Directions object given the string expression
      """
      if direction_string == 'N':
        return Directions.NORTH
      elif direction_string == 'S':
        return Directions.SOUTH
      elif direction_string == 'W':
        return Directions.WEST
      elif direction_string == 'E':
        return Directions.EAST
      else:
        return Directions.STOP

    def check_node_branch_fully_expanded(parent_node, branch_list):
      """check whether an MCT parent node has been fully expanded (i.e. all branches are explored)
      
      parameter
      -----------------
      parent_node = a given node of MCT representing a sequence of past actions e.g. "NSWE"
      branch_list = a list of branches that can be expanded from parent node, representing all the possible next actions
                    e.g. [Directions.NORTH, Directions.SOUTH]

      return
      ------------
      unexplored_branch = a list of branches (i.e. next actions) not expanded before, that follows from the parent node
      """
      unexplored_branch = []

      # avoid duplicate
      if parent_node in mct_expanded_branch_list:
        last_move_string = parent_node[-1]
        if last_move_string != "I":
          last_move_direction = convert_string_to_direction(last_move_string)
          reverse_last_move = Directions.REVERSE(last_move_direction)

        for branch in branch_list:
          # remove immediate reverse action (i.e. go back from last position)
          if branch != reverse_last_move:
            branch_string = convert_direction_to_string(branch)
            new_child_node = parent_node + branch_string

            # save child node if never expanded
            if not new_child_node in mct_expanded_branch_list:
              unexplored_branch.append(branch)
        
        return unexplored_branch

      # if never expand parent node
      else:
        unexplored_branch = branch_list 
      
      return unexplored_branch

    # run MCT only when time is sufficient
    while time.time() - start_execution_time >= MCT_EXECUTION_TIME:
      mct_iterations_count += 1
      mct_e_greedy_queue = deque([]) # queue to record all nodes (i.e. action sequence, possible next action object)
      simulation_reward = 0
      mct_current_node = mct_root_node
      next_available_actions = available_actions
      
      current_game_state = gameState.deepCopy()
      mct_stopping_criteria = self.getScore(current_game_state) - game_score_before_mct 

      # 1. MCT: no need to select a new node unless the parent node is fully expanded, sufficient time, and score is low
      while len(check_node_branch_fully_expanded(mct_current_node, next_available_actions)) == 0 and mct_stopping_criteria < MCT_MAX_CAPACITY:
        
        # no time for MCT, then return best action so far
        if time.time() - start_execution_time >= MCT_EXECUTION_TIME:
          #print("stop select at iteration=", mct_iterations_count)  
          return mct_chosen_action
          
        # has time for MCT, exploit with prob of 1-epsilon; otherwise, explore
        random_number = random.uniform(0, 1)
        if random_number < 1 - MCT_EPSILON: # exploit if chosen with 1-e prob, and has stored best action
          if mct_current_node in mct_best_branch:
            mct_current_branch = mct_best_branch[mct_current_node]
          else: # chosen with 1-e prob, but never stored best action
            mct_current_branch = random.choice(next_available_actions)
        else: # chosen outside 1-e
          mct_current_branch = random.choice(next_available_actions)

        # after MCT selection, update the new MCT node, queue, next game state, next available actions for new node
        mct_current_branch_string = convert_direction_to_string(mct_current_branch)
        mct_current_node = mct_current_node + mct_current_branch_string
        mct_e_greedy_queue.append((mct_current_node, mct_current_branch))
        current_game_state = self.getSuccessorGivenAction(current_game_state, mct_current_branch)
        next_available_actions = current_game_state.getLegalActions(self.index)
        next_available_actions.remove(Directions.STOP)

      # 2. MCT expand a random non-expanded child node
      child_available_actions = check_node_branch_fully_expanded(mct_current_node, next_available_actions)
      if len(child_available_actions) == 0:
        continue # go to next round of MCT iteration

      else: # choose a random child node
        mct_current_branch = random.choice(child_available_actions)

        # update/add the new child node to the expanded node dictionary (record the best action sequence)
        past_expanded_actions = []
        if mct_current_node in mct_expanded_branch_list:
          past_expanded_actions = mct_expanded_branch_list[mct_current_node] # already ensured no duplicate move
          past_expanded_actions.append(mct_current_branch)
        else:
          mct_expanded_branch_list[mct_current_node] = [mct_current_branch]

        # after MCT expansion, update the new MCT node, queue, next game state, next available actions for new node
        mct_current_branch_string = convert_direction_to_string(mct_current_branch)
        mct_current_node = mct_current_node + mct_current_branch_string
        mct_e_greedy_queue.append((mct_current_node, mct_current_branch))
        current_game_state = self.getSuccessorGivenAction(current_game_state, mct_current_branch)
        next_available_actions = current_game_state.getLegalActions(self.index)
        next_available_actions.remove(Directions.STOP)

      # 3. MCT simulate the child node till reached a satisfactory result
      mct_stopping_criteria = self.getScore(gameState) - game_score_before_mct
      simulation_count = 0

      while mct_stopping_criteria < MCT_MAX_CAPACITY:
        # simulate a further step only if time is sufficient
        simulation_count += 1
        if time.time() - start_execution_time >= MCT_EXECUTION_TIME:
          #print("stop simulate at iteration=", mct_iterations_count)  
          #print(mct_chosen_action)
          return mct_chosen_action
        
        # simulate by choosing a random action
        else:
          # remove the duplicate reversal movement
          #last_move = convert_string_to_direction(mct_current_node[-1])
          #reverse_last_move = Directions.REVERSE[last_move]
          #if reverse_last_move in next_available_actions:
          #  next_available_actions.remove(reverse_last_move)
          
          if len(next_available_actions) == 0:
            continue # break the while loop to calculate reward 
          else:
            mct_simulate_branch = random.choice(next_available_actions)

          # for each simulation, update the new MCT node, queue, next game state, next available actions for new node
          mct_simulate_branch_string = convert_direction_to_string(mct_simulate_branch)
          mct_current_node = mct_current_node + mct_simulate_branch_string
          mct_e_greedy_queue.append((mct_current_node, mct_simulate_branch))
          current_game_state = self.getSuccessorGivenAction(current_game_state, mct_simulate_branch)
          next_available_actions = current_game_state.getLegalActions(self.index)

      simulation_reward = self.getScore(gameState) - game_score_before_mct

      # 4. MCT backpropagate the Q value from child node to root node
      mct_node_value = simulation_reward * (MCT_DISCOUNT_FACTOR ** simulation_count)
      while len(mct_e_greedy_queue) > 0:
        if time.time() - start_execution_time < MCT_EXECUTION_TIME:
          continue
        else:
          queue_item = mct_e_greedy_queue.pop()
          child_node = queue_item[0]
          next_action = queue_item[1]

          # update value and node dictionary, if the node can be found with higher reward than existing value
          if child_node in mct_value_record:
            existing_value = mct_value_record[child_node]
            if mct_node_value > existing_value: # update to reflect best reward
              mct_value_record[child_node] = mct_node_value   
              mct_node_backprop_count[child_node] += 1
              mct_best_branch[child_node] = next_action
            else:
              mct_node_backprop_count[child_node] += 1

          # create new record if this node is never saved in dictionary
          else:
            mct_value_record[child_node] = mct_node_value
            mct_node_backprop_count[child_node] = 1
            mct_best_branch[child_node] = next_action

          mct_node_value = mct_node_value * MCT_DISCOUNT_FACTOR
      
      if mct_root_node in mct_best_branch:
        #print(mct_best_branch[mct_root_node])
        mct_chosen_action = mct_best_branch[mct_root_node]
        #print("found root at iteration=", mct_iterations_count)
    
    return mct_chosen_action  

  def getSuccessorGivenAction(self, gameState, action):
    """Gets the new game state after taking an action in a given game state
    parameter
    -----------------
    gameState = a given game state describing the game environment
    action = a given action
    
    return
    ------------
    next_game_state = the new game state 
    """
    x_temp, y_temp = gameState.getAgentPosition(self.index)
    dx_temp, dy_temp = game.Actions.directionToVector(action)
    x_temp, y_temp = int(x_temp + dx_temp), int(y_temp + dy_temp)
    if gameState.hasWall(x_temp, y_temp):
      return None
    new_game_state = gameState.generateSuccessor(self.index, action)
    new_location = new_game_state.getAgentState(self.index).getPosition()
    if new_location != util.nearestPoint(new_location):
      new_game_state = new_game_state.generateSuccessor(self.index, action)
  
    return new_game_state


class PositionSearchProblem:
    '''
    Copied from baslineTeam.py
    '''
    def __init__(self, gameState, goal, agentIndex = 0, costFn = lambda x: 1, tempWall=[]):
        self.walls = gameState.getWalls().copy() 
        self.costFn = costFn
        x,y = gameState.getAgentState(agentIndex).getPosition()
        self.startState = int(x),int(y)
        self.goal_pos = goal

        # convert any space close to enemy into a wall
        for blocked_path in tempWall:
           x_coordinate = int(blocked_path[0])
           y_coordinate = int(blocked_path[1])
           self.walls[x_coordinate][y_coordinate] = True

    def getStartState(self):
      return self.startState

    def isGoalState(self, state):
      return state == self.goal_pos
    
    # modify to include STOP action
    def getSuccessors(self, state):
        successors = []
        for action in [game.Directions.NORTH, game.Directions.SOUTH, game.Directions.EAST, game.Directions.WEST, game.Directions.STOP]:
            x,y = state
            dx, dy = game.Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append( ( nextState, action, cost) )
        return successors     
    
    def getCostOfActions(self, actions):
        if actions == None: return 999999
        x,y= self.getStartState()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = game.Actions.directionToVector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.costFn((x,y))
        return cost
    
    def _manhattanDistance(self,pos):
      return util.manhattanDistance(pos,self.goal_pos)


class Agent1(DummyAgent):
  pass

class Agent2(DummyAgent):
  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    self.carrying = 0
    self.current_target = None
    self.boundary = self.getBoundary(gameState)
  
  def chooseAction(self, gameState):
    # step 1 determine a target
    agent_state = gameState.getAgentState(self.index)
    agent_pos = agent_state.getPosition()
    enemy_location_list = []
    max_space_away = 0
    temp_wall_boundary = [] # cannot cross a single wall block
    temp_wall_list = [] # cannot cross an area around enemy
    enemy_list = self.getOpponents(gameState)
    enemy_chase_list = []
    enemy_food_list = self.getFoodYouAreDefending(gameState).asList()
    enemy_capsule_list = self.getCapsulesYouAreDefending(gameState)
 
    # cannot go to enemy land
    agent_boundary = self.boundary
    if self.red:
      for item in agent_boundary:
        x_bound, y_bound = item
        x_bound += 1
        temp_wall_boundary.append((x_bound, y_bound))
    else:
      for item in agent_boundary:
        x_bound, y_bound = item
        x_bound -= 1
        temp_wall_boundary.append((x_bound, y_bound))
    
    # locate enemy
    find_enemy = False
    for enemy_index in enemy_list:
      enemy_state = gameState.getAgentState(enemy_index)
      enemy_pos = enemy_state.getPosition()
      if enemy_state.isPacman:
        find_enemy = True
        if enemy_pos != None:
          enemy_chase_list.append(enemy_pos)
    
    # locate potential enemy from eaten food/capsule
    prior_game_state = self.getPreviousObservation()
    if prior_game_state != None:
      prior_food_list = self.getFoodYouAreDefending(prior_game_state).asList()
      prior_capsule_list = self.getCapsulesYouAreDefending(prior_game_state)
      if len(prior_food_list) + len(prior_capsule_list) > len(enemy_food_list) + len(enemy_capsule_list):
        find_enemy = True
        potential_enemy_set = (set(prior_food_list).union(set(prior_capsule_list))).intersection(set(enemy_food_list).union(set(enemy_capsule_list))) 
        for item in potential_enemy_set:
          enemy_chase_list.append(item)
    
    # choose target
    if find_enemy:
      if len(enemy_chase_list) > 0: # can locate enemy
        if int(agent_state.scaredTimer) == 0: # enemy didn't eat capsule
          self.current_target = self.getClosestPos(gameState, enemy_chase_list)

        else: # enemy eats capsule
          enemy_location_list = enemy_chase_list.copy()
          max_space_away = 2
          x_enemy_near, y_enemy_near = self.getClosestPos(gameState, enemy_chase_list)
          find_new_target = False
          maze_height = gameState.data.layout.height
          maze_width = gameState.data.layout.width
          # 3 steps away from nearest enemy
          for x in range(-ALERT_DISTANCE, ALERT_DISTANCE+1):
            for y in range(-ALERT_DISTANCE, ALERT_DISTANCE+1):
              x_temp = int(x_enemy_near + x)
              y_temp = int(y_enemy_near + y)
              temp_target = (x_temp, y_temp)
              if (x_temp >= 0 and x_temp < maze_width) and (y_temp>= 0 and y_temp < maze_height):
                if not gameState.hasWall(x_temp, y_temp):
                  if self.getMazeDistance(temp_target, (x_enemy_near, y_enemy_near)) >= ALERT_DISTANCE:
                    self.current_target = temp_target
                    find_new_target = True
                    break
          if not find_new_target:
            self.current_target = self.getClosestPos(gameState, self.boundary)

      else: # cannot locate enemy, go nearest food/capsule/boundary
        if self.current_target == None:
          self.current_target = random.choice((enemy_food_list+enemy_capsule_list)+self.boundary)
    else: # no enemy
      if self.current_target == None:
        initial_pos = gameState.getInitialAgentPosition(enemy_list[0])
        initial_x = int(initial_pos[0])
        initial_y = int(initial_pos[1])
        initial_pos = (initial_x, initial_y)
        min_distance = 99999
        best_boundary = (0, 0)
        for item in self.boundary:
          current_distance = self.getMazeDistance(initial_pos, item)
          if current_distance < min_distance:
            min_distance = current_distance
            best_boundary = item
        self.current_target = best_boundary    
    
    # step 2 model the problem, use a* to solve
    temp_wall_list = self.createTempWall(gameState, enemy_location_list, max_space_away)
    problem = PositionSearchProblem(gameState, self.current_target, self.index, tempWall=temp_wall_list+temp_wall_boundary)
    path  = self.aStarSearch(problem)

    '''
    Copied from baslineTeam.py
    '''
    if path == []: 
      actions = gameState.getLegalActions(self.index) # returns a list of actions
      action_picked = random.choice(actions) 
      # cannot go to enemy side
      if agent_pos in self.boundary:
        if self.red:
          while action_picked == Directions.EAST:
            actions.remove(action_picked)
            action_picked = random.choice(actions)
        else: # blue team
          while action_picked == Directions.WEST:
            actions.remove(action_picked)
            action_picked = random.choice(actions)  
      return action_picked
    
    # step 3.2 if found a path, then find next position + update status
    else: 
      action = path[0]
      dx,dy = game.Actions.directionToVector(action)
      x,y = gameState.getAgentState(self.index).getPosition()
      new_x,new_y = int(x+dx),int(y+dy)
      
      if (new_x,new_y) == self.current_target: # update target reached, food reached/deposited
        self.current_target = None
      if self.getFood(gameState)[new_x][new_y]:
        self.carrying +=1
      elif (new_x,new_y) in self.boundary:
        self.carrying = 0
      return path[0]
