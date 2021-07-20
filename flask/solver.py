from shapely.geometry import Polygon, LineString, Point
from copy import deepcopy
from check_answer import MAX_epsilon, check_answer
import requests
import json
import math
import sys
import numpy as np

sys.setrecursionlimit(100000)
np.random.seed(0)

ann_rate = 0.99
ann_rate_opt = 0.7


def get_problem(n):
    result = requests.get(f'{endpoint_get_problems}/{n}', headers=headers)
    return json.loads(result.text)


def submit(n, dat):
    dat = { 'vertices': dat }
    result = requests.post(f'{endpoint_submit}/{n}/solutions', json=dat, headers=headers)
    return result


def poly_contains_poly(poly_a, poly_b):
    poly_a = Polygon(poly_a)
    poly_b = Polygon(poly_b)
    return poly_a.contains(poly_b)


def rotate_all(vertices, rad, integer=True):
    centroid = get_centroid(vertices)
    new_vertices = deepcopy(vertices)
    sin = np.sin(rad)
    cos = np.cos(rad)
    for i in range(len(new_vertices)):
        dx = new_vertices[i][0] - centroid[0]
        dy = new_vertices[i][1] - centroid[1]
        ndx = cos*dx - sin*dy
        ndy = sin*dx + cos*dy
        if integer:
            new_vertices[i] = [round(ndx+centroid[0]), round(ndy+centroid[1])]
        else:
            new_vertices[i] = [ndx+centroid[0], ndy+centroid[1]]
    return new_vertices


def stretch(problem, vertices, n, dx, dy, epsilon):
    new_vertices = deepcopy(vertices)
    new_vertices[n] = [new_vertices[n][0]+dx, new_vertices[n][1]+dy]
    return new_vertices
    # valid = MAX_epsilon(problem, new_vertices)<epsilon
    # if valid:
        # return new_vertices
    # else:
        # return None


def translate(vertices, dx, dy):
    new_vertices = deepcopy(vertices)
    for i in range(len(new_vertices)):
        new_vertices[i] = [new_vertices[i][0]+dx, new_vertices[i][1]+dy]
    return new_vertices


