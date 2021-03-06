import numpy as np
import math
import pygame
import time

w = 3
h = 3
index_list = np.load('symmetries/index_list' + str(h) + '_' + str(w) + '.npy')
reduced_index_list = list(set(index_list[:, 0]))


class Agent:

    def __init__(self, w, h, experience='', agent=True, learning=True, alpha=0.5, gamma=0.8, epsilon=0.1, policy='e-greedy'):
        self.agent = agent
        self.w = w
        self.h = h
        self.policy = policy
        self.learning = learning
        self.wallet = 0  # sum of rewards
        self.score = 0  # score in a dots and boxes match
        self.action = 0  # action
        self.state = 0
        self.previous_action = 0
        self.previous_state = 0
        self.Q = 0
        self.reduced_index_list = 0

        if experience:
            self.Q = np.load(experience)

        elif not agent:
            self.learning = False
            self.Q = 0

        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def choose_action(self, reduced_vector):  # epsilon-greedily
        print('choose action:')
        if self.policy == 'e-greedy':
            s = self.state
            print('state:', self.previous_state, self.state)
            print(s, self.Q[s], reduced_vector)
            self.Q[s, np.where(reduced_vector == 1)] = -10
            print(self.Q[s])
            if np.random.rand() < self.epsilon:
                a_index = np.where(reduced_vector != 1)[0]
            else:
                a_index = np.where(self.Q[s] == np.max(self.Q[s]))[0]

            print(a_index)
            self.previous_action = self.action
            self.action = a_index[np.random.randint(len(a_index))]
            print('action:', self.previous_action, self.action)

        elif self.policy == 'random':
            a_index = np.where(reduced_vector != 1)[0]
            self.previous_action = self.action
            self.action = a_index[np.random.randint(len(a_index))]

    def update_rule(self, reward, m):
        if self.learning:
            s0 = self.previous_state
            a0 = self.previous_action
            print(self.Q[s0, a0])
            print(s0, a0)
            self.Q[s0, a0] += self.alpha * (reward + self.gamma * m - self.Q[s0, a0])
            print(self.Q[s0, a0])
            print('next')

    def target(self, reduced_vector):
        return np.max(self.Q[self.state, np.where(reduced_vector != 1)])


