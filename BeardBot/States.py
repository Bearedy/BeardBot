# All states contained here. Where the actual game logic happens.

from Controllers import *


# A state that has the goal of taking a calculated shot
# A line is drawn from each of the opponent's goal posts through the balls position. This makes a cone on the
# other side. Hitting the ball straight on from inside the cone will send it at the opponent's net, usually...
# Logic: if you are inside the cone, hit the ball. else get inside the cone.
# This state alone was enough to beat the built in All Star bot.
class calcShot:
    def __init__(self):
        self.expired = False

    # Checks if this state is usable, conditions being the ball and BeardBot are in a possible scoring position
    def available(self, agent):
        if ballReady(agent) and abs(agent.ball.location.data[1]) < 5050 and (
                (ballProject(agent) > 400 + (velocity2D(agent.me))) or (
                distance2D(agent.me, agent.ball) > velocity2D(agent.me) and ballProject(agent) > 300)):
            return True
        return False

    # Actual work of the state, where the logic happens
    def execute(self, agent):
        agent.controller = calcController

        # getting the coordinates of the goalposts
        left_post = Vector3([-sign(agent.team) * 700, 5100 * -sign(agent.team), 200])
        right_post = Vector3([sign(agent.team) * 700, 5100 * -sign(agent.team), 200])
        center = Vector3([0, 5150 * -sign(agent.team), 200])

        # time stuff that I haven't implemented yet. The fact that guess is forced
        # to 0 means this doesn't actually do anything right now
        time_guess = 0
        bloc = future(agent.ball, time_guess)

        # vectors from the goalposts to the ball & to BeardBot
        ball_left = angle2(bloc, left_post)
        ball_right = angle2(bloc, right_post)
        agent_left = angle2(agent.me, left_post)
        agent_right = angle2(agent.me, right_post)

        # determining if we are left/right/inside of cone
        if agent_left > ball_left and agent_right > ball_right:
            goal_target = right_post
        elif agent_left > ball_left and agent_right < ball_right:
            goal_target = None
        elif agent_left < ball_left and agent_right < ball_right:
            goal_target = left_post
        else:
            goal_target = None

        # if we are outside the cone
        if goal_target is not None:
            agent_to_ball = (agent.ball.location - goal_target).normalize()
            goal_to_agent = (agent.me.location - goal_target).normalize()
            difference = agent_to_ball - goal_to_agent
            error = cap(abs(difference.data[0]) + abs(difference.data[1]), 1, 10)
        else:
            # if we are inside the cone, our line to follow is a vector from the ball to us
            agent_to_ball = (agent.me.location - agent.ball.location).normalize()
            error = cap(distance2D(bloc, agent.me) / 1000, 0, 1)

        test_vector = ROTATE * agent_to_ball

        # Distance calculation
        target_distance = cap((40 + distance2D(agent.ball.location, agent.me) * (error ** 2)) / 1.8, 0, 4000)
        target_location = agent.ball.location + Vector3(
            [(agent_to_ball.data[0] * target_distance), agent_to_ball.data[1] * target_distance, 0])

        # this adjusts the target based on the ball velocity perpendicular to the direction we're trying to hit it
        multiplier = cap(distance2D(agent.me, target_location) / 1500, 0, 2)
        target_mod_distance = cap((test_vector * agent.ball.velocity) * multiplier, -1000, 1000)
        final_mod_vector = Vector3(
            [test_vector.data[0] * target_mod_distance, test_vector.data[1] * target_mod_distance, 0])
        pre_loc = target_location
        target_location += final_mod_vector

        # another target adjustment that applies if the ball is close to the wall
        extra = 3850 - abs(target_location.data[0])
        if extra < 0:
            # we prevent our target from going outside the wall, and extend it so that BeardBot gets
            # closer to the wall before taking a shot, makes things more reliable
            target_location.data[0] = cap(target_location.data[0], -3850, 3850)
            target_location.data[1] = target_location.data[1] + (-sign(agent.team) * cap(extra, -800, 800))

        # getting speed, this would be a good thing to change in the future because it's not very good
        target_local = toLocal(target_location, agent.me)
        angle_to_target = cap(math.atan2(target_local.data[1], target_local.data[0]), -3, 3)
        distance_to_target = distance2D(agent.me, target_location)
        if distance_to_target > 2.5 * velocity2D(agent.me):
            speed = 2300
        else:
            speed = 2300 - (340 * (angle_to_target ** 2))

        # picking our rendered target color based on the speed we want to go
        colorRed = cap(int((speed / 2300) * 255), 0, 255)
        colorBlue = cap(255 - colorRed, 0, 255)

        # rendering (drawing) lines from the posts to the ball and one from the ball to the target
        agent.renderer.begin_rendering()
        agent.renderer.draw_line_3d(bloc.data, left_post.data, agent.renderer.create_color(255, 255, 0, 0))
        agent.renderer.draw_line_3d(bloc.data, right_post.data, agent.renderer.create_color(255, 0, 255, 0))

        agent.renderer.draw_line_3d(agent.ball.location.data, pre_loc.data,
                                    agent.renderer.create_color(255, colorRed, 0, colorBlue))
        agent.renderer.draw_line_3d(pre_loc.data, target_location.data,
                                    agent.renderer.create_color(255, colorRed, 0, colorBlue))
        agent.renderer.draw_rect_3d(target_location.data, 10, 10, True,
                                    agent.renderer.create_color(255, colorRed, 0, colorBlue))
        agent.renderer.end_rendering()

        if ballReady(agent) is False or abs(agent.ball.location.data[1]) > 5050:
            self.expired = True
        return agent.controller(agent, target_location, speed)


