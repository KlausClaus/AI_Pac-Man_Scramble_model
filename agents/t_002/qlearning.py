from captureAgents import CaptureAgent
import random, time, util
import game
import numpy as np
import util
import os


def createTeam(firstIndex, secondIndex, isRed,
               first='AgentQ', second='AgentQ'):
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

MAX_CAPACITY = 4
dangerZONES = 3
class DummyAgent(CaptureAgent):
    X = 0

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.initialPosition = gameState.getAgentState(self.index).getPosition()
        self.carrying = 0
        self.current_target = None
        self.boundary = self.getBoundary(gameState)
        self.previousFoodList = []
        self.resetFlag = False

    def wasReset(self, gameState):
        currentPos = gameState.getAgentState(self.index).getPosition()
        if currentPos == self.initialPosition:
            if not self.resetFlag:
                self.resetFlag = True
                return True
        else:
            self.resetFlag = False
        return False

    def chooseAttackAction(self, gameState):
        if self.wasReset(gameState):
            DummyAgent.X = 1 - DummyAgent.X
        myPos = gameState.getAgentPosition(self.index)
        foodGrid = self.getFood(gameState)
        foodList = foodGrid.asList()
        opponentsIndex = self.getOpponents(gameState)
        opponentsPos = [gameState.getAgentState(i).getPosition() for i in opponentsIndex if
                        gameState.getAgentState(i).getPosition() is not None and not gameState.getAgentState(
                            i).isPacman]
        capsuleList = self.getCapsules(gameState)

        # Determine danger zones
        dangerZones = self.getDangerList(opponentsPos, gameState)

        # Check if agent is scared
        scared = any(gameState.getAgentState(i).scaredTimer > 0 for i in opponentsIndex)

        # Set target to None if it's been consumed or no longer viable
        if self.current_target and self.current_target not in foodList + capsuleList:
            self.current_target = None

        # If carrying a lot of food or only a few left, return to boundary
        if self.carrying >= MAX_CAPACITY or len(foodList) <= 2:
            if not self.current_target:
                self.current_target = self.getClosestPos(gameState, self.boundary)

        # If not scared, consider going for capsules or food
        elif not scared:
            if not self.current_target:
                if capsuleList and min(
                        self.getMazeDistance(myPos, capsule) for capsule in capsuleList) <= dangerZONES:
                    self.current_target = self.getClosestPos(gameState, capsuleList)
                else:
                    self.current_target = self.getClosestPos(gameState, foodList)
        else:
            if not self.current_target:
                self.current_target = self.getClosestPos(gameState, foodList)

        # If still no target, choose a random action
        if not self.current_target:
            return random.choice(gameState.getLegalActions(self.index))

        # Else, find a path to the target considering danger zones
        problem = PositionSearchProblem(gameState, self.current_target, self.index, dangerZones)
        path = self.aStarSearch(problem)

        if not path:
            return random.choice(gameState.getLegalActions(self.index))

        action = path[0]
        dx, dy = game.Actions.directionToVector(action)
        new_x, new_y = int(myPos[0] + dx), int(myPos[1] + dy)

        # Update carrying count if food is eaten
        if foodGrid[new_x][new_y]:
            self.carrying += 1
        elif (new_x, new_y) in self.boundary:
            self.carrying = 0

        return action

    def getDangerList(self, opponentsPos, gameState):
        dangerZones = []
        height = gameState.data.layout.height
        width = gameState.data.layout.width
        for y in range(height):
            for x in range(width):
                if any(self.getMazeDistance((x, y), oppoPos) <= dangerZONES for oppoPos in
                       opponentsPos) and not gameState.hasWall(x, y):
                    dangerZones.append((x, y))
        return dangerZones

    def chooseDefendAction(self, gameState):
        if self.wasReset(gameState):
            DummyAgent.X = 1 - DummyAgent.X
        myPos = gameState.getAgentPosition(self.index)
        opponentsIndex = self.getOpponents(gameState)
        currentFoodList = self.getFoodYouAreDefending(gameState).asList()

        hasInvader = any(gameState.getAgentState(i).isPacman for i in opponentsIndex)

        height, width = gameState.data.layout.height, gameState.data.layout.width
        j = int(width / 2) if self.red else int(width / 2) - 1
        oppoBoundary = [(j, i) for i in range(height) if not gameState.hasWall(j, i)]

        if not hasInvader:
            if self.current_target is None:
                self.current_target = random.choice(self.boundary)
            problem = PositionSearchProblem(gameState, self.current_target, self.index, oppoBoundary)
        else:
            defend_list = [gameState.getAgentState(i).getPosition() for i in opponentsIndex if
                           gameState.getAgentState(i).isPacman and gameState.getAgentState(i).getPosition() is not None]

            if len(currentFoodList) < len(self.previousFoodList):
                eatenFood = set(self.previousFoodList) - set(currentFoodList)
                defend_list.extend([pos for pos in eatenFood if pos not in defend_list])

            self.previousFoodList = currentFoodList

            if not defend_list:
                self.current_target = self.current_target or random.choice(currentFoodList)
            else:
                self.current_target = self.getClosestPos(gameState, defend_list)

            dangerList = oppoBoundary
            if gameState.getAgentState(self.index).scaredTimer > 0:
                dangerList += self.getDangerList(defend_list, gameState)
            problem = PositionSearchProblem(gameState, self.current_target, self.index, dangerList)

        path = self.aStarSearch(problem)
        if not path:
            return random.choice(gameState.getLegalActions(self.index))

        action = path[0]
        dx, dy = game.Actions.directionToVector(action)
        new_x, new_y = int(myPos[0] + dx), int(myPos[1] + dy)
        if (new_x, new_y) == self.current_target:
            self.current_target = None
        if self.getFood(gameState)[new_x][new_y]:
            self.carrying += 1
        elif (new_x, new_y) in self.boundary:
            self.carrying = 0

        return action

    def getDangerList(self, opponentsPos, gameState):
        height = gameState.data.layout.height
        width = gameState.data.layout.width
        result = []
        for i in range(height):
            for j in range(width):
                for oppoPos in opponentsPos:
                    if not gameState.hasWall(j, i) and self.getMazeDistance((j, i), oppoPos) <= 3:
                        result.append((j, i))
        return result

    def getClosestPos(self, gameState, pos_list):
        min_length = 9999
        min_pos = None
        my_local_state = gameState.getAgentState(self.index)
        my_pos = my_local_state.getPosition()
        for pos in pos_list:
            temp_length = self.getMazeDistance(my_pos, pos)
            if temp_length < min_length:
                min_length = temp_length
                min_pos = pos
        return min_pos

    def getBoundary(self, gameState):
        boundary_location = []
        height = gameState.data.layout.height
        width = gameState.data.layout.width
        for i in range(height):
            if self.red:
                j = int(width / 2) - 1
            else:
                j = int(width / 2)
            if not gameState.hasWall(j, i):
                boundary_location.append((j, i))
        return boundary_location

    def aStarSearch(self, problem):
        """Search the node that has the lowest combined cost and heuristic first."""

        from util import PriorityQueue
        myPQ = util.PriorityQueue()
        startState = problem.getStartState()
        # print(f"start states {startState}")
        startNode = (startState, '', 0, [])
        heuristic = problem._manhattanDistance
        myPQ.push(startNode, heuristic(startState))
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
                best_g[str(state)] = cost
                if problem.isGoalState(state):
                    path = path + [(state, action)]
                    actions = [action[1] for action in path]
                    del actions[0]
                    return actions
                for succ in problem.getSuccessors(state):
                    succState, succAction, succCost = succ
                    newNode = (succState, succAction, cost + succCost, path + [(node, action)])
                    myPQ.push(newNode, heuristic(succState) + cost + succCost)
        return []

