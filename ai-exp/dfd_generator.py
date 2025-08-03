import graphviz

# NOTE: Go to the official Graphviz download page and download the latest stable Windows installer (EXE) 
# for your system architecture (32-bit or 64-bit).

def parse_input(text):
    """
    Parses the input text into flow elements.
    :param text: str - Plain text defining the flow.
    :return: list - List of connections.
    """
    connections = []
    lines = text.strip().split("\n")
    for line in lines:
        if "->" in line:
            connections.append(tuple(map(str.strip, line.split("->"))))
    return connections

def generate_dfd(connections, output_file="dfd"):
    """
    Generates a Data Flow Diagram using Graphviz.
    :param connections: list - List of connections (tuples).
    :param output_file: str - Name of the output file.
    """
    graph = graphviz.Digraph(format='png', engine='dot')
    graph.attr(rankdir='LR')
   
    for connection in connections:
        if len(connection) == 2:
            graph.edge(connection[0], connection[1])
        elif len(connection) == 3:
            graph.edge(connection[0], connection[1], label=connection[2])

    # Render the graph
    graph.render(output_file, view=True)
    print(f"DFD generated: {output_file}.png")

if __name__ == "__main__":
    print("Enter your flow definition (use 'Entity -> Process -> Data Store' format):")
    user_input = """
    User -> Login Process
    Login Process -> Authentication Database
    Authentication Database -> Login Process
    Login Process -> Dashboard
    """
   
    # Parse input and generate diagram
    connections = parse_input(user_input)
    generate_dfd(connections, "data_flow_diagram")