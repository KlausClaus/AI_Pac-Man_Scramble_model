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
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'Attacker', second = 'Defender'):

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

# set the capacity to 10 in order to carry more food
# if it carries seldom food, ait will be not efficient
MAX_CAPACITY = 6


# initilaized a capture agent object and make it attack (eat as much food as it can)
# for safety concern, everytime the attacker been traced by an opponent, it will try to escape instead of keep tracing food
# modified from baslineTeam.py class class - DummyAgent
class Attacker(CaptureAgent):
    def __init__(self, *args, **kwargs):
        super(Attacker, self).__init__(*args, **kwargs)
        self.foods = None
        self.agent_position = None
        self.enemy_id = None
        self.capsules = None
        self.agent_state = None



        # the iterated food list before one of them be eaten
        self.iteratedFoods = None
        self.gameStartState = None
        self.height = None
        self.width = None

        # count if the attacker always move along with some duplicate steps
        self.repeat = 0
        # set the distance that can move safely, the attacker only attack when the movable distance is available
        # will modify the movable distance when get into enemy's territory

        # self.movableMazeDistance = 5
        # self.currentMoveStep = 0

        self.ourWidthMiddle = None
        self.enemyWidthMiddle = None

        # find where can the attacker go into enemy's territory
        self.entryPointList = None
        

    def preChooseAction(self, gameState):
        # for the covenient concern, the program will get the required argument for the chooseAction function
        # before the choose Action actually starts

        # current Agent position:
        self.agent_position = gameState.getAgentPosition(self.index)
        # current Agent state:
        self.agent_state = gameState.getAgentState(self.index)
        # the enemy agent id
        # to get the enemy's id, then the defender can efficitly find them and defense
        self.enemy_id = self.getOpponents(gameState)
        # the food list
        self.foods = self.getFood(gameState)
        # the capsule list
        self.capsules = self.getCapsules(gameState)


    # the initialize function
    # copy from baslineTeam.py - class DummyAgent - function registerIntialState
    def registerInitialState(self, gameState):

      CaptureAgent.registerInitialState(self, gameState)

      '''
      Your initialization code goes here, if you need any.
      '''
      self.carrying = 0
      self.current_target = None
      self.boundary = self.getBoundary(gameState)



      self.iteratedFoods = []
      self.height = gameState.data.layout.height
      self.width = gameState.data.layout.width

      if(self.red):
          self.ourWidthMiddle = int((gameState.data.layout.width - 2) /2 )
          self.enemyWidthMiddle = int((gameState.data.layout.width - 2) /2 ) + 1
      else:
          self.ourWidthMiddle = int((gameState.data.layout.width - 2) /2 ) + 1
          self.enemyWidthMiddle = int((gameState.data.layout.width - 2) /2 )      
      
      self.entryPointList = self.findEntryPoint(gameState)

      self.gameStartState = gameState








    # find the entry point of the enemy's territory
    def findEntryPoint(self, gameState):
      tempEntrance = []
      for i in range(1, self.height-1):
        if not gameState.hasWall(self.ourWidthMiddle, i) and not gameState.hasWall(self.enemyWidthMiddle, i):
            tempEntrance.append((self.ourWidthMiddle, i))
      return tempEntrance  
    

    def reverseDirectionHandler(self, gameState):
      reverse = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
      return reverse


    # use this method to avoid repeat move around some grids
    def repeatMoveHandler(self, gameState, actions):
       revers = self.reverseDirectionHandler(gameState)
       previous = None
       if self.getPreviousObservation():
          previous = self.getPreviousObservation().getAgentState(self.index).configuration.direction

       if revers == previous:
         self.repeat += 1
       else:
         self.repeat = 0
       if self.repeat > 4:
          actions.remove(revers)
        
       return actions


    def getClosestEnemyId(self, gameState):
       closestEnemyId = None
       minimumDistance = 9999
       for enemyId in self.enemy_id :
          enemyState = self.stateHelper(enemyId, gameState)
          enemyPosition = self.positionHelper(enemyId, gameState)

          if enemyPosition != None and not enemyState.isPacman:
             if minimumDistance > self.getMazeDistance(self.agent_position, enemyPosition):
                minimumDistance = self.getMazeDistance(self.agent_position, enemyPosition)
                closestEnemyId = enemyId
       return closestEnemyId 
    

    def getClosestEnemyDistance(self, gameState):

       minimumDistance = 9999
       for enemyId in self.enemy_id :
          enemyState = self.stateHelper(enemyId, gameState)
          enemyPosition = self.positionHelper(enemyId, gameState)

          if enemyPosition != None and not enemyState.isPacman:
             if minimumDistance > self.getMazeDistance(self.agent_position, enemyPosition):
                minimumDistance = self.getMazeDistance(self.agent_position, enemyPosition)

       return minimumDistance 


    # the function that find the best action to go through two points
    def findAction(self, gameState, actions, selfTerritory):
       # after take action X, the agent will closest to the target, then action X is the best action
       tempAction = None
       minimumDistance = 99999
       for action in actions:
          leaf = self.successorHelper(gameState, action)
          # if I go to this step and become a pacman
          if selfTerritory and leaf.getAgentState(self.index).isPacman:
             continue
          
          targetPosition = leaf.getAgentPosition(self.index)
          distanceToTarget = self.mazeDistanceHelper(self.current_target, targetPosition)

          if distanceToTarget < minimumDistance:
             tempAction = action
             minimumDistance = distanceToTarget
          
       return tempAction


    def getClosestEnemyId(self, gameState):
       closestEnemyId = None
       minimumDistance = 9999
       for enemyId in self.enemy_id :
          enemyState = self.stateHelper(enemyId, gameState)
          enemyPosition = self.positionHelper(enemyId, gameState)

          if enemyPosition != None and not enemyState.isPacman:
             if minimumDistance > self.getMazeDistance(self.agent_position, enemyPosition):
                minimumDistance = self.getMazeDistance(self.agent_position, enemyPosition)
                closestEnemyId = enemyId
       return closestEnemyId 
    

    def getClosestEnemyDistance(self, gameState):

       minimumDistance = 9999
       for enemyId in self.enemy_id :
          enemyState = self.stateHelper(enemyId, gameState)
          enemyPosition = self.positionHelper(enemyId, gameState)

          if enemyPosition != None and not enemyState.isPacman:
             if minimumDistance > self.getMazeDistance(self.agent_position, enemyPosition):
                minimumDistance = self.getMazeDistance(self.agent_position, enemyPosition)

       return minimumDistance 


    def getClosestEnemyPosition(self, gameState):

       minimumDistance = 9999
       minimumPosition = None
       for enemyId in self.enemy_id :
          enemyState = self.stateHelper(enemyId, gameState)
          enemyPosition = self.positionHelper(enemyId, gameState)

          if enemyPosition != None and not enemyState.isPacman:
             if minimumDistance > self.getMazeDistance(self.agent_position, enemyPosition):
                minimumDistance = self.getMazeDistance(self.agent_position, enemyPosition)
                minimumPosition = enemyPosition
                

       return minimumPosition






    # get the position of an agent according to the id
    def positionHelper(self, agent_id, gameState):
       return gameState.getAgentState(agent_id).getPosition()

    def stateHelper(self, agent_id, gameState):
       return gameState.getAgentState(agent_id)
    
    def scaredTimeHelper(self, agent_id, gameState):
       return gameState.getAgentState(agent_id).scaredTimer

    def mazeDistanceHelper(self, position1, position2):
       return self.getMazeDistance(position1, position2)
    
    # the function used to get the enemys position
    def get_killer_position(self, enemy_position_list, gameState):
       position = []
       # go thorough the height and width of the game's layout
       for i in range(gameState.data.layout.height):
          for j in range(gameState.data.layout.width):
             for enemyPos in enemy_position_list:
                # if at this state, the game doesn't have wall, then make the current enemy's position as wall.
                if not gameState.hasWall(j, i):
                   # make our agent escape from the enemy in 4 steps away
                   if(self.getMazeDistance((j,i), enemyPos) < 5):
                     
                      position.append((j,i))
       return position


    def getSolution(self, gameState, problem):
             # copy from baslineTeam.py - class DummyAgent
      path  = self.defenderAStarSearch(problem)
      
      if path == []:
        actions = gameState.getLegalActions(self.index)
        return random.choice(actions)
      else:
        action = path[0]
        dx,dy = game.Actions.directionToVector(action)
        x,y = gameState.getAgentState(self.index).getPosition()
        new_x,new_y = int(x+dx),int(y+dy)
        if (new_x,new_y) == self.current_target:
          self.current_target = None
        if self.getFood(gameState)[new_x][new_y]:
          self.carrying +=1
        elif (new_x,new_y) in self.boundary:
          self.carrying = 0
        return path[0]



    # the choose action function which been improved 
    # modified from baslineTeam.py - class DummyAgent - function chooseAction
    def chooseAction(self, gameState):
      """
      Picks among actions randomly.
      """
      
      self.preChooseAction(gameState)
      problem = None


      initActions = gameState.getLegalActions(self.index)
      
      actions = self.repeatMoveHandler(gameState, initActions)

      # the actions differ from when at the self side or the opponents side.
      # "agent_state.isPacman" means the agent is at the opponent side, on the self side(ghost) it will be represented by "not agent_state.isPacman"

      # when the agent is at the 
      # opponent side, 
      # do the following action:
      if self.agent_state.isPacman:
        # create a list to store all the enemies' position
        enemy_position = []

        # the rest time after the agent eat the capsule

        rest_mighty_time = None

        if self.getClosestEnemyId(gameState) != None:
           rest_mighty_time = self.scaredTimeHelper(self.getClosestEnemyId(gameState), gameState)
        else:
           
          rest_time1 = self.scaredTimeHelper(self.enemy_id[0], gameState)
          rest_time2 = self.scaredTimeHelper(self.enemy_id[1], gameState)

          # check the minimum scared time since there maybe a situation that 2 enemy have different scared time since one of them has been killed
          rest_mighty_time = min(rest_time1, rest_time2)
        
        # if the agent is currently ate the capsule and it cannot be killed
        if rest_mighty_time > 3:
          # if self.getClosestEnemyDistance(gameState) < 2:
          #    self.current_target = self.positionHelper(self.getClosestEnemyId, gameState)
          #    return self.findAction(gameState, actions, False)   
          # if there is no current target or the current target is not in the food list (e.g. the agent is looking for a boundary to go in)
          if self.current_target == None or self.current_target not in self.foods.asList() or self.current_target != self.getClosestEnemyPosition(gameState):
             # the only task is to find and eat the closest foods
            if self.getClosestEnemyDistance(gameState) < 3:
               self.current_target = self.getClosestEnemyPosition(gameState)
               return self.findAction(gameState, actions, False)   
            
            self.current_target = self.getClosestPos(gameState, self.foods.asList())
            
            return self.findAction(gameState, actions, False)   
            
        # else, there is only 3 steps beofre the capsules time ended or didn't eat capsule
        else:
          


          # go through the enemies position and be careful
          for current_enemy_id in self.enemy_id:
            # get the enemy's position
            current_enemy_state_position = self.positionHelper(current_enemy_id, gameState)

            # if the enemy is 5 step away from the current agent, it can get the position
            # if the enemy is more than 5 step away from the current agent, it will return None

            # don't defend the enemy that position is more than 5 steps
            if current_enemy_state_position == None:
                pass
            # the enemy's current position is within 5 steps to reach current agent's position
            else:
              if self.stateHelper(current_enemy_id, gameState).isPacman:
                pass
              # target enemy is in the ghost mode (can kill the current agent) and in 5 steps distance
              else:
                current_x, current_y = current_enemy_state_position
                # set the x and y coordinate to int in order to convert some coordinate like 5.0, 4.0...
                current_enemy_state_position = (int(current_x), int(current_y))
                # add the enemy position to the list
                enemy_position.append(current_enemy_state_position)

            # distance_from_enemy = self.mazeDistanceHelper(self.agent_position, current_enemy_state_position)

          distance_from_enemy = self.getClosestEnemyDistance(gameState)
          if distance_from_enemy!= None and distance_from_enemy < 5:
              # go back and choose another way to attack since the enemy is defending at this state
              if distance_from_enemy < 3:
                all_entrance = self.entryPointList.copy()

                if self.agent_position in all_entrance:
                  # choose target from the rest of boundaries
                  all_entrance.remove(self.agent_position)
                  # all_entrance.remove(self.getClosestPos(gameState, all_entrance))
                  
                self.current_target = random.choice(all_entrance)

                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
              
              else:
                 
                self.current_target = self.getClosestPos(gameState, self.entryPointList)
                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
              # return self.findAction(gameState, actions, False)   

          elif self.carrying == MAX_CAPACITY or len(self.getFood(gameState).asList())<=2:
            # if agent got all the food it needed
            # it will reach to the closest boundary with A* search (manhattanDistance as heuristic)

              if distance_from_enemy < 3:
                all_entrance = self.entryPointList.copy()

                if self.agent_position in all_entrance:
                  # choose target from the rest of boundaries
                  all_entrance.remove(self.agent_position)
                  # all_entrance.remove(self.getClosestPos(gameState, all_entrance))
                  
                self.current_target = random.choice(all_entrance)

                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
              
              else:
                 
                self.current_target = self.getClosestPos(gameState, self.entryPointList)
                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)


            # self.current_target = self.getClosestPos(gameState, self.entryPointList)
            # problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
            # return self.getSolution(gameState, problem)
            # return self.findAction(gameState, actions, False)   
          
          else:
            # if there is a capsule then go to eat the capsule
            if len(self.capsules) > 0:
               
                # go to eat the capsule
                self.current_target = self.getClosestPos(gameState, self.capsules)
                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
                # return self.findAction(gameState, actions, False)   
           
            # if agent have more capacity to carry
            # it will find the next closest food
            else: 
              self.current_target = self.getClosestPos(gameState,self.foods.asList())
              problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
              return self.getSolution(gameState, problem)
              # return self.findAction(gameState, actions, False)     
            

        problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
        return self.getSolution(gameState, problem)


      # when the agent is at their 
      # self side, 
      # do the following action:

      # - find the boundary and go to the closest boundary, 
      # then detect, if no one is guarding the boundary, then go beyond the boundary to find food
      # if there is some opponent agent guarding at the boundary, then choose another path to go through the boundary.
      else: 
      
        enemyList=[]
        # indicate whether the current Agent needs to change a target since enemy is defending:
        choose_another_way = False
        
        # if current position is at the bouindary already

        if self.agent_position in self.entryPointList:

          # go through all the enemies id

          
          for current_enemy_id in self.enemy_id:
              # get the enemy's position
              current_enemy_state_position = self.positionHelper(current_enemy_id, gameState)

              # if the enemy is 5 step away from the current agent, it can get the position
              # if the enemy is more than 5 step away from the current agent, it will return None

              # don't defend the enemy that position is more than 5 steps
              if current_enemy_state_position == None:
                pass
              else:
                enemyList.append(current_enemy_state_position)
                current_x, current_y = current_enemy_state_position
                # set the x and y coordinate to int in order to convert some coordinate like 5.0, 4.0...
                current_enemy_state_position = (int(current_x), int(current_y))


                # check if the enemy is very close to the current agent, then choose another path
                # in order to avoid the defender kills the current agent
                distance_from_enemy = self.mazeDistanceHelper(self.agent_position, current_enemy_state_position)
                # if the distance < 3 and it's not a packman (it is a ghost that can kill the current packman)
                if self.stateHelper(current_enemy_id, gameState).isPacman:
                  pass
                else:
                  if distance_from_enemy < 3:
                    # choose another way to attack since the enemy is defending at this state
                    choose_another_way = True


                    all_entrance = self.entryPointList.copy()

                    if self.agent_position in all_entrance:
                      # choose target from the rest of boundaries
                      all_entrance.remove(self.agent_position)
                      # all_entrance.remove(self.getClosestPos(gameState, all_entrance))
                      
                    self.current_target = random.choice(all_entrance)

                    #   break 

                    problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemyList, gameState))
                    return self.getSolution(gameState, problem)
                    # return self.findAction(gameState, actions, True)                  
        
        # if current position is not at boundary
        else:
            # self.current_target = random.choice(self.entryPointList)
            # problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemyList, gameState))
            # return self.getSolution(gameState, problem)

            pass
            # return self.findAction(gameState, actions, True)

                   

        # modified from baselineTeam.py - DummyAgent class
        # if there is no enemy defending on the current agent, we don't need to choose another path
        if choose_another_way == False:
          # if the agent currently doesn't have a target
          if self.current_target == None:
            # then set the current target to the foods that is the most close to the agent's position

            self.current_target=self.getClosestPos(gameState, self.foods.asList())
            # self.current_target = random.choice(self.foods.asList())
            problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemyList, gameState))
            return self.getSolution(gameState, problem)


        problem = PositionSearchProblem(gameState,self.current_target,self.index)
        return self.getSolution(gameState, problem)
  


    # the get closest position function, same as baselineTeam.py
    # copy from baslineTeam.py - class DummyAgent - function getClosestPos
    def getClosestPos(self,gameState,pos_list):
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
    

    # the choose get boundary function, same as baselineTeam.py 
    # copy from baslineTeam.py - class DummyAgent - function getBoundary
    def getBoundary(self,gameState):
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



    def attackerAStarSearch(self, problem):
      """Search the node that has the lowest combined cost and heuristic first."""
      
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



    def defenderAStarSearch(self, problem):
      """Search the node that has the lowest combined cost and heuristic first."""

      
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
    


    def successorHelper(self, gameState, action):
      temp = gameState.generateSuccessor(self.index, action)
      result = temp.getAgentState(self.index).getPosition()

      if result != nearestPoint(result):
        return temp.generateSuccessor(self.index, action)
      else:
        return temp
      




























