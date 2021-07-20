import random
from shapely.geometry import Polygon

def poly_contains_poly(poly_a, poly_b):
    poly_a = Polygon(poly_a)
    poly_b = Polygon(poly_b)
    return poly_a.contains(poly_b)


def MAX_epsilon(problem, dat):
    figure_edges = problem['figure']['edges']
    figure_vertices = problem['figure']['vertices']

    max_epsilon = -1

    for i, j in figure_edges:
        x, y = figure_vertices[i]
        z, w = figure_vertices[j]

        dist1 = (x-z)**2+(y-w)**2

        x, y = dat[i]
        z, w = dat[j]

        if x==-1000 or y==-1000 or z==-1000 or w==-1000:
            continue

        dist2 = (x-z)**2+(y-w)**2
        max_epsilon = max(
            max_epsilon, (abs(dist2/dist1-1)) * 1000000)

    return max_epsilon


def check_contain(problem, dat):
    ep = 10**(-9)
    hole = problem['hole']
    figure_edges = problem['figure']['edges']

    poly_contain_flag = 1

    for i, j in figure_edges:
        x, y = dat[i]
        z, w = dat[j]

        if x==-1000 or y==-1000 or z==-1000 or w==-1000:
            continue

        for line in ([[x, y], [z, w], [(x+z)/2+ep, (y+w)/2]], [[x, y], [z, w], [(x+z)/2-ep, (y+w)/2]], [[x, y], [z, w], [(x+z)/2, (y+w)/2+ep]], [[x, y], [z, w], [(x+z)/2, (y+w)/2-ep]], [[x, y], [z, w], [(x+z)/2+ep, (y+w)/2+ep]], [[x, y], [z, w], [(x+z)/2+ep, (y+w)/2-ep]], [[x, y], [z, w], [(x+z)/2-ep, (y+w)/2+ep]], [[x, y], [z, w], [(x+z)/2-ep, (y+w)/2-ep]]):
            if poly_contains_poly(hole, line) == 1:
                break
        else:
            poly_contain_flag = 0

    if poly_contain_flag == 1:
        return True
    else:
        return False


def check_answer(problem, dat):
    epsilon = problem['epsilon']
    maxepsilon = MAX_epsilon(problem, dat)

    if maxepsilon <= epsilon and check_contain(problem, dat) == True:
        return True
    else:
        return False


# 以下、Problem 16 のチェック。
"""
problem = {'hole': [[0, 7], [22, 0], [36, 19], [22, 38], [0, 31]], 'epsilon': 8897, 'figure': {'edges': [
    [0, 1], [0, 2], [1, 3], [2, 4], [3, 4]], 'vertices': [[8, 6], [26, 22], [21, 25], [19, 0], [0, 14]]}}
dat = [[0, 7], [22, 0], [0, 31], [36, 19],  [22, 38]]


while True:
    random.shuffle(dat)

    if check_answer(problem, dat) == True:
        print(dat)
        break
    else:
        print(dat,MAX_epsilon(problem, dat))
"""