class Game:

    def __init__(self, w, h, player1, player2, graphics=False, new=True):
        self.new = new
        self.w = w
        self.h = h
        self.dim = h * (w-1) + (h-1) * w

        self.total_score = (w-1) * (h-1)
        self.half_score = (w-1) * (h-1) / 2

        self.p = [player1, player2]
        self.learning = player1.agent or player2.agent

        self.state = [np.zeros((h, w - 1), dtype='int'), np.zeros((h - 1, w), dtype='int')]
        self.vector = vector_form(self.state)

        self.terminal_vector = np.ones(self.dim, dtype='int')
        self.terminal_index = enumerate(self.terminal_vector)
        self.reduced_vector = vectorize(0, self.dim)

        self.boxes = 2 * np.ones((h-1, w-1), dtype='int')
        self.turn = 0   # players indices
        self.scored = 0
        self.terminal_state = False
        self.extra_turn = False

        if player1.agent and player2.agent:
            self.graphics = graphics
        else:
            self.graphics = True

        if self.graphics:
            self.board = Board(self)

    def initialize_episode(self):
        self.p[0].score = 0
        self.p[1].score = 0

        self.state = [np.zeros((h, w - 1), dtype='int'), np.zeros((h - 1, w), dtype='int')]
        self.vector = vector_form(self.state)
        self.reduced_vector = vectorize(0, self.dim)

        self.boxes = 2 * np.ones((h-1, w-1), dtype='int')
        self.turn = 0   # players indices
        self.scored = 0
        self.terminal_state = False
        self.extra_turn = False

    def episode(self):  # player1 and player2 play n matches of dots and boxes
        self.initialize_episode()
        print(self.state)

        if not self.p[self.turn].agent:
            choice = self.board.choose_action()

        else:
            t0 = self.update()
            print(self.p[self.turn].state)
            print('turn:', self.turn)
            self.p[self.turn].choose_action(self.reduced_vector)
            choice = self.action(self.p[self.turn].action, t0)  # choose action

        # self.info(choice)
        if self.graphics:
            self.board.draw()

        self.move(choice)
        print(self.p[self.turn].state)
        print(self.state)

        self.turn = 1 - self.turn

        if not self.p[self.turn].agent:
            choice = self.board.choose_action()

        else:
            t1 = self.update()
            print('turn:', self.turn)
            self.p[self.turn].choose_action(self.reduced_vector)
            choice = self.action(self.p[self.turn].action, t1)  # choose action

        # self.info(choice)
        if self.graphics:
            self.board.draw()

        self.move(choice)
        print(self.p[self.turn].state)
        print(self.state)

        self.turn = 1 - self.turn

        while not self.terminal_state:

            if self.graphics:
                self.board.draw()
                time.sleep(1)

            if not self.p[self.turn].agent:
                choice = self.board.choose_action()

            else:
                t2 = self.update()
                print('turn:', self.turn)
                self.p[self.turn].choose_action(self.reduced_vector)
                choice = self.action(self.p[self.turn].action, t2)  # choose action
                # self.info(choice)

            self.move(choice)
            print(self.state)
            print(self.p[self.turn].state)

            if self.terminal_state:
                reward = self.reward()
                if self.turn != 0:
                    reward = -reward

                m = 0
                for turn in range(2):
                    # # print(self.p[0].Q)
                    self.p[turn].previous_state = self.p[turn].state
                    self.p[turn].previous_action = self.p[turn].action
                    self.p[turn].update_rule(reward, m)
                    # # print(self.p[0].Q)

            else:
                m = 0
                reward = 0
                if self.p[self.turn].learning:
                    m = self.p[self.turn].target(self.reduced_vector)

                # # print(self.p[0].Q)
                self.p[self.turn].update_rule(reward, m)
                s0 = self.p[self.turn].previous_state
                a0 = self.p[self.turn].previous_action
                # # print(self.p[0].Q)

                if not self.extra_turn:
                    self.turn = 1 - self.turn

    def reward(self):
        reward = 0

        if self.p[0].score > self.half_score:
            reward = 1
            if self.graphics:
                self.board.win = True

        elif self.p[0].score < self.half_score:
            reward = -1

        self.p[0].wallet += reward
        self.p[1].wallet -= reward

        if self.graphics:
            self.board.finished()

        return reward

    def move(self, choice):
        score = 0
        self.extra_turn = False
        h, x, y = choice

        self.state[h][x, y] = 1  # update state
        self.vector = vector_form(self.state)

        if h == 0:

            if x != 0:
                upper = self.state[0][x - 1, y] == 1
                upper_left = self.state[1][x - 1, y] == 1
                upper_right = self.state[1][x - 1, y + 1] == 1
                if upper and upper_left and upper_right:
                    score += 1
                    self.boxes[x-1, y] = self.turn

            if x != self.h - 1:
                lower = self.state[0][x + 1, y] == 1
                lower_left = self.state[1][x, y] == 1
                lower_right = self.state[1][x, y + 1] == 1
                if lower and lower_left and lower_right:
                    score += 1
                    self.boxes[x, y] = self.turn

        else:

            if y != 0:
                left = self.state[1][x, y - 1] == 1
                upper_left = self.state[0][x, y - 1] == 1
                lower_left = self.state[0][x + 1, y - 1] == 1
                if left and upper_left and lower_left:
                    score += 1
                    self.boxes[x, y-1] = self.turn

            if y != self.w - 1:
                right = self.state[1][x, y + 1] == 1
                upper_right = self.state[0][x, y] == 1
                lower_right = self.state[0][x + 1, y] == 1
                if right and lower_right and upper_right:
                    score += 1
                    self.boxes[x, y] = self.turn

        self.scored += score

        if self.scored == self.total_score:
            self.terminal_state = True

        if score != 0 and not self.terminal_state:
            self.extra_turn = True

        self.p[self.turn].score += score

    def update(self):
        s, t = index_list[enumerate(self.vector)]
        self.reduced_vector = vectorize(s, self.dim)
        self.state = matrix_form(self.vector, self.h, self.w)
        self.p[self.turn].previous_state = self.p[self.turn].state
        self.p[self.turn].state = reduced_index_list.index(s)
        return t

    def action(self, a, t):
        v = np.zeros(self.dim, dtype='int')
        v[a] = 1
        print('t:', t)
        arr_list = matrix_form(v, self.h, self.w)
        print(arr_list)

        h_arr, v_arr = transformation[t](arr_list)
        if np.sum(h_arr) == 1:
            h = 0
            i, j = np.where(h_arr == 1)
            x = i[0]
            y = j[0]
        else:
            h = 1
            i, j = np.where(v_arr == 1)
            x = i[0]
            y = j[0]

        return h, x, y

    def info(self, choice):
        print('state_array:', self.state)
        print('state_vector:', self.vector)
        print('reduced_state_vector:', self.reduced_vector)
        print('scores:', self.p[0].score, self.p[1].score)
        print('scored:', self.scored)
        print('turn and action:', self.turn, self.p[self.turn].action)
        print('choice', choice)


