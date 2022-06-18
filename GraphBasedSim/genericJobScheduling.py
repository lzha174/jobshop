import simpy
from GraphBasedSim.networkXDraw import  *

def g2():
    add_edge('A', 'B', 1)
    add_edge('B', 'C', 1)
    add_edge('C', 'T', 1)
    add_edge('A', 'D', 1)
    add_edge('D', 'T', 1)

def g1():
    add_edge('A', 'B', 1)
    add_edge('B', 'C', 1)
    add_edge('C', 'T', 1)
    add_edge('A', 'D', 1)
    add_edge('D', 'T', 1)

def g3():
    add_edge('A', 'B', 1)
    add_edge('B', 'D', 1)
    add_edge('A', 'C', 1)
    add_edge('C', 'D', 1)
    add_edge('A', 'E', 1)
    add_edge('D', 'T', 1)
    add_edge('E', 'T', 1)

g3()



# now can I create correct scheduling based on this graph?

# start a subprocess for A,C, start a sub process for B, yield on all, start on D
# how do I acheive that?
x = G.in_edges('D')
y = G.out_edges('A')
print(x)
print(y)

# find start edges
# edge without incoming edges
mergeNodes = {}
startNodes = []
for n in G.nodes():

    z = G.in_edges(n)
    if len(z) > 1:
        mergeNodes[n] = z

    if len(z) == 0:
        print(f' start node is {n}')
        startNodes.append(n)
# need to explore subprocess
print(mergeNodes)
# sub path end at a merge node

env = simpy.Environment()

print('try get sub path')
for node in mergeNodes:
    for path in nx.all_simple_paths(G, source='A', target=node):
        print(path)
    # these two process can go at same time

dependentEventDict = {}
eventsArray = {}
for node in G.nodes():
    dependentEventDict[node] = []
    eventsArray[node] = []
    for incoming in G.in_edges(node):
        finishEvent = env.event()
        dependentEventDict[node].append([incoming[0], finishEvent])
        eventsArray[node].append(finishEvent)
print(dependentEventDict)
print(eventsArray)
# how to start an event when all previous depending events are finsihed?

def nodeProcess(env: simpy.Environment, node):
    print(f'try do {node} at time {env.now}')
    # for each node, all predessors need to finish before continue
    yield env.all_of(eventsArray[node])
    print(f' I can do this event {node} at time {env.now}')
    duration = 1
    if node == 'T': duration = 0
    yield env.timeout(duration)
    print(f'finish this event {node} at time {env.now}')
    # if another node depends this node to fnish, notify that node this node is finished
    for key, eventList in dependentEventDict.items():
        if (len(eventList) == 0): continue
        for event in eventList:
            if node == event[0]:
                print(f' for node {key}, the predecesso event {node} is done')
                event[1].succeed()

nodes = ['A', 'B']
for node in G.nodes():
    env.process(nodeProcess(env, node))

env.run()


drawGraph()