# A very simple and fast hit on the ball if we are close to it, aka "clearing the ball".
# it tries to hit it towards the opponent's goal, but unlike calcShot will hit the ball even if its not a good shot.
class quickShot:
    def __init__(self):
        self.expired = False

    # checks if BeardBot is a reasonable distance from the ball in relation to how close the
    # ball is to the opponent's goal, and if it can get to the ball fast. A little arbitrary right now.
    def available(self, agent):
        if ballProject(agent) > -1 * distance2D(agent.me, agent.ball) and timeZ(agent.ball) < 1.5:
            return True
        return False

    # Where the logic of the state happens
    def execute(self, agent):
        left_post = Vector3([-sign(agent.team) * 700, 5100 * -sign(agent.team), 200])
        right_post = Vector3([sign(agent.team) * 700, 5100 * -sign(agent.team), 200])

        ball_left = angle2(agent.ball.location, left_post)
        ball_right = angle2(agent.ball.location, right_post)
        agent_left = angle2(agent.me, left_post)
        agent_right = angle2(agent.me, right_post)

        if agent_left > ball_left and agent_right > ball_right:
            goal_target = left_post
        elif agent_left > ball_left and agent_right < ball_right:
            goal_target = None
        elif agent_left < ball_left and agent_right < ball_right:
            goal_target = right_post
        else:
            goal_target = None

        if goal_target is not None:
            goal_to_ball = (agent.ball.location - goal_target).normalize()
        else:
            goal_to_ball = (agent.me.location - agent.ball.location).normalize()

        test_vector = ROTATE * goal_to_ball
        target_distance = cap(distance2D(agent.ball.location, agent.me) / 4, 0, 1000)
        target_location = agent.ball.location + Vector3(
            [(goal_to_ball.data[0] * target_distance), goal_to_ball.data[1] * target_distance, 0])

        multiplier = cap(distance2D(agent.me, target_location) / 1500, 0, 2)
        target_mod_distance = cap((test_vector * agent.ball.velocity) * multiplier, -1000, 1000)
        final_mod_vector = Vector3(
            [test_vector.data[0] * target_mod_distance, test_vector.data[1] * target_mod_distance, 0])
        target_location += final_mod_vector

        location = toLocal(target_location, agent.me)
        angle_to_target = math.atan2(location.data[1], location.data[0])
        distance_to_target = distance2D(agent.me, target_location)

        if distance_to_target > 2.5 * velocity2D(agent.me):
            speed = 2300
        else:
            speed = 2300 - (340 * (angle_to_target ** 2))

        agent.controller = shotController

        if not self.available(agent):
            self.expired = True
        if calcShot().available(agent):
            self.expired = True


        agent.renderer.begin_rendering()
        agent.renderer.draw_line_3d(agent.ball.location.data, left_post.data,
                                    agent.renderer.create_color(255, 255, 0, 0))
        agent.renderer.draw_line_3d(agent.ball.location.data, right_post.data,
                                    agent.renderer.create_color(255, 0, 255, 0))
        agent.renderer.draw_line_3d(agent.ball.location.data, target_location.data,
                                    agent.renderer.create_color(255, 0, 255, 255))
        agent.renderer.end_rendering()

        return agent.controller(agent, target_location, speed)


# BeardBot uses this state if the ball is in a spot we cant hit it, as BeardBot doesn't know how to fly yet.
# Logic: If the ball is too high to hit right now, grab boost if we need it. Otherwise go to where we think the ball
# is going to land.
class wait():
    def __init__(self):
        self.expired = False

    def available(self, agent):
        if timeZ(agent.ball) > 2:
            return True

    def execute(self, agent):
        # taking a rough guess at where the ball will be in the future, based on how long it will take to hit the ground
        ball_future = future(agent.ball, timeZ(agent.ball))

        # if we are low on boost, we'll go for boost
        if agent.me.boost < 35:
            closest = 0
            closest_distance = distance2D(boosts[0], ball_future)

            # going through every large pad to see which one is closest to our ball_future guesstimation
            for i in range(1, len(boosts)):
                if distance2D(boosts[i], ball_future) < closest_distance:
                    closest = i
                    closest_distance = distance2D(boosts[i], ball_future)

            target = boosts[closest]
            speed = 2300
        # if we have boost, we just go towards the ball_future position, and slow down as we get close
        else:
            target = ball_future
            current = velocity2D(agent.me)
            ratio = distance2D(agent.me, target) / (current + 0.01)

            speed = cap(600 * ratio, 0, 2300)
        if speed <= 100:
            speed = 0

        if agent.ball.location.data[2] < 170:
            self.expired = True

        return frugalController(agent, target, speed)



# Mostly example code form the starter bot. Converted it to the state/controller system for testing. Not currently used.
class exampleATBA:
    def __init__(self):
        self.expired = False

    def execute(self, agent):
        target_location = agent.ball
        target_speed = velocity2D(agent.ball) + (distance2D(agent.ball, agent.me) / 1.5)

        return agent.controller(agent, target_location, target_speed)


