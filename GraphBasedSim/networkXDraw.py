import matplotlib.pyplot as plt
import networkx as nx

G = nx.DiGraph()

def add_edge(start = None, finish = None, weight = 1):
    G.add_edge(start, finish, weight=weight, len=20)
def drawGraph():

    elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 0.5]
    esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 0.5]
    pos = nx.spectral_layout(G)  # positions for all nodes - seed for reproducibility
    # nodes
    nx.draw_networkx_nodes(G, pos, node_size=700)
    # edges
    nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6,  arrows=True,  arrowsize=14, arrowstyle='-|>')
    nx.draw_networkx_edges(
        G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
    )
    # node labels
    nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")
    # edge weight labels
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels)
    ax = plt.gca()
    ax.margins(0.08)
    plt.axis("off")

    plt.show(block=False)
    plt.pause(5)
    plt.close()



