from ete4 import Tree

t = Tree(open("demo1.tree"))
t = Tree()
t.explore(keep_server=True, open_browser=False)