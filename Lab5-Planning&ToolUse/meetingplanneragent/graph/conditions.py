# Conditional logic for LangGraph
# Note: In the new architecture, routing logic is in nodes.py (_route_to_next_node)
# This file is kept for backward compatibility but is no longer used

def need_tools(state):
    """
    DEPRECATED: This function is no longer used in the new architecture.
    Routing logic is now in nodes._route_to_next_node
    """
    tools_to_use = state.get('tools_to_use', [])
    
    if tools_to_use:
        return "execute_tools"
    else:
        return "skip_tools"


def is_complete(state):
    """
    DEPRECATED: This function is no longer used in the new architecture.
    Routing logic is now in nodes._route_to_next_node
    """
    ready = state.get('ready_to_finalize', False)
    
    if ready:
        return "finalize"
    else:
        return "continue"