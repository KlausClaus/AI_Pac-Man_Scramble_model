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
import copy

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'Agent3', second = 'Agent4'):
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

# max distance from potential enemy (need escape)
ALERT_DISTANCE = 3

# capsule effective in 5 moves only
CAPSULE_EFFECT_REMAINING = 5

# max steps taken before setting the same boundary as target
MAX_REPEAT_STEPS_OF_BOUNDARY = 10

# capsule remaining time before coming back to defend
BACK_TO_DEFEND_COUNTDOWN = 5

# best distance to keep away from enemy
SAFE_DISTANCE_FROM_POWER_ENEMY = 3

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
    self.carrying = 0 # food to carry (not deposited yet)
    self.total_food = len(self.getFood(gameState).asList())
    self.current_target = None # next goal destination 
    self.boundary = self.getBoundary(gameState) # boundary to cross and enter enemy land
    self.capsule_time = 0 # time that remained after eating capsule
    self.maze_walls = gameState.data.layout.walls
    self.maze_matrix = gameState.getWalls().copy() # walls of map
    self.maze_width = self.maze_matrix.width
    self.maze_height = self.maze_matrix.height
    self.boundary_target_dict = dict() # stores in which move a given boundary has been set as a target
    self.agent_steps_taken = 0 # records the number of moves that agent has walked
    if self.red:
     self.my_narrow_path_list, self.enemy_narrow_path_list, self.dead_end_list = self.precalculate_narrow_path(gameState) # stores a list of narrow path that leads to dead-end
    else:
      self.enemy_narrow_path_list, self.my_narrow_path_list, self.dead_end_list = self.precalculate_narrow_path(gameState)
    self.easy_food_area, self.hard_food_area = self.calculate_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)
    self.deposit_easy_food = False
    self.enemy_boundary = self.getEnemyBoundary(gameState)
    self.enemy_list = self.getOpponents(gameState)
    self.current_ghost_count = len(self.enemy_list)
    self.previous_ghost_count = 0
    print(self.enemy_boundary)
    

  def precalculate_narrow_path(self, gameState):
    """ finds out the location of cells with one-way narrow path
    """
    red_narrow_path_list = []
    blue_narrow_path_list = []
    dead_end_list = []
    
    closed = set()
    for x in range(1, self.maze_width - 1):
      for y in range(1, self.maze_height - 1):
        left = x-1
        right = x+1
        top = y+1
        bottom = y-1
        solution = ""
        # check whether (x, y) are vertical narrow paths
        if self.maze_walls[left][y] and self.maze_walls[right][y] and (not self.maze_walls[x][top]) and (not self.maze_walls[x][bottom]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(x, top, x, bottom, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))

        # check whether (x, y) are horizontal narrow paths
        elif self.maze_walls[x][top] and self.maze_walls[x][bottom] and (not self.maze_walls[left][y]) and (not self.maze_walls[right][y]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(left, y, right, y, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))

        # check whether turning point are narrow paths: go up, turn right
        elif self.maze_walls[left][y] and self.maze_walls[x][top] and (not self.maze_walls[x][bottom]) and (not self.maze_walls[right][y]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(x, bottom, right, y, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))
        
        # check whether turning point are narrow paths: go up, turn left
        elif self.maze_walls[right][y] and self.maze_walls[x][top] and (not self.maze_walls[x][bottom]) and (not self.maze_walls[left][y]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(x, bottom, left, y, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))

        # check whether turning point are narrow paths: go down, turn right
        elif self.maze_walls[left][y] and self.maze_walls[x][bottom] and (not self.maze_walls[x][top]) and (not self.maze_walls[right][y]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(x, top, right, y, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))

        # check whether turning point are narrow paths: go down, turn left
        elif self.maze_walls[right][y] and self.maze_walls[x][bottom] and (not self.maze_walls[x][top]) and (not self.maze_walls[left][y]) and not self.maze_walls[x][y]:
          self.maze_walls[x][y] = True
          solution = self.breathFirstSearch(x, top, left, y, x, y, closed, gameState)
          self.maze_walls[x][y] = False
          if solution == "Null":
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))
            closed.add((x, y))

        # find dead-end
        if gameState.hasWall(x, top) and gameState.hasWall(x, bottom) and gameState.hasWall(left, y) and not gameState.hasWall(right, y) and not gameState.hasWall(x, y): 
          dead_end_list.append((x, y))
          closed.add((x, y))
        elif gameState.hasWall(x, top) and gameState.hasWall(x, bottom) and gameState.hasWall(right, y) and not gameState.hasWall(left, y) and not gameState.hasWall(x, y):
          dead_end_list.append((x, y))
          closed.add((x, y))
        elif gameState.hasWall(left, y) and gameState.hasWall(x, bottom) and gameState.hasWall(right, y) and not gameState.hasWall(x, top) and not gameState.hasWall(x, y):
          dead_end_list.append((x, y))
          closed.add((x, y))
        elif gameState.hasWall(x, top) and gameState.hasWall(right, y) and gameState.hasWall(left, y) and not gameState.hasWall(x, bottom) and not gameState.hasWall(x, y):
          dead_end_list.append((x, y))
          closed.add((x, y))
    
    for x in range(1, self.maze_width - 1):
      for y in range(1, self.maze_height - 1):
        left = (x-1, y)
        right = (x+1, y)
        top = (x, y+1)
        bottom = (x, y-1)
        is_valid = True
        if not (x, y) in closed and not gameState.hasWall(x, y):
          for item in [left, right, top, bottom]:
            new_x = item[0]
            new_y = item[1]
            if 0 <= new_x and new_x < self.maze_width and 0 <= new_y and new_y < self.maze_height and not gameState.hasWall(new_x, new_y):
              if not (new_x, new_y) in closed:
                is_valid = False
                break
          if is_valid:
            closed.add((x, y))
            if x < self.maze_width / 2:
              red_narrow_path_list.append((x, y))
            else:
              blue_narrow_path_list.append((x, y))


    return (red_narrow_path_list, blue_narrow_path_list, dead_end_list)
 

  def calculate_food_difficulty(self, gameState, narrow_path_list, dead_end_list):
    '''separates food into two types: inside narrow path, or outside narrow path
    '''
    easy_food_list = []
    hard_food_list = []
    for food in self.getFood(gameState).asList():
      if food in narrow_path_list + dead_end_list:
        hard_food_list.append(food)
      else:
        easy_food_list.append(food)
    return (easy_food_list, hard_food_list)

  def breathFirstSearch(self, initial_x, initial_y, goal_x, goal_y, closed_x, closed_y, closed_set, gameState):
    '''Use breadth first search to find a path from initial location to goal
    '''
    walls = gameState.getWalls().asList().copy()
    closed_set = closed_set.copy().union(set(walls))
    solution = ""
    bfs_queue = util.Queue()
    state = (initial_x, initial_y, ((initial_x, initial_y),)) # i.e. (x, y) and path leading to current location
    x = initial_x
    y = initial_y
    has_visited = set(walls)
    has_visited.add((closed_x, closed_y))
    next_direction_value = ((0, -1), (0, 1), (-1, 0), (1, 0))
    next_direction_string = ('N', 'S', 'W', 'E')

    while (state[0], state[1]) != (goal_x, goal_y):
      if not ((state[0], state[1])) in has_visited:
        has_visited.add((state[0],state[1]))
        x = state[0]
        y = state[1]
        # find successor
        for index, dxy in enumerate(next_direction_value):
          new_x = x + dxy[0]
          new_y = y + dxy[1]
          name = next_direction_string[index]
          if 0 <= new_x and new_x < self.maze_width and 0 <= new_y and new_y < self.maze_height:
            if self.maze_walls[new_x][new_y]:
              closed_set.add((new_x, new_y))
            else:
              if not (new_x, new_y, name) in has_visited:
                child_state = (new_x, new_y)
                if not child_state in has_visited and not child_state in closed_set:
                  bfs_queue.push(child_state)
          
      if bfs_queue.isEmpty():
        solution = "Null"
        break
      
      node = bfs_queue.pop()
      state = (node[0], node[1])
      solution = "Found"
    return solution


  def chooseAction(self, gameState):
    # step 1 determine a target
    agent_state = gameState.getAgentState(self.index)
    agent_pos = agent_state.getPosition()
    agent_x = int(agent_pos[0])
    agent_y = int(agent_pos[1])
    agent_pos = (agent_x, agent_y)
    enemy_location_list = []
    max_space_away = 0
    temp_wall_boundary = [] # cannot cross a single wall block
    temp_wall_list = [] # cannot cross an area around enemy
    food_list = self.getFood(gameState).asList()
    capsule_list = self.getCapsules(gameState)
    self.agent_steps_taken += 1
    self.easy_food_area, self.hard_food_area = self.calculate_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)

    # determine capsule remaining effect
    prior_game_state = self.getPreviousObservation()
    if prior_game_state != None:
      prior_capsule_list = self.getCapsules(prior_game_state)
      if capsule_list != []:
        if len(prior_capsule_list) > len(capsule_list):
          self.capsule_time = 40
        else:
          if self.capsule_time > 0:
            self.capsule_time -= 1
      else:
        capsule_list = []

    # agent is on own land as a ghost
    if not agent_state.isPacman:
      if not agent_pos in self.boundary: # not on boundary

        defend_list = [] # check non-wall cells nearby
        eat_enemy_list = []
        for x in [-1, 0, 1]:
          for y in [-1, 0, 1]:
            if x == 0 and y == 0:
              continue
            nearby = (agent_pos[0] + x, agent_pos[1] + y)
            new_x = int(nearby[0])
            new_y = int(nearby[1])
            if new_x > 0 and new_y > 0 and new_x < self.maze_width and new_y < self.maze_height:
              if not gameState.hasWall(new_x, new_y):
                defend_list.append(nearby)

        for enemy_index in self.enemy_list: # check enemy ghost on own side
          enemy_state = gameState.getAgentState(enemy_index)
          enemy_pos = enemy_state.getPosition()
          if enemy_pos != None:
            if enemy_pos in defend_list:
              eat_enemy_list.append(enemy_pos)
            if enemy_state.isPacman and agent_state.scaredTimer > 0: # meet ghost 
              if self.getMazeDistance(agent_pos, enemy_pos) <= ALERT_DISTANCE:
                enemy_location_list.append(enemy_pos)
                max_space_away = 2

        # eat enemy if it's around
        if eat_enemy_list != []:
          previous_target = self.current_target
          min_maze_dist = 9999
          nearest = None
          for item in eat_enemy_list:
            dist = self.getMazeDistance(agent_pos, item)
            if dist < min_maze_dist:
              min_maze_dist = dist
              nearest = item
          if min_maze_dist == 1:
            self.current_target = nearest
          elif min_maze_dist == 2 and previous_target != None:
            found = False
            for item in defend_list:
              if self.getMazeDistance(nearest, item) == 2:
                self.current_target = item
                found = True
                break
            if not found:
              self.current_target = previous_target  
          elif min_maze_dist > 2 and previous_target != None:
            self.current_target = previous_target

          else:
            if previous_target == None: # take exactly same action as if "no enemy around for eat" scenario
              possible_target = self.getClosestPos(gameState, self.boundary) # then go to boundary
              target_x = int(possible_target[0])
              target_y = int(possible_target[1])
              possible_target = (target_x, target_y)
              boundary_target_last_step = self.boundary_target_dict.get((x, y), -1)

              # avoid setting to same boundary as target repeatedly
              if boundary_target_last_step == -1 or self.agent_steps_taken - boundary_target_last_step > MAX_REPEAT_STEPS_OF_BOUNDARY:
                self.current_target = possible_target
              else:
                boundary_set = self.boundary.copy()
                if possible_target in boundary_set and len(boundary_set) >= 2:
                  boundary_set.remove(possible_target)
                  possible_target = self.getClosestPos(gameState, boundary_set)
                  self.current_target = possible_target
                else: # only has 1 boundary
                  self.current_target = possible_target
              self.boundary_target_dict[possible_target] = self.agent_steps_taken
        else: # no enemy around for eat
          if self.current_target == None: 
            possible_target = self.getClosestPos(gameState, self.boundary) # then go to boundary
            target_x = int(possible_target[0])
            target_y = int(possible_target[1])
            possible_target = (target_x, target_y)
            boundary_target_last_step = self.boundary_target_dict.get(possible_target, -1)

            # avoid setting to same boundary as target repeatedly
            if boundary_target_last_step == -1 or self.agent_steps_taken - boundary_target_last_step > MAX_REPEAT_STEPS_OF_BOUNDARY:
              self.current_target = possible_target
            else:
              boundary_set = self.boundary.copy()
              if possible_target in boundary_set and len(boundary_set) >= 2:
                boundary_set.remove(possible_target)
                possible_target = self.getClosestPos(gameState, boundary_set)
                self.current_target = possible_target
              else: # only has 1 boundary
                self.current_target = possible_target
            self.boundary_target_dict[possible_target] = self.agent_steps_taken

      else: # agent is on boundary
        for enemy_index in self.enemy_list: # check enemy ghost on other side
          enemy_state = gameState.getAgentState(enemy_index)
          enemy_pos = enemy_state.getPosition()
          if enemy_pos != None:
            if self.getMazeDistance(agent_pos, enemy_pos) <= ALERT_DISTANCE: # close
              if enemy_state.isPacman: # meet capsule-eating enemy 
                if agent_state.scaredTimer > 0: 
                    enemy_location_list.append(enemy_pos)
                    max_space_away = 2
              else: # meet ghost
                enemy_location_list.append(enemy_pos)

        if len(enemy_location_list) > 0: # ghost is close, check whether safe to cross boundary
          observe_enemy_boundary = self.createTempWall(gameState, enemy_location_list)
          desired_dx = 0
          if self.red:
            desired_dx = 1
          else:
            desired_dx = -1
          desired_x = agent_pos[0] + desired_dx
          desired_y = agent_pos[1]
          if (desired_x, desired_y) in observe_enemy_boundary or gameState.hasWall(desired_x, desired_y):
            boundary_set = self.boundary.copy()
            if agent_pos in boundary_set:
              boundary_set.remove(agent_pos)
            

            # avoid repeatedly choose same boundary as target
            max_iteration_count = min(len(boundary_set), 5)
            earliest_boundary_target_repeat = 0
            best_temp_boundary_target = random.choice(boundary_set)
            for iteration in range(max_iteration_count):
              temp_boundary_target = random.choice(boundary_set)
              temp_x = int(temp_boundary_target[0])
              temp_y = int(temp_boundary_target[1])
              temp_boundary_target = (temp_x, temp_y)
              boundary_set.remove(temp_boundary_target)
              last_step = self.boundary_target_dict.get(temp_boundary_target, -1)

              if last_step == -1: # never set this boundary as target
                best_temp_boundary_target = temp_boundary_target
                break
              else: # set as boundary before
                if self.agent_steps_taken - last_step > MAX_REPEAT_STEPS_OF_BOUNDARY: # repeated long ago
                  best_temp_boundary_target = temp_boundary_target
                  break
                else: # repeated this target recently (can be a good target if repeated far enough)
                  step_dist = self.agent_steps_taken - last_step
                  if step_dist > earliest_boundary_target_repeat:
                    earliest_boundary_target_repeat = step_dist
                    best_temp_boundary_target = temp_boundary_target
            
            self.current_target = best_temp_boundary_target
            self.boundary_target_dict[best_temp_boundary_target] = self.agent_steps_taken
                    
          else: # cannot observe enemy beside, can go straight to enemy land
            target = self.enemy_boundary.copy()
            for item in self.createTempWall(gameState, enemy_location_list):
              if item in target:
                target.remove(item)
            first_chosen_target = self.getClosestPos(gameState, target)
            if self.easy_food_area != []: # change target if has duplicate move
              if first_chosen_target in self.boundary_target_dict: # has set as target and repeatedly done so
                if self.agent_steps_taken - self.boundary_target_dict[first_chosen_target] > MAX_REPEAT_STEPS_OF_BOUNDARY:
                  foodlist_copy = copy.deepcopy(food_list)
                  if first_chosen_target in foodlist_copy:
                    foodlist_copy.remove(first_chosen_target)
                  self.current_target = random.choice(self.enemy_boundary) 
                else: # no duplicate move
                  self.boundary_target_dict[self.current_target] = self.agent_steps_taken
                  self.current_target = first_chosen_target
              else: # never set as target
                self.boundary_target_dict[self.current_target] = self.agent_steps_taken
                self.current_target = first_chosen_target
            else:
              self.current_target = random.choice(target) 
            
        else: # no ghost, food becomes new target
          if food_list != []:
            if len(food_list) <= 2:
              self.current_target = self.getClosestPos(gameState, self.boundary)
            else:
              self.current_target = self.getClosestPos(gameState, food_list)    
    
    # agent is on enemy land as a pacman
    else:
      near_home_point = self.getClosestPos(gameState, self.boundary)
      home_distance = self.getMazeDistance(agent_pos, near_home_point)
      defend_pos = []
      eat_enemy_list = []
      ghost_count = 0

      if self.red: # find points that likely to eat enemy on my land
        defend_x = -1
      else:
        defend_x = 1
      defend_up = (defend_x, agent_pos[1] + 1)
      defend_next = (defend_x, agent_pos[1])
      defend_down = (defend_x, agent_pos[1] - 1)
      
      for item in [defend_up, defend_next, defend_down]:
        if not gameState.hasWall(item[0], item[1]):
          defend_pos.append(item)

      for enemy_index in self.enemy_list: # add ghost location to enemy_location_list, all enemy location to all_enemy_pos
        enemy_state = gameState.getAgentState(enemy_index)
        enemy_pos = enemy_state.getPosition()
        if enemy_pos != None:
          if enemy_state.isPacman:
            if int(agent_state.scaredTimer) == 0:
              if enemy_pos in defend_pos:
                enemy_x = int(enemy_pos[0])
                enemy_y = int(enemy_pos[1])
                eat_enemy_list.append(enemy_pos)
          else:
            ghost_count += 1
            if enemy_pos != None:
              distance = self.getMazeDistance(agent_pos, enemy_pos)
              if distance <= 3: # ghost is close
                if int(enemy_state.scaredTimer) <= 8: # capsule ineffective
                  enemy_location_list.append(enemy_pos)
                  max_space_away = 2

      self.previous_ghost_count = self.current_ghost_count
      self.current_ghost_count = ghost_count

      if eat_enemy_list != []: # 0. come back to own land if enemy is near
         self.current_target = self.getClosestPos(gameState, eat_enemy_list)

      elif len(food_list) <= 2: # 1. almost win, comes back
        self.current_target = near_home_point

      elif int(gameState.data.timeleft) / 4 < (home_distance + 20): # 2. time is up, comes back
        if self.carrying > 0:
          self.current_target = near_home_point

      elif self.current_ghost_count == 0 and self.previous_ghost_count == 0: # 3. no ghost now, eat safely
        self.current_target = self.getClosestPos(gameState, food_list)

      elif self.current_ghost_count > self.previous_ghost_count and self.previous_ghost_count == 0 and self.carrying > 0 and self.easy_food_area == []: # 4. ghost comes back, deposit first
        avoid_enemy = self.createTempWall(gameState, enemy_location_list)
        final_targets = []
        for item in self.enemy_boundary:
          if not item in avoid_enemy:
            final_targets.append(item)
        self.current_target = self.getClosestPos(gameState, final_targets)

      else:
        if self.current_target == None: # choose next new target

          if self.easy_food_area != []: # 3. find easy food first
            self.current_target = self.getClosestPos(gameState, self.easy_food_area)
            if len(self.easy_food_area) == 1: # east last easy food
              self.deposit_easy_food = True

          else:
            if self.deposit_easy_food: # deposit all easy food (once only)
              self.current_target = near_home_point
              self.deposit_easy_food = False 

            if capsule_list != [] and self.capsule_time == 0: # eat capsule before eat hard food
              self.current_target = self.getClosestPos(gameState, capsule_list)
            
            nearest_food = self.getClosestPos(gameState, food_list) # estimate min distance from food to boundary
            min_food_boundary_distance = 9999999
            nearest_food_boundary = (self.maze_height / 2, self.maze_width / 2)
            for item in self.boundary:
              if self.getMazeDistance(nearest_food, item) < min_food_boundary_distance:
                min_food_boundary_distance = self.getMazeDistance(nearest_food, item)
                nearest_food_boundary = item

            if self.capsule_time > 0: # capsule is effective
              if self.capsule_time > min_food_boundary_distance + self.getMazeDistance(agent_pos, nearest_food): # eat any food if capsule lasts long
                self.current_target = self.getClosestPos(gameState, food_list)
              else: # not enough time to come back
                self.current_target = self.getClosestPos(gameState, self.boundary)
            else:  # capsule expires 
              if capsule_list != []: # still has uneaten capsule
                if enemy_location_list == None:
                  if self.carrying > 0:
                    self.current_target = near_home_point
                  else:
                    self.current_target = self.getClosestPos(gameState, food_list + capsule_list)
                else: # find boundary or capsule
                  self.current_target = self.getClosestPos(gameState, capsule_list + self.boundary)
            
              else: # no capsule available (must be careful)
                if self.capsule_time == 0: # no capsule available, all left with hard food
                  next_food = self.getClosestPos(gameState, food_list)
                  if next_food in self.easy_food_area:
                    self.current_target = next_food
                  if next_food in self.hard_food_area: # if close to hard food list, and will not be caught by enemy, then eat
                    if enemy_location_list == []:
                      self.current_target = next_food
                    if enemy_location_list != []:
                      enemy_dist = 99999
                      for enemy in enemy_location_list:
                        dist = self.getMazeDistance(agent_pos, enemy)
                        if dist < enemy_dist:
                          enemy_dist = dist
                      if self.getMazeDistance(agent_pos, next_food) * 2 < enemy_dist:
                        self.current_target = next_food
                      if self.carrying > 0:
                        self.current_target = near_home_point
                      else:
                        food_list_copy = copy.deepcopy(food_list)
                        food_list_copy.remove(next_food)
                        self.current_target = random.choice(food_list_copy) # choose different food if closest one is close to enemy

    # step 2 model the problem, use a* to solve
    if self.capsule_time > 8 or self.current_ghost_count == 0:
      temp_wall_boundary = capsule_list
    temp_wall_list = self.createTempWall(gameState, enemy_location_list, max_space_away)
    if agent_pos in temp_wall_list:
      temp_wall_list.remove(agent_pos)
    
    problem = PositionSearchProblem(gameState, self.current_target, self.index, tempWall=temp_wall_list+temp_wall_boundary)
    path  = self.aStarSearch(problem)

    # step 3 choose action, update status
    # step 3.1 if no path is found, then stop (no status update)
    '''
    Copied from baslineTeam.py
    '''
    if path == []: 
      actions = gameState.getLegalActions(self.index)
      actions.remove(Directions.STOP)
      action_picked = random.choice(actions)
      suboptimal_actions = []
      # avoid go to enemy
      if (agent_state.isPacman and len(enemy_location_list) > 0) or ((not agent_state.isPacman) and agent_state.scaredTimer > 0):
        dx_temp,dy_temp = game.Actions.directionToVector(action_picked) 
        x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
        while (x_temp, y_temp) in temp_wall_list and len(actions) > 1:
          if not (x_temp, y_temp) in (enemy_location_list):
            suboptimal_actions.append(action_picked)
          if action_picked in actions:
            actions.remove(action_picked)
          action_picked = random.choice(actions)
          dx_temp,dy_temp = game.Actions.directionToVector(action_picked)
          x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
          if actions == []:
            if suboptimal_actions != []:
              action_picked = random.choice(suboptimal_actions)
            else:
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
      x = int(pos[0])
      y = int(pos[1])
      if 0 <= x and x < self.maze_width and 0 <= y and y < self.maze_height:
        if not self.maze_walls[x][y]:
          temp_length = self.getMazeDistance(my_pos,pos)
          if temp_length < min_length:
            min_length = temp_length
            min_pos = pos
    if min_pos != None:
      min_pos = (int(min_pos[0]), int(min_pos[1]))
    return min_pos
  
  def getClosestPosGeneral(self, target, pos_list):
    '''for a given target, find the position with shortest maze distance to it
    '''
    min_length = 999999
    min_pos = None
    for pos in pos_list:
      x = int(pos[0])
      y = int(pos[1])
      if 0 <= x and x < self.maze_width and 0 <= y and y < self.maze_height:
        if not self.maze_walls[x][y]:
          temp_length = self.getMazeDistance(pos, target)
          if temp_length < min_length:
            min_length = temp_length
            min_pos = pos
    if min_pos != None:
      min_pos = (int(min_pos[0]), int(min_pos[1]))
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
        if not gameState.hasWall(j, i) and not gameState.hasWall(j+1, i): # enemy boundary has no wall too
          boundary_location.append((j,i))
      else:
        j = int(width/2)
        if not gameState.hasWall(j,i) and not gameState.hasWall(j-1, i):
          boundary_location.append((j,i))
    return boundary_location
  
  def getEnemyBoundary(self, gameState):
    '''calculate the boundary for enemy land
    '''
    boundary_location = []
    for i in range(self.maze_height):
      if self.red:
        j = int(self.maze_width/2)
      else:
        j = int(self.maze_width/2) - 1
      if not gameState.hasWall(j, i):
        if self.red:
          if not gameState.hasWall(j-1, i):
            boundary_location.append((j, i))
        else:
          if not gameState.hasWall(j+1, i):
            boundary_location.append((j, i))
    return boundary_location

  def createTempWall(self, gameState, enemy_location_list=[], max_distance=0):
    '''
    created temporary walls to avoid encountering enemy in next game state
    '''
    maze_matrix = gameState.getWalls().copy()

    dx_dy_list = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    if enemy_location_list != None:
      for x_enemy, y_enemy in enemy_location_list:
        for index, item in enumerate(dx_dy_list):
          dx, dy = item
          x_new = int(x_enemy) + dx
          y_new = int(y_enemy) + dy

          # ensure the new position is within the maze 
          if x_new < 0 or x_new > (self.maze_width - 1) or y_new < 0 or y_new > (self.maze_height - 1):
            continue
          if gameState.hasWall(x_new, y_new):
            continue
          maze_matrix[x_new][y_new] = True

    wall_list = maze_matrix.asList()
    result = []
    for item in wall_list:
      x = int(item[0])
      y = int(item[1])
      result.append((x, y))
    return wall_list


  def aStarSearch(self, problem):
    '''
    Copied from baslineTeam.py
    '''
    from util import PriorityQueue
    myPQ = util.PriorityQueue()
    if problem.startState == None or problem.goal_pos == None:
      return []
    else:
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

        # keep start state if it's part of the wall
        self.walls[int(x)][int(y)] = False

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
    self.maze_matrix = gameState.getWalls().copy()
    self.maze_width = self.maze_matrix.width
    self.maze_height = self.maze_matrix.height
    self.maze_walls = gameState.data.layout.walls
    self.boundary_target_dict = dict() # stores in which move a given boundary has been set as a target
    if self.red:
     self.my_narrow_path_list, self.enemy_narrow_path_list, self.dead_end_list = self.precalculate_narrow_path(gameState) # stores a list of narrow path that leads to dead-end
    else:
      self.enemy_narrow_path_list, self.my_narrow_path_list, self.dead_end_list = self.precalculate_narrow_path(gameState)
    self.easy_food_area, self.hard_food_area = self.calculate_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)
    self.enemy_hard_food_list, self.enemy_easy_food_list = self.calculate_enemy_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)
    self.no_enemy_interval_count = 0
    self.agent_steps_taken = 0
    self.back_to_defend = True
    self.enemy_list = self.getOpponents(gameState)
    self.enemy_boundary = self.getEnemyBoundary(gameState)
    self.previous_target = None
    if self.red:
      self.initial_food = gameState.getRedFood().asList()
      self.initial_enemy_food = gameState.getBlueFood().asList()
      self.initial_enemy_capsule = gameState.getRedCapsules()
    else:
      self.initial_food = gameState.getBlueFood().asList()
      self.initial_enemy_food = gameState.getRedFood().asList()
      self.iniital_enemy_capsule = gameState.getRedCapsules()
    self.cross_boundary_action = None
    if self.red:
      self.cross_boundary_action = Directions.EAST
    else:
      self.cross_boundary_action = Directions.WEST

  def calculate_enemy_food_difficulty(self, gameState, narrow_path_list, dead_end_list):
    '''separates enemy food into two types: inside narrow path, or outside narrow path
    '''
    easy_food_list = []
    hard_food_list = []
    for food in self.getFoodYouAreDefending(gameState).asList():
      if food in narrow_path_list + dead_end_list:
        hard_food_list.append(food)
      else:
        easy_food_list.append(food)
    return (easy_food_list, hard_food_list)
  
  def chooseAction(self, gameState):
    # step 1 determine a target

    agent_state = gameState.getAgentState(self.index)
    agent_pos = agent_state.getPosition()
    enemy_avoid_list = [] # must avoid enemy
    max_space_away = 0
    
    temp_wall_list = [] # cannot cross an area around enemy
    enemy_chase_list = [] # can eat or follow enemy
    enemy_food_list = self.getFoodYouAreDefending(gameState).asList()
    enemy_capsule_list = self.getCapsulesYouAreDefending(gameState)
    temp_wall_boundary = [] # cannot cross a single wall block
    capsule_list = self.getCapsules(gameState)
    food_list = self.getFood(gameState).asList()
    ghost_count = 0
    find_enemy = False
    self.easy_food_area, self.hard_food_area = self.calculate_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)
    self.enemy_hard_food_area, self.enemy_easy_food_area = self.calculate_enemy_food_difficulty(gameState, self.enemy_narrow_path_list, self.dead_end_list)
    self.agent_steps_taken += 1
    enemy_capsule_remaining = False
    if int(agent_state.scaredTimer) > 0:
      enemy_capsule_remaining = True
    else:
      enemy_capsule_remaining = False
    available_actions = gameState.getLegalActions(self.index)
    if agent_pos in self.boundary:
      if self.cross_boundary_action in available_actions:
        available_actions.remove(self.cross_boundary_action)
    action_picked = None

    # locate enemy from gameState
    min_dist_enemy = 9999
    nearest_enemy_target = None
    for enemy_index in self.enemy_list:
      enemy_state = gameState.getAgentState(enemy_index)
      enemy_pos = enemy_state.getPosition()
      if enemy_state.isPacman:
        if enemy_pos != None:
          enemy_chase_list.append(enemy_pos)
          find_enemy = True
          dist = self.getMazeDistance(agent_pos, enemy_pos)
          if dist < min_dist_enemy:
            min_dist_enemy = dist
            nearest_enemy_target = (int(enemy_pos[0]), int(enemy_pos[1]))
      else:
        if enemy_pos != None:
          enemy_avoid_list.append(enemy_pos)
    
    if find_enemy:
      self.no_enemy_interval_count = 0

    # locate enemy from eaten food/capsule
    prior_game_state = self.getPreviousObservation()
    if prior_game_state != None:
      prior_food_list = self.getFoodYouAreDefending(prior_game_state).asList()
      prior_capsule_list = self.getCapsulesYouAreDefending(prior_game_state)
      if len(prior_food_list) + len(prior_capsule_list) > len(enemy_food_list) + len(enemy_capsule_list):
        potential_enemy_set = (set(prior_food_list).union(set(prior_capsule_list))).intersection(set(enemy_food_list).union(set(enemy_capsule_list))) 
        
        for item in potential_enemy_set:
          if not item in enemy_chase_list:
            enemy_chase_list.append(item)
          x = int(item[0])
          y = int(item[1])
          dist = self.getMazeDistance(agent_pos, (x, y))
          if dist < min_dist_enemy:
            min_dist_enemy = dist
            nearest_enemy_target = (int(item[0]), int(item[1]))

    # avoid eating capsule to reserve for attacker
    if capsule_list != []:
      enemy_avoid_list = enemy_avoid_list.copy() + capsule_list.copy()

    # 1. in my own land
    if not agent_state.isPacman:
        
      # 1.1 on my non-boundary land, has enemy 
      if find_enemy:
        
        # enemy didn't eat capsule
        #if int(agent_state.scaredTimer) < CAPSULE_EFFECT_REMAINING:

        # 1.1.2 on my land, has enemy, can locate
        if enemy_chase_list != []:
          target = self.getClosestPos(gameState, enemy_chase_list)
          
          # 1.1.2a enemy eats capsule, current maze dist is safe (pick action to stay near)
          if int(agent_state.scaredTimer) > 0 and min_dist_enemy == SAFE_DISTANCE_FROM_POWER_ENEMY:
            action_picked = Directions.STOP # not lose target (once capsule expires)

          # 1.1.2b enemy eats capsule, current maze dist is unsafe (pick action to stay far)
          elif int(agent_state.scaredTimer) > 0 and min_dist_enemy < SAFE_DISTANCE_FROM_POWER_ENEMY:
            action_picked = self.safe_distance_action(gameState, target)

          # 1.1.2c enemy eats capsule, current maze dist is far (find route to follow) 
          elif int(agent_state.scaredTimer) > 0 and min_dist_enemy > SAFE_DISTANCE_FROM_POWER_ENEMY:
            action_picked = self.breathFirstSearchAgent(gameState)

          # 1.1.2d
          else: # enemy didn't eat capsule, or ineffective to agent
            action_picked = self.breathFirstSearchAgent(gameState)
            
          
            # target = self.get_nearest_enemy_target(gameState, enemy_chase_list, enemy_capsule_remaining)
            # target = None
            # if enemy_capsule_remaining:
            #   if self.current_target == None:
            #     target = self.get_nearest_enemy_target(gameState, agent_pos, enemy_chase_list, enemy_capsule_remaining)
            # else:
            #   if self.current_target == None:
            #     self.current_target = self.getClosestPos(gameState, self.boundary)
              # if self.previous_target != None:
              #   if agent_pos == self.previous_target:
              #     target = self.getClosestPos(gameState, enemy_chase_list)
              #   else:
              #     target = self.previous_target
            
            # if target != None:
            #   if self.current_target == None:
            #     self.current_target = target
            # else:
            #   if self.current_target == None:
            #     if enemy_capsule_list != None:
            #       self.current_target = self.getClosestPos(gameState, enemy_capsule_list)
            #     else:
            #       self.current_target= self.getClosestPos(gameState, enemy_food_list)

            # temp_wall_boundary = self.enemy_boundary.copy()

          # 1.1.1a.2 on my non-boundary land, has enemy not eating capsule, can't locate, go to nearest capsule to boundary, if no capsule, chase go food to boundary
          # else:
          #   if self.current_target == None:
          #     if enemy_capsule_list + enemy_food_list != None:
          #       if len(enemy_capsule_list + enemy_food_list) > 2:
          #         self.current_target = random.choice(enemy_capsule_list+enemy_food_list)
          #       else:
          #         self.current_target = random.choice(gameState, self.boundary)
          #     else:
          #       self.current_target = random.choice(gameState, self.boundary)

          #   temp_wall_boundary = self.enemy_boundary.copy()
        
        # 1.1.3 there's enemy in our land, but can't locate, then reset only if wants to cross boundary, or has no goal
        else:
          if self.current_target == None: # has no target
            self.current_target = random.choice(enemy_food_list+enemy_capsule_list)
          else: # has improper target crossing the boundary
            enemy_boundary_x = self.enemy_boundary[0]
            current_target_x = self.current_target[0]
            if self.red:
              if current_target_x > enemy_boundary_x:
                self.current_target = random.choice(enemy_food_list+enemy_capsule_list)
            else:
              if current_target_x < enemy_boundary_x:
                self.current_target = random.choice(enemy_food_list+enemy_capsule_list)

      # 1.1.2 on my non-boundary land, no enemy in my own land
      else:
        
        # 1.1.2.1 more than 100 steps, no enemy here, change target -> go to boundary
        if self.no_enemy_interval_count > 100:
          if self.current_target == None:
            target = random.choice(self.getClosestPos(gameState, food_list))
        
        # 1.1.2.2 less than 100 steps, no enemy, keep target, wandering across top, best, bottom boundary (if no target, choose best first)
        else:
          if self.current_target == None:
            boundary_targets = self.get_top_best_bottom_boundary(gameState).copy()
            best_targets = boundary_targets[2:-1]
            if not self.previous_target in best_targets or self.previous_target == None:
              self.current_target = random.choice(best_targets)
            else:
              self.current_target = random.choice(boundary_targets)

          temp_wall_boundary = self.enemy_boundary.copy()

      # # 1.2 on boundary of my side
      # else:
        
      #   # 1.2.1 on my boundary, has enemy 
      #   if find_enemy:
          
      #     # 1.2.1a on my boundary, can locate enemy, enemy didn't eat capsule
      #     if int(agent_state.scaredTimer) < BACK_TO_DEFEND_COUNTDOWN:
            

      #       # 1.2.1a.1 on my boundary, can locate enemy, enemy didn't eat capsule, can locate, chase closest enemy
      #       if enemy_chase_list != []:
      #         if self.current_target == None:
      #           self.current_target = self.getClosestPos(gameState, enemy_chase_list)
      #           # self.current_target = self.get_nearest_enemy_target(gameState, enemy_chase_list, enemy_capsule_remaining)
              
      #         temp_wall_boundary = self.enemy_boundary.copy()
            
      #       # 1.2.1a.2 on my boundary land, has enemy, can't locate, enemy didn't eat capsule, go to nearest capsule to boundary, if no capsule, chase closest food to boundary
      #       else:
      #         if self.current_target == None:
      #           if enemy_capsule_list != []:
      #             self.current_target = self.getClosestPos(gameState, enemy_capsule_list)
      #           else:
      #             self.current_target= self.getClosestPos(gameState, enemy_food_list)
              
      #         temp_wall_boundary = self.enemy_boundary.copy()
          
      #     # 1.2.1b on my boundary, can locate enemy, enemy eat capsule, go to enemy land and eat food
      #     else:
      #       if self.current_target == None:
      #         if food_list != []:
      #           self.current_target = random.choice(food_list)
        
      #   # 1.2.2 on my boundary, no enemy in my own land
      #   else:
          
      #     # 1.2.2.1 on my boundary, more than 100 steps no enemy here, go to closest enemy food
      #     if self.no_enemy_interval_count > 150:
      #       if self.current_target == None:
      #         if food_list != []:
      #           self.current_target = random.choice(food_list)
          
      #     # 1.2.2.2 on my boundary, less than 100 steps no enemy, go to a different boundary (if no target, choose best boundary first)
      #     else:
      #       if self.current_target == None:
      #         boundary_targets = self.get_top_best_bottom_boundary(gameState).copy()
      #         if self.previous_target in boundary_targets:
      #           boundary_targets.remove(self.previous_target)
      #         self.current_target = random.choice(boundary_targets)

      #         temp_wall_boundary = self.enemy_boundary.copy()

    # 2 on enemy side
    else:
      # 2.2.1 i'm on enemy side eating
      if find_enemy:
        
        # 2.2.1a i'm on enemy side eating, enemy didn't eat capsule, or capsule about to expire
        if int(agent_state.scaredTimer) < BACK_TO_DEFEND_COUNTDOWN:


          # 2.2.1.1 i'm on enemy side eating, enemy didn't eat capsule, enemy enters my area, can locate, return to closest boundary
          if enemy_chase_list != []:
            if self.current_target == None:
              self.current_target = self.getClosestPos(gameState, self.boundary)
              # self.current_target = self.get_nearest_enemy_target(gameState, enemy_chase_list, enemy_capsule_remaining)

          
          # 2.2.1.2 on enemy side eating, has enemy, enemy didn't eat capsule, can't locate, continue eating, if no target then go to closest boundary
          else:
            if self.current_target == None:
              self.current_target = self.getClosestPos(gameState, self.locate_far_entering_boundary(gameState, enemy_avoid_list))
        
        # 2.2.1b i'm on enemy side eating, enemy still has capsule long, then I continue eating next my food
        else:
          if self.current_target == None:
            if food_list != []:
              self.current_target = self.getClosestPos(gameState, food_list)

              if len(food_list) <= 2:
                self.current_target = self.getClosestPos(gameState, self.locate_far_entering_boundary(gameState, enemy_avoid_list))
            else:
              self.current_target = self.getClosestPos(gameState, self.locate_far_entering_boundary(gameState, enemy_avoid_list))
            
            # temp_wall_boundary = self.boundary.copy()
            # if self.current_target in temp_wall_boundary:
            #   temp_wall_boundary.remove(self.current_target)

      else: # 2.3 no enemy is found on my place, eat next enemy food
        if self.current_target == None:
          if food_list != []:
              if len(food_list) <= 2:
                self.current_target = self.getClosestPos(gameState, self.boundary)
              else:
                self.current_target = self.getClosestPos(gameState, food_list)

          else:
            self.current_target = self.getClosestPos(gameState, self.boundary)

          temp_wall_boundary = self.boundary.copy()
          if self.current_target in temp_wall_boundary:
            temp_wall_boundary.remove(self.current_target)

    temp_wall_list = self.createTempWall(gameState, enemy_avoid_list)
    temp_wall_boundary = temp_wall_boundary.copy() + capsule_list
    if agent_pos in temp_wall_list:
      temp_wall_list.remove(agent_pos)
    if agent_pos in temp_wall_boundary:
      temp_wall_boundary.remove(agent_pos)
    problem = PositionSearchProblem(gameState, self.current_target, self.index, tempWall=temp_wall_list+temp_wall_boundary)
    path  = self.aStarSearch(problem)

    '''
    choose action when no solution is found
    '''
    if action_picked != None:
      return action_picked
    else:
      if path == []: 
        actions = gameState.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        action_picked = random.choice(actions)
        suboptimal_actions = []

        # don't want to meet capsule-eating enemy pacman or enemy ghost, or cross boundary (if not intend to)
        all_avoid_list = []
        if agent_state.scaredTimer > 0:
          all_avoid_list = enemy_chase_list.copy()

        all_avoid_list = all_avoid_list.copy() + temp_wall_boundary.copy() + self.createTempWall(gameState, enemy_avoid_list)

        # avoid go to enemy by randomly choosing only the safe actions
        dx_temp,dy_temp = game.Actions.directionToVector(action_picked) 
        x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
        while (x_temp, y_temp) in temp_wall_list and len(actions) > 1:
          if not (x_temp, y_temp) in all_avoid_list:
            suboptimal_actions.append(action_picked)
          if action_picked in actions:
            actions.remove(action_picked)
          action_picked = random.choice(actions)
          dx_temp,dy_temp = game.Actions.directionToVector(action_picked)
          x_temp, y_temp = int(agent_pos[0] + dx_temp), int(agent_pos[1] + dy_temp)
          if actions == []:
            if suboptimal_actions != []:
              action_picked = random.choice(suboptimal_actions)
            else:
              action_picked = Directions.STOP
        
        dx,dy = game.Actions.directionToVector(action_picked)
        x,y = gameState.getAgentState(self.index).getPosition()
        new_x,new_y = int(x+dx),int(y+dy)

        if (new_x,new_y) == self.current_target: # update target reached, food reached/deposited
          self.previous_target = self.current_target
          self.current_target = None
        
        # update target food that disappeared coz eaten
        if self.current_target in self.initial_food or self.current_target in self.initial_enemy_food:
          if not self.current_target in food_list or not self.current_target in enemy_food_list or not self.current_target in enemy_capsule_list:
            self.current_target = None

        if self.getFood(gameState)[new_x][new_y]:
          self.carrying +=1
        elif (new_x,new_y) in self.boundary:
          self.carrying = 0      
        return action_picked
      
      # step 3.2 if found a path, then find next position + update status
      else: 
        action = path[0]
        dx,dy = game.Actions.directionToVector(action)
        x,y = gameState.getAgentState(self.index).getPosition()
        new_x,new_y = int(x+dx),int(y+dy)
        
        if (new_x,new_y) == self.current_target: # update target reached, food reached/deposited
          self.previous_target = self.current_target
          self.current_target = None
        if self.getFood(gameState)[new_x][new_y]:
          self.carrying +=1
        elif (new_x,new_y) in self.boundary:
          self.carrying = 0
        return path[0]

  def locate_enemy_next_food(self, gameState, enemy_location_list, potential_next_food_list):
    '''find the enemy's nearest potential target
    '''
    nearest_distance = 99999999
    nearest_pos = None
    for enemy_pos in enemy_location_list:
      for item in potential_next_food_list:
        distance = self.getMazeDistance(enemy_pos, item)
        if distance < nearest_distance:
          nearest_distance = distance
          nearest_pos = item
    if nearest_pos != None:
      nearest_pos = (int(nearest_pos[0]), int(nearest_pos[1]))
    
    return nearest_pos
  
  def locate_far_entering_boundary(self, gameState, enemy_location_list, distance=3):
    '''find all boundary entry points that's far from ghost
    '''
    danger_point = self.createTempWall(gameState, enemy_location_list)
    entry_points = []
    distance = 99999999
    for bound in self.boundary:
      if not bound in danger_point:
        temp = self.getClosestPosGeneral(bound, danger_point)
        if temp != None:
          temp_distance = self.getMazeDistance(bound, temp)
          if temp_distance > distance:
            distance = temp_distance
            entry_points.append(bound)

    return entry_points
  
  def get_nearest_enemy_target(self, gameState, agent_pos, enemy_chase_list, enemy_capsule_remaining):
    '''find the nearest enemy target that agent can access safely
    '''
    best_target = None
    good_target_list = []

    if enemy_chase_list != []:
      if enemy_capsule_remaining == True: # capsule remains
        avoid_target = self.createTempWall(gameState, enemy_chase_list)
        for pos in enemy_chase_list:
          for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
              new_x = int(x + pos[0])
              new_y = int(y + pos[1])
              if 0 <= new_x and new_x < self.maze_width and 0 <= new_y and new_y < self.maze_height:
                if not gameState.hasWall(new_x, new_y):
                  if not (x, y) in avoid_target:
                    good_target_list.append((x, y))
        if good_target_list != []:
          best_target = self.getClosestPos(gameState, good_target_list)
        return best_target

      else: # capsule expires
        for pos in enemy_chase_list:
          good_target_list.append(pos)
    
        if good_target_list != []:
          if len(good_target_list) == 1:
            best_target = good_target_list[0]
          else:
            best_target = self.getClosestPosGeneral(agent_pos, good_target_list)
        return best_target
  
  def get_top_best_bottom_boundary(self, gameState):
    '''find the upper and lower, and closest to starting point boundaries
    '''
    x = 0
    top = 0
    bottom = self.maze_height
    best = []
    nearest_distance = 9999999
    starting_point = gameState.getInitialAgentPosition(self.index)
    for item in self.boundary:
      x = item[0]
      y = item[1]
      if y > top:
        top = y
      if y < bottom:
        bottom = y
      distance = self.getMazeDistance(item, starting_point)
      if distance < nearest_distance:
        nearest_distance = distance
        best.append((x, y))

    result = [(x, top), (x, bottom)] + best.copy()

    return result
  
  def safe_distance_action(self, gameState, nearest_enemy_target):
    '''find action that keep defender a safe distance from capsule-eating enemy
    '''
    available_actions = gameState.getLegalActions(self.index)
    action_simulator = dict()
    max_dist = 0
    for item in available_actions:
      next_game_state = gameState.generateSuccessor(self.index, item)
      agent_next_state = next_game_state.getAgentState(self.index)

      if agent_next_state.isPacman:
        next_enemy_dist = 0 # want to avoid crossing the boundary, unwanted action
      else:
        dist = self.getMazeDistance(nearest_enemy_target, agent_next_state.getPosition())
        if dist > SAFE_DISTANCE_FROM_POWER_ENEMY + 1 + 1: # the farthest distance to move, so must be eaten and return to starting point
          dist = 0 # want to avoid being eaten
        else:
          if max_dist < dist:
            max_dist = dist

        dict_value = action_simulator.get(dist, None)
        if dict_value == None: # save actions into dictionary, and return the action that gets further distance from enemy in next round
          action_simulator[dist] = [item]
        else:
          action_simulator[dist].append(item)
    
    return random.choice(action_simulator[max_dist])
  
  def breathFirstSearchAgent(self, gameState, alert_distance=2):
    '''find the action for the first solution returned by BrFS (needed to keep distance from enemy)
    '''
    current_game_state = gameState.deepCopy()
    open_list = util.Queue()
    closed_list = set()
    open_list.push((current_game_state, None))

    # search every node in queue, till it's all searched
    while not open_list.isEmpty():
      current_game_state, last_action = open_list.pop()
      current_pos = current_game_state.getAgentPosition(self.index)
      x = int(current_pos[0])
      y = int(current_pos[1])
      current_pos = (x, y)

      # go check every child node
      if not current_pos in closed_list:
        closed_list.add(current_pos)

        # goal reached
        if current_pos == self.current_target:
          if last_action == None:
            return Directions.STOP # coz reached goal, wait for next move
          else:
            return last_action

        # remove the action that gets defender to cross the boundary
        available_actions = current_game_state.getLegalActions(self.index)
        if current_pos in self.boundary and self.cross_boundary_action in available_actions:
          available_actions.remove(self.cross_boundary_action)

        # check the position and agent state(pacman/ghost) after each action is taken
        for item in available_actions:
          next_game_state = current_game_state.generateSuccessor(self.index, item)
          next_pos = next_game_state.getAgentPosition(self.index)
          next_x = int(next_pos[0])
          next_y = int(next_pos[1])
          next_pos = (next_x, next_y)

          # found the wanted action
          if not next_game_state.getAgentState(self.index).isPacman:
            dist = self.getMazeDistance(next_pos, current_pos)
            if dist > 1: 
              if last_action != None:
                return last_action
              else:
                return item
          else:
            open_list.push((next_game_state.deepCopy(), item))


class Agent3(DummyAgent):
  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    self.carrying = 0
    self.current_target = None
    self.boundary = self.getBoundary(gameState)
    self.maze_walls = gameState.data.layout.walls
    self.maze_matrix = gameState.getWalls().copy() # walls of map
    self.maze_width = self.maze_matrix.width
    self.maze_height = self.maze_matrix.height
  
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

class Agent4(CaptureAgent):
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
    temp_wall_list = self.createTempWall(gameState, enemy_location_list, max_space_away)
    problem = PositionSearchProblem(gameState, self.current_target, self.index, tempWall=temp_wall_list+temp_wall_boundary)
    path  = self.aStarSearch(problem)

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