def get_centroid(vertices):
    centroid = [0, 0]
    n = len(vertices)
    for v in vertices:
        centroid[0] += v[0]
        centroid[1] += v[1]
    centroid = [centroid[0]//n, centroid[1]//n]
    return centroid


def calculate_dislikes(problem, vertices):
    dislikes = 0
    for i in range(len(problem['hole'])):
        hx, hy = problem['hole'][i]
        m = 1e10
        for (vx, vy) in vertices:
            d = (hx-vx)**2 + (hy-vy)**2
            m = min(m, d)
        dislikes += m
    return dislikes


def flip(vertices, axis=0):
    centroid = get_centroid(vertices)
    new_vertices = deepcopy(vertices)
    for i in range(len(new_vertices)):
        dx = new_vertices[i][0] - centroid[0]
        dy = new_vertices[i][1] - centroid[1]
        dx = dx if axis==0 else -dx
        dy = dy if axis==1 else -dy
        new_vertices[i] = [dx+centroid[0], dy+centroid[1]]
    return new_vertices


isec_table = {}

def calc_intersection(hole, edges):
    hole = Polygon(hole)
    total = 0
    intersection = 0
    for line in edges:
        total += math.sqrt((line[0][0]-line[1][0])**2 + (line[0][1]-line[1][1])**2)
        key = str(line)
        if key in isec_table.keys():
            isecs = isec_table[key]
        else:
            line = LineString(line)
            isecs = hole.intersection(line)
            isec_table[key] = isecs
        if not isecs.is_empty:
            if isecs.geom_type.startswith('Multi') or isecs.geom_type=='GeometryCollection':
                for isec in isecs:
                    if isec.geom_type=='LineString':
                        (x0, y0), (x1, y1) = list(isec.coords)
                        intersection += math.sqrt((x0-x1)**2 + (y0-y1)**2)
            elif isecs.geom_type=='LineString':
                (x0, y0), (x1, y1) = list(isecs.coords)
                intersection += math.sqrt((x0-x1)**2 + (y0-y1)**2)
    return intersection / total


def calc_integer_ratio(vertices):
    n_int = 0
    for v in vertices:
        if float(v[0]).is_integer() and float(v[1]).is_integer():
            n_int += 1
    return n_int / len(vertices)


rotatable_vertices = []
flippable_pairs = []


def get_disjoint_unions(problem, vs):
    par = [i for i in range(len(problem['figure']['vertices']))]
    def find(x):
        if par[x]==x:
            return x
        par[x] = find(par[x])
        return par[x]
    def unite(x, y):
        x = find(x)
        y = find(y)
        if x==y:
            return 0
        par[x] = y
    for e in problem['figure']['edges']:
        if e[0] in vs or e[1] in vs:
            continue
        unite(e[0], e[1])
    unions = {}
    for i in range(len(par)):
        p = find(i)
        if p in vs:
            continue
        if p in unions.keys():
            unions[p].append(i)
        else:
            unions[p] = [i]
    return list(unions.values())


def init_rotatable_vertices(problem):
    global rotatable_vertices
    rotatable_vertices = [None for _ in range(len(problem['figure']['vertices']))]
    for i in range(len(problem['figure']['vertices'])):
        rotatable_vertices[i] = get_disjoint_unions(problem, [i])


def init_flippable_pairs(problem):
    global flippable_pairs
    flippable_pairs = [[None for _ in range(len(problem['figure']['vertices']))] for _ in range(len(problem['figure']['vertices']))]
    for i in range(len(problem['figure']['vertices'])):
        for j in range(len(problem['figure']['vertices'])):
            if i>=j:
                continue
            flippable_pairs[i][j] = get_disjoint_unions(problem, [i, j])


def get_initial_vertices(problem):
    hole_centroid = get_centroid(problem['hole'])
    fig_centroid = get_centroid(problem['figure']['vertices'])
    dx = hole_centroid[0] - fig_centroid[0]
    dy = hole_centroid[1] - fig_centroid[1]
    vertices = deepcopy(problem['figure']['vertices'])
    for i in range(len(vertices)):
        vertices[i] = [vertices[i][0]+dx, vertices[i][1]+dy]
    return vertices


def vertex_rotate(problem, vertices, v, n, rad, integer=True):
    rot_vertices = rotatable_vertices[v][n]
    new_vertices = deepcopy(vertices)
    sin = np.sin(rad)
    cos = np.cos(rad)
    for rv in rot_vertices:
        dx = vertices[rv][0] - vertices[v][0]
        dy = vertices[rv][1] - vertices[v][1]
        ndx = cos*dx - sin*dy
        ndy = sin*dx + cos*dy
        dx = ndx
        dy = ndy
        # if rot90==1:
            # tmp = dy
            # dy = dx
            # dx = -tmp
        # elif rot90==2:
            # dx = -dx
            # dy = -dy
        # else:
            # tmp = dy
            # dy = -dx
            # dx = tmp
        if integer:
            new_vertices[rv] = [round(vertices[v][0]+dx), round(vertices[v][1]+dy)]
        else:
            new_vertices[rv] = [vertices[v][0]+dx, vertices[v][1]+dy]
    return new_vertices


def pair_rotate(problem, vertices, p, n, integer=True):
    flip_pairs = flippable_pairs[p[0]][p[1]][n]
    new_vertices = deepcopy(vertices)
    l0 = np.asarray(vertices[p[0]])
    l1 = np.asarray(vertices[p[1]])
    for fv in flip_pairs:
        v = np.asarray(vertices[fv])
        a = l1 - l0
        b = v - l0
        if np.linalg.norm(b)==0 or np.linalg.norm(a)==0:
            r = [0, 0]
        else:
            cos = (a*b).sum() / np.linalg.norm(a) / np.linalg.norm(b)
            s = np.linalg.norm(b)*cos / np.linalg.norm(a)
            if np.isnan(cos):
                r = [0, 0]
            else:
                t = a * s
                r = (t - b) * 2
        if integer:
            new_vertices[fv] = [round(v[0]+r[0]), round(v[1]+r[1])]
        else:
            new_vertices[fv] = [v[0]+r[0], v[1]+r[1]]
    return new_vertices


def integerize(vertices, n, dx, dy):
    new_vertices = deepcopy(vertices)
    new_vertices[n] = [round(new_vertices[n][0]+dx), round(new_vertices[n][1]+dy)]
    return new_vertices


count = 0
sol_table = {}
best_isec = 0
best = None
search_max_count = 10

def find_feasible_solution(problem, prev_vertices, epsilon, depth=0, integer=True):
    global count
    global best_isec
    global best
    global search_max_count

    if count>search_max_count:
        return None

    vertices = deepcopy(prev_vertices)
    if integer:
        if check_answer(problem, vertices):
            return vertices
    else:
        if calc_integer_ratio(prev_vertices)==1 and check_answer(problem, vertices):
            return vertices
    key = str(prev_vertices)
    if key in sol_table.keys():
        current_intersection = sol_table[key]
    else:
        edges = list(map(lambda x: [vertices[x[0]], vertices[x[1]]], problem['figure']['edges']))
        if integer:
            current_intersection = calc_intersection(problem['hole'], edges)
        else:
            int_rate = calc_integer_ratio(vertices)
            current_intersection = calc_intersection(problem['hole'], edges)# * int_rate
    # if current_intersection<best_isec:
        # return None
    # best_isec = current_intersection
    count += 1
    if integer:
        print(current_intersection, depth)
    else:
        print(current_intersection, int_rate, depth)
    # rotation
    rotations = [
        flip(vertices, 1), flip(vertices, -1),
        rotate_all(vertices, np.pi, integer),
        rotate_all(vertices, np.pi/2, integer), rotate_all(vertices, -np.pi/2, integer),
        rotate_all(vertices, np.pi/4, integer), rotate_all(vertices, -np.pi/4, integer),
        rotate_all(vertices, np.pi/8, integer), rotate_all(vertices, -np.pi/8, integer),
        rotate_all(vertices, np.pi/16, integer), rotate_all(vertices, -np.pi/16, integer),
        rotate_all(vertices, np.pi/32, integer), rotate_all(vertices, -np.pi/32, integer),
        rotate_all(vertices, np.pi/64, integer), rotate_all(vertices, -np.pi/64, integer),
    ]

    # translate
    translations = [
        # translate(vertices, 160, 0), translate(vertices, -160, 0),
        # translate(vertices, 0, 160), translate(vertices, 0, -160),
        # translate(vertices, 128, 0), translate(vertices, -128, 0),
        # translate(vertices, 0, 128), translate(vertices, 0, -128),
        # translate(vertices, 96, 0), translate(vertices, -96, 0),
        # translate(vertices, 0, 96), translate(vertices, 0, -96),
        # translate(vertices, 64, 0), translate(vertices, -64, 0),
        # translate(vertices, 0, 64), translate(vertices, 0, -64),
        translate(vertices, 32, 0), translate(vertices, -32, 0),
        translate(vertices, 0, 32), translate(vertices, 0, -32),
        translate(vertices, 16, 0), translate(vertices, -16, 0),
        translate(vertices, 0, 16), translate(vertices, 0, -16),
        translate(vertices, 8, 0), translate(vertices, -8, 0),
        translate(vertices, 0, 8), translate(vertices, 0, -8),
        translate(vertices, 4, 0), translate(vertices, -4, 0),
        translate(vertices, 0, 4), translate(vertices, 0, -4),
        translate(vertices, 2, 0), translate(vertices, -2, 0),
        translate(vertices, 0, 2), translate(vertices, 0, -2),
        translate(vertices, 1, 0), translate(vertices, -1, 0),
        translate(vertices, 0, 1), translate(vertices, 0, -1),
    ]
    if not integer:
        translations.append(translate(vertices, 0.5, 0))
        translations.append(translate(vertices, 0, 0.5))
        translations.append(translate(vertices, -0.5, 0))
        translations.append(translate(vertices, 0, -0.5))
        translations.append(translate(vertices, 0.25, 0))
        translations.append(translate(vertices, 0, 0.25))
        translations.append(translate(vertices, -0.25, 0))
        translations.append(translate(vertices, 0, -0.25))

    # vertex rotation
    vrotations = []
    for v in range(len(vertices)):
        rot_vertices = rotatable_vertices[v]
        if len(rot_vertices)<2:
            continue
        for n in range(len(rot_vertices)):
            rvs = rot_vertices[n]
            if len(rvs)>max_rotatable_vertices:
                # too many vertices to be rotated
                continue
            for rad in [np.pi, np.pi/2, -np.pi/2]:
                rotate = vertex_rotate(problem, vertices, v, n, rad, integer)
                vrotations.append(rotate)
            if not integer:
                for rad in [np.pi/4, -np.pi/4, np.pi/8, -np.pi/8]:
                    rotate = vertex_rotate(problem, vertices, v, n, rad, integer)
                    vrotations.append(rotate)

    # pair rotation
    protations = []
    for i in range(len(vertices)):
        for j in range(i+1, len(vertices)):
            flip_pairs = flippable_pairs[i][j]
            if len(flippable_pairs)<2:
                continue
            for n in range(len(flip_pairs)):
                fvs = flip_pairs[n]
                if len(fvs)>max_flippable_vertices:
                    # too many vertices to be flipped
                    continue
                flp = pair_rotate(problem, vertices, (i, j), n, integer)
                protations.append(flp)

    # stretch
    sts = []
    hole_centroid = get_centroid(problem['hole'])
    poly_hole = Polygon(problem['hole'])
    for i in range(len(vertices)):
        out = not poly_hole.contains(Point(vertices[i]))
        stretches = [
            stretch(problem, vertices, i, 1, 0, epsilon), stretch(problem, vertices, i, -1, 0, epsilon),
            stretch(problem, vertices, i, 0, 1, epsilon), stretch(problem, vertices, i, 0, -1, epsilon),
        ]
        if not integer:
            stretches.append(stretch(problem, vertices, i, 0.5, 0, epsilon))
            stretches.append(stretch(problem, vertices, i, 0, 0.5, epsilon))
            stretches.append(stretch(problem, vertices, i, -0.5, 0, epsilon))
            stretches.append(stretch(problem, vertices, i, 0, -0.5, epsilon))
        for st in stretches:
            if st is None:
                continue
            sts.append(st)

    integerizations = None
    if not integer:
        integerizations = []
        for v in range(len(vertices)):
            for dx in [-0.5, 0.5]:
                for dy in [-0.5, 0.5]:
                    integerizations.append(integerize(vertices, v, dx, dy))

    tmp_best = prev_vertices
    tmp_best_isec = current_intersection
    cands = rotations + translations + vrotations + protations + sts
    if not integer:
        cands = cands + integerizations
    ann_trans = None
    ann_best = -1
    for cand in cands:
        if MAX_epsilon(problem, cand)>=epsilon:
            continue
        edges = list(map(lambda x: [cand[x[0]], cand[x[1]]], problem['figure']['edges']))
        if integer:
            intersection = calc_intersection(problem['hole'], edges)
        else:
            intersection = calc_intersection(problem['hole'], edges) * pow((1+calc_integer_ratio(cand))/2, 0.01)
        r_ann = np.random.uniform()
        if r_ann>ann_best:
            ann_best = r_ann
            ann_trans = cand
        if intersection>tmp_best_isec:
            tmp_best = cand
            tmp_best_isec = intersection

    if tmp_best_isec>current_intersection:
        if tmp_best_isec>best_isec:
            best_isec = tmp_best_isec
            best = tmp_best
        res = find_feasible_solution(problem, tmp_best, epsilon, depth+1, integer)
        if res is not None:
            return res

    if ann_best>ann_rate:
        res = find_feasible_solution(problem, ann_trans, epsilon, depth+1, integer)
        if res is not None:
            return res

    return None


best_sol = None
best_dislikes = 1e10
max_count = 100
opt_count = 0
searched = set()

max_rotatable_vertices = 30
max_flippable_vertices = 30

def optimize_solution(problem, prev_vertices, epsilon, depth=0):
    global opt_count
    global best_sol
    global best_dislikes
    global max_count
    global searched
    # if str(prev_vertices) in searched:
        # return best_sol
    # searched.add(str(prev_vertices))
    vertices = deepcopy(prev_vertices)
    current_dislikes = calculate_dislikes(problem, vertices)
    if current_dislikes<best_dislikes:
        best_dislikes = current_dislikes
        best_sol = deepcopy(vertices)
    opt_count += 1
    if opt_count>max_count:
        return best_sol
    print(current_dislikes, best_dislikes, depth, opt_count)

    # rotation
    rotations = [
        flip(vertices, 1), flip(vertices, -1),
        rotate_all(vertices, np.pi),
        rotate_all(vertices, np.pi/2), rotate_all(vertices, -np.pi/2),
        rotate_all(vertices, np.pi/4), rotate_all(vertices, -np.pi/4),
        rotate_all(vertices, np.pi/8), rotate_all(vertices, -np.pi/8),
        rotate_all(vertices, np.pi/16), rotate_all(vertices, -np.pi/16),
        rotate_all(vertices, np.pi/32), rotate_all(vertices, -np.pi/32),
        rotate_all(vertices, np.pi/64), rotate_all(vertices, -np.pi/64),
    ]

    # translate
    translations = [
        translate(vertices, 64, 0), translate(vertices, -64, 0),
        translate(vertices, 0, 64), translate(vertices, 0, -64),
        translate(vertices, 32, 0), translate(vertices, -32, 0),
        translate(vertices, 0, 32), translate(vertices, 0, -32),
        translate(vertices, 16, 0), translate(vertices, -16, 0),
        translate(vertices, 0, 16), translate(vertices, 0, -16),
        translate(vertices, 8, 0), translate(vertices, -8, 0),
        translate(vertices, 0, 8), translate(vertices, 0, -8),
        translate(vertices, 4, 0), translate(vertices, -4, 0),
        translate(vertices, 0, 4), translate(vertices, 0, -4),
        translate(vertices, 2, 0), translate(vertices, -2, 0),
        translate(vertices, 0, 2), translate(vertices, 0, -2),
        translate(vertices, 1, 0), translate(vertices, -1, 0),
        translate(vertices, 0, 1), translate(vertices, 0, -1),
    ]

    # vertex rotation
    vrotations = []
    for v in range(len(vertices)):
        rot_vertices = rotatable_vertices[v]
        if len(rot_vertices)<2:
            continue
        for n in range(len(rot_vertices)):
            rvs = rot_vertices[n]
            if len(rvs)>max_rotatable_vertices:
                # too many vertices to be rotated
                continue
            for rad in [np.pi, np.pi/2, -np.pi/2]:
                rotate = vertex_rotate(problem, vertices, v, n, rad)
                vrotations.append(rotate)

    # pair rotation
    protations = []
    for i in range(len(vertices)):
        for j in range(i+1, len(vertices)):
            flip_pairs = flippable_pairs[i][j]
            if len(flippable_pairs)<2:
                continue
            for n in range(len(flip_pairs)):
                fvs = flip_pairs[n]
                if len(fvs)>max_flippable_vertices:
                    # too many vertices to be flipped
                    continue
                flp = pair_rotate(problem, vertices, (i, j), n)
                protations.append(flp)

    # stretch
    hole_centroid = get_centroid(problem['hole'])
    poly_hole = Polygon(problem['hole'])
    sts = []
    for i in range(len(vertices)):
        out = not poly_hole.contains(Point(vertices[i]))
        stretches = [
            stretch(problem, vertices, i, 1, 0, epsilon), stretch(problem, vertices, i, -1, 0, epsilon),
            stretch(problem, vertices, i, 0, 1, epsilon), stretch(problem, vertices, i, 0, -1, epsilon),
            stretch(problem, vertices, i, 1, 1, epsilon), stretch(problem, vertices, i, 1, -1, epsilon),
            stretch(problem, vertices, i, -1, 1, epsilon), stretch(problem, vertices, i, -1, -1, epsilon),
        ]
        for st in stretches:
            if st is None:
                continue
            sts.append(st)

    tmp_best = prev_vertices
    tmp_best_dislikes = current_dislikes
    cands = rotations + translations + vrotations + protations + sts
    ann_trans = None
    ann_best = -1
    for cand in cands:
        if not check_answer(problem, cand):
            continue
        dislikes = calculate_dislikes(problem, cand)
        r_ann = np.random.uniform()
        if r_ann>ann_best:
            ann_best = r_ann
            ann_trans = cand
        if dislikes<tmp_best_dislikes:
            tmp_best = cand
            tmp_best_dislikes = dislikes

    if tmp_best_dislikes<current_dislikes:
        if tmp_best_dislikes<best_dislikes:
            best_dislikes = tmp_best_dislikes
            best_sol = tmp_best
            print(best_dislikes)
            print(best_sol)
        res = optimize_solution(problem, tmp_best, epsilon, depth+1)
        if res is not None:
            return res

    if ann_best>ann_rate_opt:
        res = optimize_solution(problem, ann_trans, epsilon, depth+1)
        if res is not None:
            return res

    # searched.add(str(prev_vertices))
    return best_sol


def solve(problem, vertices):
    global isec_table
    global rotatable_vertices
    global flippable_pairs

    global count
    global sol_table
    global best_isec
    global best

    global best_sol
    global best_dislikes
    global max_count
    global opt_count
    global searched

    best_sol = None
    best_dislikes = 1e10
    max_count = 100
    opt_count = 0
    searched = set()

    count = 0
    sol_table = {}
    best_isec = 0
    best = None

    rotatable_vertices = []
    flippable_pairs = []
    isec_table = {}
    init_rotatable_vertices(problem)
    init_flippable_pairs(problem)

    max_count = 10
    res = find_feasible_solution(problem, vertices, problem['epsilon'], 0, True)
    # return res
    if res is None:
        return vertices
    ref = optimize_solution(problem, res, problem['epsilon'])
    return ref