class AgentA(DummyAgent):
    def chooseAction(self, gameState):
        # if DummyAgent.X == 1:
        #     return self.chooseDefendAction(gameState)
        # (Eliminating the annotation symbols above can achieve attack defense conversion)
        return self.chooseAttackAction(gameState)

class AgentD(DummyAgent):
    def chooseAction(self, gameState):
        # if DummyAgent.X == 1:
        #     return self.chooseAttackAction(gameState)
        # (Eliminating the annotation symbols above can achieve attack defense conversion)
        return self.chooseDefendAction(gameState)


class PositionSearchProblem:

    def __init__(self, gameState, goal, agentIndex = 0, dangerPos=[], costFn=lambda x: 1):
        self.walls = gameState.getWalls().copy()
        for (x, y) in dangerPos:
            self.walls[x][y] = True
        self.costFn = costFn
        x, y = gameState.getAgentState(agentIndex).getPosition()
        self.startState = int(x), int(y)
        self.goal_pos = goal

    def getStartState(self):
        return self.startState

    def isGoalState(self, state):

        return state == self.goal_pos

    def getSuccessors(self, state):
        successors = []
        for action in [game.Directions.NORTH, game.Directions.SOUTH, game.Directions.EAST, game.Directions.WEST]:
            x, y = state
            dx, dy = game.Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

    def getCostOfActions(self, actions):
        if actions == None: return 999999
        x, y = self.getStartState()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = game.Actions.directionToVector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.costFn((x, y))
        return cost

    def _manhattanDistance(self, pos):
        return util.manhattanDistance(pos, self.goal_pos)
