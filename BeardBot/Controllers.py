import math
import time
from rlbot.agents.base_agent import SimpleControllerState
from Util import *


def frugalController(agent, target, speed):
    controller_state = SimpleControllerState()
    location = toLocal(target, agent.me)
    angle_to_target = math.atan2(location.data[1], location.data[0])

    controller_state.steer = steer(angle_to_target)

    speed -= ((angle_to_target ** 2) * 300)
    current_speed = velocity2D(agent.me)
    if current_speed < speed:
        controller_state.throttle = 1.0
    elif current_speed - 50 > speed:
        controller_state.throttle = -1.0
    else:
        controller_state.throttle = 0

    time_difference = time.time() - agent.start
    if time_difference > 2.2 and distance2D(target, agent.me) > (velocity2D(agent.me) * 2.3) and abs(
            angle_to_target) < 0.9 and speed > current_speed > 220:
        agent.start = time.time()
    elif time_difference <= 0.1:
        controller_state.jump = True
        controller_state.pitch = -1
    elif 0.1 <= time_difference <= 0.15:
        controller_state.jump = False
        controller_state.pitch = -1
    elif 0.15 < time_difference < 1:
        controller_state.jump = True
        controller_state.yaw = controller_state.steer
        controller_state.pitch = -1

    return controller_state


def calcController(agent, target_object, target_speed):
    location = toLocal(target_object, agent.me)
    controller_state = SimpleControllerState()
    angle_to_ball = math.atan2(location.data[1], location.data[0])

    current_speed = velocity2D(agent.me)
    controller_state.steer = steer(angle_to_ball)
    r = radius(current_speed)
    cool = (Vector3([0, sign(location.data[1]) * (r + 40), 0]) - Vector3(
        [location.data[0], location.data[1], 0])).magnitude() / cap(r * 1.7, 1, 1200)
    if cool < 0.6:
        controller_state.handbrake = True
    else:
        controller_state.handbrake = False
    target_speed = cap(target_speed * cool, -target_speed, target_speed)

    # throttle
    if target_speed > current_speed:
        controller_state.throttle = 1.0
        if target_speed > 1400 and agent.start > 2.2 and current_speed < 2250:
            controller_state.boost = True
    elif target_speed < current_speed:
        controller_state.throttle = -1.0
    return controller_state


def shotController(agent, target_object, target_speed):
    goal_local = toLocal([0, -sign(agent.team) * FIELD_LENGTH / 2, 100], agent.me)
    goal_angle = math.atan2(goal_local.data[1], goal_local.data[0])
    location = toLocal(target_object, agent.me)
    controller_state = SimpleControllerState()
    angle_to_target = math.atan2(location.data[1], location.data[0])

    current_speed = velocity2D(agent.me)
    # steering
    controller_state.steer = steer(angle_to_target)
    r = radius(current_speed)
    cool = (Vector3([0, sign(location.data[1]) * (r + 40), 0]) - Vector3(
        [location.data[0], location.data[1], 0])).magnitude() / cap(r * 1.7, 1, 1200)
    if cool < 0.6:
        controller_state.handbrake = True
    else:
        controller_state.handbrake = False
    target_speed = cap(target_speed * cool, -target_speed, target_speed)

    # throttle
    if target_speed > 1400 and target_speed > current_speed and agent.start > 2.5 and current_speed < 2250:
        controller_state.boost = True
    if target_speed > current_speed:
        controller_state.throttle = 1.0
    elif target_speed < current_speed:
        controller_state.throttle = 0

    # dodging
    closing = distance2D(target_object, agent.me) / cap(
        -dpp(target_object, agent.ball.velocity, agent.me.location, agent.me.velocity), 1, 2300)
    time_difference = time.time() - agent.start
    if ballReady(agent) and time_difference > 2.2 and closing <= 0.4 and distance2D(agent.me, target_object) < 200:
        agent.start = time.time()
    elif time_difference <= 0.1:
        controller_state.jump = True
        controller_state.pitch = -1
    elif time_difference >= 0.1 and time_difference <= 0.15:
        controller_state.jump = False
        controller_state.pitch = -1
    elif time_difference > 0.15 and time_difference < 1:
        controller_state.jump = True
        controller_state.yaw = math.sin(goal_angle)
        controller_state.pitch = -abs(math.cos(goal_angle))

    return controller_state


def exampleController(agent, target_object, target_speed):
    location = toLocal(target_object, agent.me)
    controller_state = SimpleControllerState()
    angle_to_ball = math.atan2(location.data[1], location.data[0])

    current_speed = velocity2D(agent.me)
    # steering
    controller_state.steer = steer(angle_to_ball)

    # throttle
    if target_speed > current_speed:
        controller_state.throttle = 1.0
        if target_speed > 1400 and agent.start > 2.2 and current_speed < 2250:
            controller_state.boost = True
    elif target_speed < current_speed:
        controller_state.throttle = 0

    # dodging
    time_difference = time.time() - agent.start
    if time_difference > 2.2 and distance2D(target_object, agent.me) > (velocity2D(agent.me) * 2.5) and abs(
            angle_to_ball) < 1.3:
        agent.start = time.time()
    elif time_difference <= 0.1:
        controller_state.jump = True
        controller_state.pitch = -1
    elif time_difference >= 0.1 and time_difference <= 0.15:
        controller_state.jump = False
        controller_state.pitch = -1
    elif time_difference > 0.15 and time_difference < 1:
        controller_state.jump = True
        controller_state.yaw = controller_state.steer
        controller_state.pitch = -1

    return controller_state