def enumerate(vector):
    return int("".join(str(v) for v in vector), 2)


def vectorize(num, dim):
    vector = np.zeros(dim, dtype='int')
    v = np.array([int(s) for s in bin(num)[2:]])
    vector[dim - np.size(v):] = v
    return vector


def vector_form(array_list):
    return np.concatenate((np.concatenate(array_list[0]), np.concatenate(array_list[1])))


def matrix_form(vector, h, w):
    a = h * (w-1)
    vector_list = [vector[:a], vector[a:]]
    array_list = [np.ndarray((h, w-1), dtype='int'), np.ndarray((h-1, w), dtype='int')]

    for i in range(w-1):
        array_list[0][:, i] = vector_list[0][i::(w-1)]

    for j in range(w):
        array_list[1][:, j] = vector_list[1][j::w]

    return array_list


def Symmetry_Group():

    # identity
    def id(arr_list):
        return arr_list

    # horizontal symmetry
    def hor(arr_list):
        return [arr_list[0][:, ::-1], arr_list[1][:, ::-1]]

    # vertical symmetry
    def ver(arr_list):
        return [arr_list[0][::-1], arr_list[1][::-1]]

    # 180 degree rotation:
    def r180(arr_list):
        return [arr_list[0][::-1, ::-1], arr_list[1][::-1, ::-1]]

    # diagonal symmetry if w = h
    def d1(arr_list):
        return [np.transpose(arr_list[1][::-1, ::-1]), np.transpose(arr_list[0][::-1, ::-1])]

    def d2(arr_list):
        return [np.transpose(arr_list[1]), np.transpose(arr_list[0])]

    def r90(arr_list):
        return [np.transpose(arr_list[1])[::-1], np.transpose(arr_list[0])[::-1]]

    def r270(arr_list):
        return [np.transpose(arr_list[1])[:, ::-1], np.transpose(arr_list[0])[:, ::-1]]

    def c1(arr_list):
        arr_list[0][0, 0], arr_list[1][0, 0] = arr_list[1][0, 0], arr_list[0][0, 0]
        return arr_list

    def c2(arr_list):
        arr_list[0][0, -1], arr_list[1][0, -1] = arr_list[1][0, -1], arr_list[0][0, -1]
        return arr_list

    def c3(arr_list):
        arr_list[0][-1, 0], arr_list[1][-1, 0] = arr_list[1][-1, 0], arr_list[0][-1, 0]
        return arr_list

    def c4(arr_list):
        arr_list[0][-1, -1], arr_list[1][-1, -1] = arr_list[1][-1, -1], arr_list[0][-1, -1]
        return arr_list

    return [id, hor, ver, r180, d1, d2, r90, r270, c1, c2, c3, c4]


transformation = Symmetry_Group()
inverse = [0, 1, 2, 3, 4, 5, 7, 6, 8, 9, 10, 11]
multiply = np.array([[0, 1, 2, 3, 4, 5, 6, 7],
                     [1, 0, 3, 2, 6, 7, 4, 5],
                     [2, 3, 0, 1, 7, 6, 5, 4],
                     [3, 2, 1, 0, 5, 4, 7, 6],
                     [4, 7, 6, 5, 0, 3, 2, 1],
                     [5, 6, 7, 4, 3, 0, 1, 2],
                     [6, 5, 4, 7, 1, 2, 3, 0],
                     [7, 4, 5, 6, 2, 1, 0, 3]])


