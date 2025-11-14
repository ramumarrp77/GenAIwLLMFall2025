"""
Neo4j connection and graph operations
"""

from langchain_neo4j import Neo4jGraph
import config


def get_neo4j_graph():
    """Get Neo4j graph connection"""
    
    graph = Neo4jGraph(
        url=config.NEO4J_URI,
        username=config.NEO4J_USERNAME,
        password=config.NEO4J_PASSWORD
    )
    
    # Initialize Ram's user node if doesn't exist
    graph.query("""
    MERGE (u:User {name: $user_name})
    """, params={"user_name": config.USER_NAME})
    
    return graph


def initialize_schema(graph: Neo4jGraph):
    """Create constraints and indexes for the knowledge graph"""
    
    # Constraints
    constraints = [
        "CREATE CONSTRAINT restaurant_name IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT dish_name IF NOT EXISTS FOR (d:Dish) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT cuisine_type IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.type IS UNIQUE",
        "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            graph.query(constraint)
        except Exception as e:
            # Constraint might already exist
            pass
    
    print("✅ Neo4j schema initialized")