class AgentA(DummyAgent):
    def chooseAction(self, gameState):
        # if DummyAgent.X == 1:
        #     return self.chooseDefendAction(gameState)
        # (Eliminating the annotation symbols above can achieve attack defense conversion)
        return self.chooseAttackAction(gameState)

class AgentD(DummyAgent):
    def chooseAction(self, gameState):
        # if DummyAgent.X == 1:
        #     return self.chooseAttackAction(gameState)
        # (Eliminating the annotation symbols above can achieve attack defense conversion)
        return self.chooseDefendAction(gameState)


class PositionSearchProblem:

    def __init__(self, gameState, goal, agentIndex = 0, dangerPos=[], costFn=lambda x: 1):
        self.walls = gameState.getWalls().copy()
        for (x, y) in dangerPos:
            self.walls[x][y] = True
        self.costFn = costFn
        x, y = gameState.getAgentState(agentIndex).getPosition()
        self.startState = int(x), int(y)
        self.goal_pos = goal

    def getStartState(self):
        return self.startState

    def isGoalState(self, state):

        return state == self.goal_pos

    def getSuccessors(self, state):
        successors = []
        for action in [game.Directions.NORTH, game.Directions.SOUTH, game.Directions.EAST, game.Directions.WEST]:
            x, y = state
            dx, dy = game.Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

    def getCostOfActions(self, actions):
        if actions == None: return 999999
        x, y = self.getStartState()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = game.Actions.directionToVector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.costFn((x, y))
        return cost

    def _manhattanDistance(self, pos):
        return util.manhattanDistance(pos, self.goal_pos)