class Board:

    def __init__(board, game):
        pass
        pygame.init()
        pygame.font.init()

        # initialize pygame clock
        board.clock = pygame.time.Clock()

        board.game = game

        board.w = game.w
        board.h = game.h

        if board.w < 8 and board.h < 8:
            board.width, board.height = 389, 489
        else:
            board.width = (board.w-1) * 64 + board.w
            board.height = board.width + 100

        # initialize the screen
        board.screen = pygame.display.set_mode((board.width, board.height))
        pygame.display.set_caption("Boxes")
        board.initGraphics()

        board.turn = True

        board.win = False

        board.indicator = [board.greenindicator, board.redindicator]
        board.distance = 64

    def initGraphics(board):
        board.normallinev = pygame.image.load("png_files/normalline.png")
        board.normallineh = pygame.transform.rotate(pygame.image.load("png_files/normalline.png"), -90)
        board.bar_donev = pygame.image.load("png_files/bar_done.png")
        board.bar_doneh = pygame.transform.rotate(pygame.image.load("png_files/bar_done.png"), -90)
        board.hoverlinev = pygame.image.load("png_files/hoverline.png")
        board.hoverlineh = pygame.transform.rotate(pygame.image.load("png_files/hoverline.png"), -90)
        board.separators = pygame.image.load("png_files/separators.png")
        board.redindicator = pygame.image.load("png_files/redindicator.png")
        board.greenindicator = pygame.image.load("png_files/greenindicator.png")
        board.marker = pygame.image.load("png_files/greenplayer.png")
        board.othermarker = pygame.image.load("png_files/redplayer.png")
        board.winningscreen = pygame.image.load("png_files/youwin.png")
        board.gameover = pygame.image.load("png_files/gameover.png")
        board.score_panel = pygame.image.load("png_files/score_panel.png")

    def drawBoard(board):
        for x in range(board.w-1):
            for y in range(board.h):
                if not board.game.state[0][y, x]:
                    board.screen.blit(board.normallineh, [(x) * board.distance + 5, (y) * board.distance])
                else:
                    board.screen.blit(board.bar_doneh, [(x) * board.distance + 5, (y) * board.distance])

        for x in range(board.w):
            for y in range(board.h-1):
                if not board.game.state[1][y, x]:
                    board.screen.blit(board.normallinev, [(x) * board.distance, (y) * board.distance + 5])
                else:
                    board.screen.blit(board.bar_donev, [(x) * board.distance, (y) * board.distance + 5])
        # draw separators
        for x in range(board.w):
            for y in range(board.h):
                board.screen.blit(board.separators, [x * board.distance, y * board.distance])

    def drawOwnermap(board):
        for x in range(board.w-1):
            for y in range(board.h-1):
                if board.game.boxes[y, x] != 2:
                    if board.game.boxes[y, x] == 0:
                        board.screen.blit(board.marker, (x * board.distance + 5, y * board.distance + 5))
                    if board.game.boxes[y, x] == 1:
                        board.screen.blit(board.othermarker, (x * board.distance + 5, y * board.distance + 5))

    def drawHUD(board):
        # draw the background for the bottom:
        board.screen.blit(board.score_panel, [int((board.width - 389)/2), board.width])

        # create font
        myfont = pygame.font.SysFont(None, 32)

        # create text surface
        label = myfont.render("Turn:", 1, (255, 255, 255))

        # draw surface
        board.screen.blit(label, (int((board.width - 389)/2)+10, board.height - 89))
        board.screen.blit(board.indicator[board.game.turn], (int((board.width - 389)/2)+170, board.height-94))
        # same thing here
        myfont64 = pygame.font.SysFont(None, 64)
        myfont20 = pygame.font.SysFont(None, 20)

        scoreme = myfont64.render(str(board.game.p[0].score), 1, (255, 255, 255))
        scoreother = myfont64.render(str(board.game.p[1].score), 1, (255, 255, 255))
        scoretextme = myfont20.render("Green Player", 1, (255, 255, 255))
        scoretextother = myfont20.render("Red Player", 1, (255, 255, 255))

        board.screen.blit(scoretextme, (int((board.width - 389)/2)+10, board.height-64))
        board.screen.blit(scoreme, (int((board.width - 389)/2)+10, board.height-54))
        board.screen.blit(scoretextother, (int((board.width - 389)/2)+280, board.height-64))
        board.screen.blit(scoreother, (int((board.width - 389)/2)+340, board.height-54))

    def choose_action(board):
        while True:
            # sleep to make the game 60 fps
            board.clock.tick(60)

            # clear the screen
            board.screen.fill(0)

            # draw the board
            board.drawBoard()
            board.drawHUD()
            board.drawOwnermap()

            for event in pygame.event.get():
                # quit if the quit button was pressed
                if event.type == pygame.QUIT:
                    exit()

                # 1
                mouse = pygame.mouse.get_pos()

                # 2
                xpos = int(math.ceil((mouse[0] - board.distance/2) / board.distance))
                ypos = int(math.ceil((mouse[1] - board.distance/2) / board.distance))

                # 3
                is_horizontal = abs(mouse[1] - ypos * board.distance) < abs(mouse[0] - xpos * board.distance)

                # 4
                ypos = ypos - 1 if mouse[1] - ypos * board.distance < 0 and not is_horizontal else ypos
                xpos = xpos - 1 if mouse[0] - xpos * board.distance < 0 and is_horizontal else xpos

                # 5
                Board = board.game.state[0] if is_horizontal else board.game.state[1]
                isoutofbounds = False

                # 6
                try:
                    if not Board[ypos, xpos]:
                        board.screen.blit(board.hoverlineh if is_horizontal else board.hoverlinev,
                                          [xpos * board.distance + 5 if is_horizontal else xpos * board.distance,
                                           ypos * board.distance if is_horizontal else ypos * board.distance + 5])

                except:
                    isoutofbounds = True
                    pass

                if not isoutofbounds:
                    alreadyplaced = Board[ypos, xpos]

                else:
                    alreadyplaced = False

                if pygame.mouse.get_pressed()[0] and not alreadyplaced and not isoutofbounds:
                    if is_horizontal:
                        pygame.display.flip()
                        return [0, ypos, xpos]
                    else:
                        pygame.display.flip()
                        return [1, ypos, xpos]

            # update the screen
            pygame.display.flip()

    def draw(board):
        board.clock.tick(60)

        # clear the screen
        board.screen.fill(0)

        # draw the board
        board.drawBoard()
        board.drawHUD()
        board.drawOwnermap()

        pygame.display.flip()

    def finished(board):
        board.drawBoard()
        board.drawHUD()
        board.drawOwnermap()
        board.screen.blit(board.gameover if not board.win else board.winningscreen, (0, 0))
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
            pygame.display.flip()