# use Attacker agent as the base code and do some modification to make it defend from oponents' attack
class Defender(Attacker):
    def __init__(self, *args, **kwargs):
        super(Attacker, self).__init__(*args, **kwargs)
        self.our_total_foods = None
        self.our_actual_foods = None
        self.agent_position = None
        self.enemy_id = None
        self.agent_state = None
        self.foods = None
        self.entryPointList = None
        

    def preChooseAction(self, gameState):
        # for the covenient concern, the program will get the required argument for the chooseAction function
        # before the choose Action actually starts

        # current Agent position:
        self.agent_position = gameState.getAgentPosition(self.index)
        # current Agent state:
        self.agent_state = gameState.getAgentState(self.index)
        # the enemy agent id
        # to get the enemy's id, then the defender can efficitly find them and defense
        self.enemy_id = self.getOpponents(gameState)
        # our food list
        
        self.our_actual_foods = self.getFoodYouAreDefending(gameState).asList()
        self.foods = self.getFood(gameState)
        
    # the initialize function
    # copy from baslineTeam.py - class DummyAgent - function registerIntialState
    def registerInitialState(self, gameState):

      CaptureAgent.registerInitialState(self, gameState)

      '''
      Your initialization code goes here, if you need any.
      '''
      self.our_total_foods = []

      self.carrying = 0
      self.current_target = None
      self.boundary = self.getBoundary(gameState)
      self.height = gameState.data.layout.height
      self.width = gameState.data.layout.width
      self.gameJustStart = True

      if(self.red):
          self.ourWidthMiddle = int((gameState.data.layout.width - 2) /2 )
          self.enemyWidthMiddle = int((gameState.data.layout.width - 2) /2 ) + 1
      else:
          self.ourWidthMiddle = int((gameState.data.layout.width - 2) /2 ) + 1
          self.enemyWidthMiddle = int((gameState.data.layout.width - 2) /2 )      
      
      self.entryPointList = self.findEntryPoint(gameState)




    # find the entry point of the enemy's territory
    def findEntryPoint(self, gameState):
      tempEntrance = []
      for i in range(1, self.height-1):
        if not gameState.hasWall(self.ourWidthMiddle, i) and not gameState.hasWall(self.enemyWidthMiddle, i):
            tempEntrance.append((self.ourWidthMiddle, i))
      return tempEntrance  


    def findAction(self, gameState, actions):
       # after take action X, the agent will closest to the target, then action X is the best action
       tempAction = None
       minimumDistance = 99999
       for action in actions:
          leaf = self.successorHelper(gameState, action)
          # if I go to this step and become a pacman
          if leaf.getAgentState(self.index).isPacman:
             continue
          
          targetPosition = leaf.getAgentPosition(self.index)
          distanceToTarget = self.mazeDistanceHelper(self.current_target, targetPosition)

          if distanceToTarget < minimumDistance:
             tempAction = action
             minimumDistance = distanceToTarget
          
       return tempAction
    

    # compute the enemies' boundary line
    def compute_enemy_boundary(self, gameState, width, height):
      boundary_list = []
      for i in range(height):
        if self.red:
          j = int(width/2)
        else:
          j = int(width/2)-1
        if not gameState.hasWall(j,i):
          boundary_list.append((j,i))
      return boundary_list
    
    # find the target enemy
    def determine_target_based_on_enemy(self, gameState):
        enemy_packman_position_list = []
        for enemyIndex in self.enemy_id:
        
          current_enemy_state_position = self.positionHelper(enemyIndex, gameState)
          # if current enemy's position can be detected, means it is in 5 steps distance
          if current_enemy_state_position != None:
            # if enemy is currently a packman, same as Attacker class, add the enemy to the enemy list
            if self.stateHelper(enemyIndex, gameState).isPacman:
                current_enemy_x, current_enemy_y = current_enemy_state_position
                enemy_packman_position_list.append((int(current_enemy_x), int(current_enemy_y)))
        return enemy_packman_position_list
    
    # check whether there are some enemies appear
    def check_enemy_appearance(self, gameState):
      enemy_appear = False
      # traverse all the enemies
      for current_enemy_id in self.enemy_id:
          # if enemy become a packman, means it comes to our territory
          if self.stateHelper(current_enemy_id, gameState).isPacman:
            enemy_appear = True
            return enemy_appear

      return enemy_appear
    

    def chooseAction(self, gameState):
      problem = None
      self.preChooseAction(gameState)
      
      actions = gameState.getLegalActions(self.index)

      # the choose get boundary function, same as baselineTeam.py 
      # modified from baslineTeam.py - class DummyAgent - function getBoundary
      
      height = gameState.data.layout.height
      width = gameState.data.layout.width
      # opposite from our layout since this is the enemy's boundary
      enemy_boundary_location = self.compute_enemy_boundary(gameState, width, height)

      # if there is no enemy appear in our territory:
      if self.check_enemy_appearance(gameState) == False and self.gameJustStart:
        # print("here")
         # if there is no current target for the agent
        # if self.current_target==None:

        # self.current_target = random.choice(self.entryPointList)
        
        # problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location)
        # return self.getSolution(gameState, problem)
        
        # if self.positionHelper(self.index, gameState) in self.entryPointList:
        #   print("change state")

        self.gameJustStart = False
        # self.current_target = self.getClosestPos(gameState, self.entryPointList)
        if self.red:
              self.current_target= (int(width/2)-2, int(height/2))
              problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location)
              return self.getSolution(gameState, problem)
        else:
              self.current_target= (int(width/2)+1, int(height/2))
              problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location)
              return self.getSolution(gameState, problem)
        

      
      # if there is one or more enemy appear in our territory:
      else:
         
        # same as the attacker find enemy code
        # create a list to store the invaders' position
        
        # if the enemy is in 5 step distance from current agent
        # traverse all the enemy

        enemy_packman_position_list = self.determine_target_based_on_enemy(gameState)
        # if our food been eaten, we will know where the enemy is
        # and we go to trace that enemy
        if len(self.our_actual_foods) < len(self.our_total_foods):
          # means our food been eaten
          # and we need to find out the food position
          temp_food = set(self.our_total_foods) - set(self.our_actual_foods)

          # if there are more than one food been eaten, we need to traverse them
          while(len(temp_food) > 0):
            # popup the most reacent eaten food
            food_position = temp_food.pop()
            # if it is not in the list we are tracing for, add it
            if not food_position in enemy_packman_position_list:
               enemy_packman_position_list.append(food_position)

        self.our_total_foods = self.our_actual_foods

          
        enemy_position = []
        # if enemy eat a capsule, we need to consider enemy's nearby position as a killer area as well
        if self.scaredTimeHelper(self.index, gameState) > 0:
          # self.current_target = self.getClosestPos(gameState, self.foods.asList())
          # problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location + self.get_killer_position(enemy_packman_position_list, gameState))
          
          # return self.getSolution(gameState, problem)

          
          # go through the enemies position and be careful
          for current_enemy_id in self.enemy_id:
            # get the enemy's position
            current_enemy_state_position = self.positionHelper(current_enemy_id, gameState)

            # if the enemy is 5 step away from the current agent, it can get the position
            # if the enemy is more than 5 step away from the current agent, it will return None

            # don't defend the enemy that position is more than 5 steps
            if current_enemy_state_position == None:
                pass
            # the enemy's current position is within 5 steps to reach current agent's position
            else:
              if self.stateHelper(current_enemy_id, gameState).isPacman:
                pass
              # target enemy is in the ghost mode (can kill the current agent) and in 5 steps distance
              else:
                current_x, current_y = current_enemy_state_position
                # set the x and y coordinate to int in order to convert some coordinate like 5.0, 4.0...
                current_enemy_state_position = (int(current_x), int(current_y))
                # add the enemy position to the list
                enemy_position.append(current_enemy_state_position)

            # distance_from_enemy = self.mazeDistanceHelper(self.agent_position, current_enemy_state_position)

          distance_from_enemy = self.getClosestEnemyDistance(gameState)
          if distance_from_enemy!= None and distance_from_enemy < 4:
              # go back and choose another way to attack since the enemy is defending at this state
              # self.current_target = random.choice(self.boundary)
              if distance_from_enemy < 3:
                  # choose another way to attack since the enemy is defending at this state
                  

                  all_entrance = self.entryPointList.copy()

                  if self.agent_position in all_entrance:
                    # choose target from the rest of boundaries
                    all_entrance.remove(self.agent_position)
                    # all_entrance.remove(self.getClosestPos(gameState, all_entrance))
                    
                  self.current_target = random.choice(all_entrance)

                  problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                  return self.getSolution(gameState, problem)
              else:
                self.current_target = self.getClosestPos(gameState, self.entryPointList)
                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
                # return self.findAction(gameState, actions, False)   

          elif self.carrying == MAX_CAPACITY-2 or len(self.getFood(gameState).asList())<=2:
              if distance_from_enemy < 3:
                  # choose another way to attack since the enemy is defending at this state
                  

                  all_entrance = self.entryPointList.copy()

                  if self.agent_position in all_entrance:
                    # choose target from the rest of boundaries
                    all_entrance.remove(self.agent_position)
                    # all_entrance.remove(self.getClosestPos(gameState, all_entrance))
                    
                  self.current_target = random.choice(all_entrance)

                  problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                  return self.getSolution(gameState, problem)
              else:
                self.current_target = self.getClosestPos(gameState, self.entryPointList)
                problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
                return self.getSolution(gameState, problem)
            # return self.findAction(gameState, actions, False)   
          
          else:
            # if agent have more capacity to carry
            # it will find the next closest food
            # self.current_target = self.getClosestPos(gameState,self.foods.asList())
            self.current_target = random.choice(self.getFood(gameState).asList())
            problem = PositionSearchProblem(gameState,self.current_target,self.index, self.get_killer_position(enemy_position, gameState))
            return self.getSolution(gameState, problem)



        else:
           if self.stateHelper(self.index, gameState).isPacman:
              self.current_target = self.getClosestPos(gameState, self.entryPointList)
              problem = PositionSearchProblem(gameState, self.current_target, self.index, self.get_killer_position(enemy_position, gameState))
              return self.getSolution(gameState, problem)
           else:
              if len(enemy_packman_position_list) > 0:
                  self.current_target = self.getClosestPos(gameState, enemy_packman_position_list)
                  problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location)
                  return self.getSolution(gameState, problem)
              else:
                  self.current_target = random.choice(self.entryPointList)
                  # self.current_target = self.getClosestPos(gameState, self.boundary)
                  problem = PositionSearchProblem(gameState, self.current_target, self.index, enemy_boundary_location)
                  return self.getSolution(gameState, problem)


      

  
    def getSolution(self, gameState, problem):
             # copy from baslineTeam.py - class DummyAgent
      path  = self.defenderAStarSearch(problem)
      
      if path == []:
        actions = gameState.getLegalActions(self.index)
        return random.choice(actions)
      else:
        action = path[0]
        dx,dy = game.Actions.directionToVector(action)
        x,y = gameState.getAgentState(self.index).getPosition()
        new_x,new_y = int(x+dx),int(y+dy)
        if (new_x,new_y) == self.current_target:
          self.current_target = None
        if self.getFood(gameState)[new_x][new_y]:
          self.carrying +=1
        elif (new_x,new_y) in self.boundary:
          self.carrying = 0
        return path[0]
      
# set the position search algorithm
# modified from baslineTeam.py - class PositionSearchProblem
class PositionSearchProblem:
    def __init__(self, gameState, goal, agentIndex = 0, killer_position = [], costFn = lambda x: 1):
        self.walls = gameState.getWalls().copy()
        # for every position of enemy's current state (for the attacker) or the enemy boundary (for the defender)
        for killerPos in killer_position:
           killer_x = int(killerPos[0])
           killer_y = int(killerPos[1])
           # mark the enemies' position as wall, so our packman will avoid it
           self.walls[killer_x][killer_y] = True
        self.costFn = costFn
        x,y = gameState.getAgentState(agentIndex).getPosition()
        self.startState = int(x),int(y)
        self.goal_pos = goal
        self.gameState = gameState

    def getStartState(self):
      return self.startState
    
    def getGameState(self):
       return self.gameState

    def isGoalState(self, state):

      return state == self.goal_pos


    def getGoal(self):
       return self.goal_pos

    def getSuccessors(self, state):
        successors = []
        for action in [game.Directions.NORTH, game.Directions.SOUTH, game.Directions.EAST, game.Directions.WEST]:
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
      