class AgentQ(CaptureAgent):

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)
        self.initializeTraining()
        self.boundary = self.getBoundary(gameState)
        self.current_target = None

    def initializeTraining(self, actions=None, learningRate=0.1, rewardDecay=1, Egreedy=0.9):
        if actions is None:
            actions = ["North", "South", "West", "East", "Stop"]
        self.act = actions
        self.lr = learningRate
        self.rd = rewardDecay
        self.Egreedy = Egreedy
        directory = 'agents/t_002'
        path = os.path.join(directory, 'weight.txt')
        if os.path.exists(path):
            with open(path) as data:
                self.weights = util.Counter(eval(data.readline().strip()))
        else:
            self.weights = util.Counter(
                {
                    "foodDis": 50,
                    "foodCarry": 100,
                    "foodLeft": 100,
                    "homeDis": 500,
                    "capsuleDis": 50,
                    "ghostDis": 200,
                    "teammateDis": -100,
                    "eatCapsule": 50,
                 })

    def getClosestPos(self, gameState, pos_list):
        min_length = 9999
        min_pos = None
        my_local_state = gameState.getAgentState(self.index)
        my_pos = my_local_state.getPosition()
        for pos in pos_list:
            temp_length = self.getMazeDistance(my_pos, pos)
            if temp_length < min_length:
                min_length = temp_length
                min_pos = pos
        return min_pos

    def getBoundary(self, gameState):
        boundary_location = []
        height = gameState.data.layout.height
        width = gameState.data.layout.width
        for i in range(height):
            if self.red:
                j = int(width / 2) - 1
            else:
                j = int(width / 2)
            if not gameState.hasWall(j, i):
                boundary_location.append((j, i))
        return boundary_location

    def chooseAction(self, gameState):

        global action
        if len(self.getFood(gameState).asList()) <= 2:
            self.current_target = self.getClosestPos(gameState, self.boundary)

        else:
            legal_actions = gameState.getLegalActions(self.index)
            Qvalue = [self.getFeatures(gameState, action)["features"] * self.weights for action in legal_actions]
            if np.random.uniform() < self.Egreedy:
                action = legal_actions[Qvalue.index(max(Qvalue))]
            else:
                action = np.random.choice(legal_actions)

        successor = gameState.generateSuccessor(self.index, action)
        reward = self.getFeatures(gameState, action)["reward"]
        self.Qlearning(gameState, action, reward, successor)
        return action

    def getHomeDis(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        return self.getMazeDistance(myPos, self.start) + 1

    def getFoodDis(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        foodDis = []
        for x, y in foodList:
            food = tuple((x, y))
            foodDis.append(self.getMazeDistance(food, myPos))
        return foodDis

    def getCapDis(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        capList = self.getCapsules(gameState)
        if capList != []:
            capDis = []
            for x, y in capList:
                cap = tuple((x, y))
                capDis.append(self.getMazeDistance(cap, myPos))
        else:
            capDis = [0.1]
        return capDis

    def getGhostDis(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        ghost = self.getOpponents(gameState)
        ghostDis = [9999]
        height = gameState.data.layout.height
        width = gameState.data.layout.width
        for y in range(height):
            for x in range(width):
                currPos = (x, y)
                for i in ghost:
                    if not gameState.getAgentState(i).isPacman:
                        ghostPos = gameState.getAgentPosition(i)
                    else:
                        ghostPos = None
                    if ghostPos is not None:
                        if currPos == myPos:
                            distance = self.getMazeDistance(ghostPos, myPos)
                            ghostDis.append(distance)
        return ghostDis

    def getTeamateDis(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        teammatePos = gameState.getAgentPosition((self.index+2)%4)
        return self.getMazeDistance(myPos,teammatePos)

    def getFeatures(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        successorPos = successor.getAgentPosition(self.index)
        successorState = successor.getAgentState(self.index)
        currentState = gameState.getAgentState(self.index)

        features = {
            "foodDis": min(self.getFoodDis(gameState)) - min(self.getFoodDis(successor)),
            "foodCarry": successorState.numCarrying - currentState.numCarrying,
            "foodLeft": len(self.getFood(gameState).asList()) - len(self.getFood(successor).asList()),
            "homeDis": self.getHomeDis(gameState) - self.getHomeDis(successor),
            "capsuleDis": min(self.getCapDis(gameState)) - min(self.getCapDis(successor)),
            "ghostDis": min(self.getGhostDis(successor)) - min(self.getGhostDis(gameState)),
            "teammateDis": self.getTeamateDis(gameState) - self.getTeamateDis(successor),
            "eatCapsule": len(self.getCapsules(gameState)) - len(self.getCapsules(successor)),

        }

        if successorState.numCarrying < 3 or min(self.getGhostDis(successor)) > 5 or not gameState.getAgentState(self.index).isPacman:
            features["homeDis"] = 0

        if min(self.getGhostDis(successor)) <= 5 or features["foodCarry"] < 0 or features["foodDis"] < -1:
            features["foodDis"] = 0

        if features["foodCarry"] < 0 and successorPos != successor.getInitialAgentPosition(self.index):
            features["foodCarry"] = -features["foodCarry"]

        if min(self.getGhostDis(successor)) > 5:
            features["eatCapsule"] = 0

        if successorPos == successor.getInitialAgentPosition(self.index):
            features["foodLeft"] = 0
            features["foodDis"] = 0

        if len(self.getFood(successor).asList()) <= 2:
            features["foodDis"] = 0

        if features["teammateDis"] > 4:
            teamWork = 10
        else:
            teamWork = 0

        if successorPos == successor.getInitialAgentPosition(self.index):
            beEatenReward = -500
        else:
            beEatenReward = 0

        if min(self.getGhostDis(successor)) < 10:
            surviveReward = 10 * successorState.numCarrying
        else:
            surviveReward = 0

        if successorState.isPacman:
            stayReward = 50
        else:
            stayReward = -50

        foodReward = -features["foodDis"] * 6

        total_reward = (stayReward - 5 * features["foodLeft"] + 40 * features["eatCapsule"] +
                        teamWork + beEatenReward + foodReward + surviveReward +
                        abs(successor.getScore() - gameState.getScore()) * 1000)

        return {"features": util.Counter(features), "reward": total_reward}

    def Qlearning(self, s, a, r, s_):
        state_data = s_.data
        is_loss, is_win = state_data._lose, state_data._win
        score_correction = self.lr * 1000 * self.getScore(s_)

        correction = score_correction if is_win else -abs(score_correction) if is_loss else 0
        if not correction:
            future_q_values = [self.computeQValue(s_, action) for action in s_.getLegalActions(self.index)]
            current_q_value = self.computeQValue(s, a)
            correction = self.lr * (r + self.rd * max(future_q_values, default=0) - current_q_value)

        print(f'Correction: {correction}')
        self.updateWeights(s, a, correction)

        print(f'Weights update: {self.weights}')
        # self.saveWeights()

    def computeQValue(self, state, action):
        features = self.getFeatures(state, action)["features"]
        return sum(self.weights[key] * value for key, value in features.items())

    def updateWeights(self, state, action, correction):
        features = self.getFeatures(state, action)["features"]
        updated_weights = {key: weight + correction * features.get(key, 0) for key, weight in self.weights.items()}
        self.weights.update(updated_weights)

    # def saveWeights(self):
    #     path = 'agents/t_002/weight.txt'
    #     with open(path, 'w') as file:
    #         file.write(str(self.weights))