def self_training(theta, w, h):
    p1 = Agent(w, h)
    p2 = Agent(w, h)
    # print("Agents are ready")
    game = Game(w, h, p1, p2)
    # print(game.index_list)
    # print(len(game.reduced_index_list))
    # print("Game is set")
    p1.reduced_index_list = game.reduced_index_list
    p2.reduced_index_list = game.reduced_index_list
    Q = np.ones((len(game.reduced_index_list), game.dim))
    p1.Q = np.copy(Q)
    p2.Q = np.copy(Q)
    epsiode_counter = 0

    try:
        while epsiode_counter < 20:
            q = np.copy(p1.Q)
            game.episode()
            epsiode_counter += 1
            # print('round', epsiode_counter)
            Delta = np.max(abs(p1.Q - q))
            # print('delta:', Delta)

            if epsiode_counter % 10 == 9:
                if Delta < theta:
                    # print('converged')
                    break

    except KeyboardInterrupt:
        np.save('s-action_value_function.npy', p1.Q)

    np.save('action_value_function' + str(h) + '-' + str(w) + '.npy', Q)


def random_opponent(theta, w, h):
    p1 = Agent(w, h)
    p2 = Agent(w, h)
    # print("Agents are ready")
    game = Game(w, h, p1, p2)
    # print("Game is set")
    # print(game.index_list)
    p1.reduced_index_list = game.reduced_index_list
    p2.reduced_index_list = game.reduced_index_list
    Q = np.ones((len(game.reduced_index_list), game.dim))
    p1.Q = np.copy(Q)
    p2.Q = np.copy(Q)
    epsiode_counter = 0

    try:
        while epsiode_counter < 20:
            q = np.copy(p1.Q)
            game.episode()
            epsiode_counter += 1
            # print('round', epsiode_counter)
            Delta = np.max(abs(p1.Q - q))
            # print('delta:', Delta)

            if epsiode_counter % 10 == 9:
                if Delta < theta:
                    # print('converged')
                    break

    except KeyboardInterrupt:
        np.save('action_value_function.npy', p1.Q)

    np.save('r-action_value_function' + str(h) + '-' + str(w) + '.npy', Q)


p1 = Agent(w, h, agent=False)
p2 = Agent(w, h, experience='action_value_function/sh2-action_value_function3-3.npy', learning=False)
# print("Agents are ready")
game = Game(w, h, p1, p2)
# print(game.index_list)
# print(len(game.reduced_index_list))
# print("Game is set")

game.episode()
