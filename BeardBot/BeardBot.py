import math
import time
from Util import *
from States import *

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

# For clarity, in the RLBot framework agent is referring to the bot, thus the two are synonymous.
# Any instance of agent is referring to BeardBot.

class BeardBot(BaseAgent):

    # Basically the init method. As stated above, BeardBot is an agent. The RLBot framework has already
    # initialized the agent "as a safety measure" -RLBot wiki
    def initialize_agent(self):
        self.me = obj()
        self.ball = obj()
        self.players = []  # holds other players in match
        self.start = time.time()

        self.state = calcShot()
        self.controller = calcController

    # Where it is checked if there is an active state. If not a new one is picked.
    def checkState(self):
        if self.state.expired:
            if calcShot().available(self):
                self.state = calcShot()
            elif quickShot().available(self):
                self.state = quickShot()
            elif wait().available(self):
                self.state = wait()
            else:
                self.state = quickShot()

    def get_output(self, game: GameTickPacket) -> SimpleControllerState:
        self.preprocess(game)
        self.checkState()
        return self.state.execute(self)

    # REQUIRED STEP. Cuts down on a lot of typing and helps standardize data throughout program.
    def preprocess(self, game):
        self.players = []
        car = game.game_cars[self.index]
        self.me.location.data = [car.physics.location.x, car.physics.location.y, car.physics.location.z]
        self.me.velocity.data = [car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z]
        self.me.rotation.data = [car.physics.rotation.pitch, car.physics.rotation.yaw, car.physics.rotation.roll]
        self.me.rvelocity.data = [car.physics.angular_velocity.x, car.physics.angular_velocity.y,
                                  car.physics.angular_velocity.z]
        self.me.matrix = rotator_to_matrix(self.me)
        self.me.boost = car.boost

        ball = game.game_ball.physics
        self.ball.location.data = [ball.location.x, ball.location.y, ball.location.z]
        self.ball.velocity.data = [ball.velocity.x, ball.velocity.y, ball.velocity.z]
        self.ball.rotation.data = [ball.rotation.pitch, ball.rotation.yaw, ball.rotation.roll]
        self.ball.rvelocity.data = [ball.angular_velocity.x, ball.angular_velocity.y, ball.angular_velocity.z]

        self.ball.local_location = to_local(self.ball, self.me)

        # collects info for all other cars in match, updates objects in self.players accordingly
        for i in range(game.num_cars):
            if i != self.index:
                car = game.game_cars[i]
                temp = obj()
                temp.index = i
                temp.team = car.team
                temp.location.data = [car.physics.location.x, car.physics.location.y, car.physics.location.z]
                temp.velocity.data = [car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z]
                temp.rotation.data = [car.physics.rotation.pitch, car.physics.rotation.yaw, car.physics.rotation.roll]
                temp.rvelocity.data = [car.physics.angular_velocity.x, car.physics.angular_velocity.y,
                                       car.physics.angular_velocity.z]
                self.me.boost = car.boost
                flag = False
                for item in self.players:
                    if item.index == i:
                        item = temp
                        flag = True
                        break
                if flag:
                    self.players.append(temp)


