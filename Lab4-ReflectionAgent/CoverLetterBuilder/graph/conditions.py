# Conditional logic for LangGraph

def should_continue(state):
    """
    Decide if we should continue iterating or stop
    Returns: "continue" or "stop"
    """
    score = state['critiques'][-1]['overall_score']
    iteration = state['current_iteration']
    max_iter = state['max_iterations']
    threshold = state['quality_threshold']
    
    print(f"Decision: Score={score}, Iteration={iteration}/{max_iter}, Threshold={threshold}")
    
    if score >= threshold:
        state['stop_reason'] = 'quality_threshold'
        print(f"→ STOP: Quality threshold reached ({score} >= {threshold})")
        return "stop"
    
    elif iteration >= max_iter:
        state['stop_reason'] = 'max_iterations'
        print(f"→ STOP: Max iterations reached ({iteration} >= {max_iter})")
        return "stop"
    
    else:
        print(f"→ CONTINUE: Refining...")
        return "continue"