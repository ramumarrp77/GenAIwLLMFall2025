"""
Long-term memory management with Neo4j knowledge graph
Hierarchical structure: Ram -> Restaurant -> Dish -> Ingredient
"""

from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from typing import List, Dict
import config


class LongTermMemoryManager:
    """
    Manages long-term memory by extracting entities to Neo4j
    Preserves full semantic relationships: Ram -> Restaurant -> Dish -> Ingredients
    """
    
    def __init__(self, graph: Neo4jGraph, llm):
        self.graph = graph
        self.llm = llm
        
        # Initialize graph transformer for entity extraction
        self.transformer = LLMGraphTransformer(
            llm=llm,
            allowed_nodes=["Restaurant", "Dish", "Cuisine", "Location", "Ingredient"],
            allowed_relationships=[
                "SERVES",           # Restaurant -> Dish
                "CONTAINS",         # Dish -> Ingredient
                "LOCATED_IN",       # Restaurant -> Location
                "HAS_CUISINE",      # Restaurant -> Cuisine
                "HAS_PROPERTY"      # For attributes like "spicy", "sweet"
            ],
            strict_mode=True,
            ignore_tool_usage=True
        )
    
    def should_extract(self, user_message: str, bot_response: str) -> bool:
        """
        Check if conversation contains food/restaurant information worth extracting
        """
        
        combined_text = f"User: {user_message}\nAssistant: {bot_response}"
        
        # Quick heuristic check first (fast)
        food_keywords = [
            'restaurant', 'ate', 'food', 'dish', 'cuisine', 'meal',
            'breakfast', 'lunch', 'dinner', 'rating', 'delicious',
            'tried', 'ordered', 'taste', 'flavor', 'cafe', 'bakery'
        ]
        
        has_keywords = any(keyword in combined_text.lower() for keyword in food_keywords)
        
        if not has_keywords:
            return False
        
        # LLM check for confirmation (slower but accurate)
        prompt = f"""Does this conversation contain specific information about restaurants, dishes, or food preferences that should be saved to memory?

Conversation:
{combined_text}

Answer with just 'YES' or 'NO':"""
        
        response = self.llm.invoke(prompt).strip().upper()
        
        return 'YES' in response
    
    def extract_and_store(self, user_message: str, bot_response: str) -> dict:
        """
        Extract entities from conversation and store in Neo4j
        Preserves hierarchical relationships
        """
        
        combined_text = f"{user_message}\n{bot_response}"
        
        try:
            # Extract using LLMGraphTransformer
            doc = Document(page_content=combined_text)
            graph_docs = self.transformer.convert_to_graph_documents([doc])
            
            if not graph_docs or not graph_docs[0].nodes:
                return {
                    "extracted": False,
                    "entities": [],
                    "relationships": []
                }
            
            # Store ALL extracted relationships in Neo4j
            # This preserves Restaurant->SERVES->Dish, Dish->CONTAINS->Ingredient
            self.graph.add_graph_documents(
                graph_docs,
                baseEntityLabel=True,
                include_source=False
            )
            
            # Link Ram to top-level entities only
            self._link_ram_to_top_entities(graph_docs[0])
            
            return {
                "extracted": True,
                "entities": [f"{node.type}: {node.id}" for node in graph_docs[0].nodes],
                "relationships": [
                    f"{rel.source.id} -[{rel.type}]-> {rel.target.id}" 
                    for rel in graph_docs[0].relationships
                ]
            }
            
        except Exception as e:
            return {
                "extracted": False,
                "error": str(e),
                "entities": [],
                "relationships": []
            }
    
    def _link_ram_to_top_entities(self, graph_doc):
        """
        Link Ram only to top-level entities
        Fixed: Removed last_visit, only use date property
        """
        
        for node in graph_doc.nodes:
            if node.type == "Restaurant":
                # Ram ate at this restaurant
                # Fixed: Only set date on CREATE, don't try to update non-existent last_visit
                self.graph.query("""
                MERGE (u:User {name: $user})
                MERGE (r:Restaurant {id: $restaurant})
                MERGE (u)-[rel:ATE_AT]->(r)
                ON CREATE SET rel.date = datetime()
                """, params={"user": config.USER_NAME, "restaurant": node.id})
            
            elif node.type == "Cuisine":
                # Ram prefers this cuisine
                self.graph.query("""
                MERGE (u:User {name: $user})
                MERGE (c:Cuisine {id: $cuisine})
                MERGE (u)-[rel:PREFERS]->(c)
                """, params={"user": config.USER_NAME, "cuisine": node.id})
            
            elif node.type == "Location":
                # Ram visited this location
                self.graph.query("""
                MERGE (u:User {name: $user})
                MERGE (l:Location {id: $location})
                MERGE (u)-[rel:VISITED]->(l)
                ON CREATE SET rel.date = datetime()
                """, params={"user": config.USER_NAME, "location": node.id})
    
    def query_memory(self, query_type: str, **kwargs) -> List[dict]:
        """
        Query the knowledge graph with hierarchical relationships
        """
        
        if query_type == "all_restaurants":
            # Fixed: Removed last_visit reference
            return self.graph.query("""
            MATCH (u:User {name: $user})-[r:ATE_AT]->(rest:Restaurant)
            RETURN rest.id as restaurant, r.date as date
            ORDER BY r.date DESC
            """, params={"user": config.USER_NAME})
        
        elif query_type == "all_dishes":
            # Query through restaurant hierarchy
            return self.graph.query("""
            MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant)-[:SERVES]->(d:Dish)
            RETURN DISTINCT d.id as dish, 
                   collect(DISTINCT r.id) as restaurants
            """, params={"user": config.USER_NAME})
        
        elif query_type == "dishes_at_restaurant":
            restaurant = kwargs.get('restaurant', '')
            return self.graph.query("""
            MATCH (r:Restaurant {id: $restaurant})-[:SERVES]->(d:Dish)
            OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
            RETURN d.id as dish, 
                   collect(DISTINCT i.id) as ingredients
            """, params={"restaurant": restaurant})
        
        elif query_type == "dish_ingredients":
            dish = kwargs.get('dish', '')
            return self.graph.query("""
            MATCH (d:Dish {id: $dish})-[:CONTAINS]->(i:Ingredient)
            RETURN i.id as ingredient
            """, params={"dish": dish})
        
        elif query_type == "favorites":
            return self.graph.query("""
            MATCH (u:User {name: $user})-[:PREFERS]->(c:Cuisine)
            RETURN c.id as cuisine
            """, params={"user": config.USER_NAME})
        
        elif query_type == "by_cuisine":
            cuisine = kwargs.get('cuisine', '')
            return self.graph.query("""
            MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant)-[:HAS_CUISINE]->(c:Cuisine)
            WHERE c.id = $cuisine OR toLower(c.id) CONTAINS toLower($cuisine)
            RETURN DISTINCT r.id as restaurant
            """, params={"user": config.USER_NAME, "cuisine": cuisine})
        
        elif query_type == "by_location":
            location = kwargs.get('location', '')
            return self.graph.query("""
            MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant)-[:LOCATED_IN]->(l:Location)
            WHERE l.id = $location OR toLower(l.id) CONTAINS toLower($location)
            RETURN DISTINCT r.id as restaurant, l.id as location
            """, params={"user": config.USER_NAME, "location": location})
        
        elif query_type == "recent":
            limit = kwargs.get('limit', 5)
            return self.graph.query("""
            MATCH (u:User {name: $user})-[r:ATE_AT]->(rest:Restaurant)
            RETURN rest.id as restaurant, r.date as date
            ORDER BY r.date DESC
            LIMIT $limit
            """, params={"user": config.USER_NAME, "limit": limit})
        
        elif query_type == "stats":
            result = self.graph.query("""
            MATCH (u:User {name: $user})
            OPTIONAL MATCH (u)-[:ATE_AT]->(r:Restaurant)
            WITH u, count(DISTINCT r) as restaurants
            OPTIONAL MATCH (u)-[:ATE_AT]->(:Restaurant)-[:SERVES]->(d:Dish)
            WITH u, restaurants, count(DISTINCT d) as dishes
            OPTIONAL MATCH (u)-[:PREFERS]->(c:Cuisine)
            RETURN restaurants, dishes, count(DISTINCT c) as cuisines
            """, params={"user": config.USER_NAME})
            
            if result:
                return result[0]
            return {"restaurants": 0, "dishes": 0, "cuisines": 0}
        
        elif query_type == "restaurant_full_details":
            restaurant = kwargs.get('restaurant', '')
            return self.graph.query("""
            MATCH (r:Restaurant {id: $restaurant})
            OPTIONAL MATCH (r)-[:SERVES]->(d:Dish)
            OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
            OPTIONAL MATCH (r)-[:LOCATED_IN]->(l:Location)
            OPTIONAL MATCH (r)-[:HAS_CUISINE]->(c:Cuisine)
            RETURN r.id as restaurant,
                   collect(DISTINCT d.id) as dishes,
                   collect(DISTINCT i.id) as ingredients,
                   collect(DISTINCT l.id) as locations,
                   collect(DISTINCT c.id) as cuisines
            """, params={"restaurant": restaurant})
        
        return []
    
    def get_graph_visualization_data(self) -> List[dict]:
        """
        Get data for graph visualization - includes hierarchical relationships
        """
        
        result = self.graph.query("""
        MATCH (u:User {name: $user})-[r]->(n)
        RETURN u.name as source, 
               type(r) as relationship, 
               coalesce(n.id, n.name) as target, 
               labels(n)[0] as target_type
        UNION
        MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant)-[rel]->(n)
        RETURN r.id as source,
               type(rel) as relationship,
               coalesce(n.id, n.name) as target,
               labels(n)[0] as target_type
        UNION
        MATCH (u:User {name: $user})-[:ATE_AT]->(:Restaurant)-[:SERVES]->(d:Dish)-[rel]->(n)
        RETURN d.id as source,
               type(rel) as relationship,
               coalesce(n.id, n.name) as target,
               labels(n)[0] as target_type
        LIMIT 100
        """, params={"user": config.USER_NAME})
        
        return result
    
    def search_by_ingredient(self, ingredient: str) -> List[dict]:
        """Find dishes with specific ingredient"""
        return self.graph.query("""
        MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant)
              -[:SERVES]->(d:Dish)-[:CONTAINS]->(i:Ingredient)
        WHERE toLower(i.id) CONTAINS toLower($ingredient)
        RETURN r.id as restaurant, d.id as dish, i.id as ingredient
        """, params={"user": config.USER_NAME, "ingredient": ingredient})
    
    def get_full_path(self, restaurant: str) -> List[dict]:
        """Get complete path: Ram -> Restaurant -> Dishes -> Ingredients"""
        return self.graph.query("""
        MATCH (u:User {name: $user})-[:ATE_AT]->(r:Restaurant {id: $restaurant})
        OPTIONAL MATCH (r)-[:SERVES]->(d:Dish)
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        RETURN r.id as restaurant, 
               collect(DISTINCT d.id) as dishes,
               collect(DISTINCT i.id) as ingredients
        """, params={"user": config.USER_NAME, "restaurant": restaurant})