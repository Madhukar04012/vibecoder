"""
DB Schema Agent - Generates SQLAlchemy models from architecture

Input: Planner output (modules, features)
Output: SQLAlchemy models + relationship definitions

Deterministic. No AI calls. Pure logic.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


# ========== TYPES ==========

class Column(BaseModel):
    name: str
    type: str  # string, integer, boolean, datetime, text, foreign_key
    nullable: bool = False
    primary_key: bool = False
    unique: bool = False
    default: Optional[str] = None
    foreign_key: Optional[str] = None  # "table.column"


class Table(BaseModel):
    name: str
    columns: List[Column]
    relationships: List[str] = []  # ["users", "posts"]


class SchemaOutput(BaseModel):
    tables: List[Table]
    orm_models: bool = True
    migration_ready: bool = True


# ========== COMMON PATTERNS ==========

# Standard columns every table gets
BASE_COLUMNS = [
    Column(name="id", type="integer", primary_key=True),
    Column(name="created_at", type="datetime", default="datetime.utcnow"),
    Column(name="updated_at", type="datetime", nullable=True),
]

# Common module → table mappings
MODULE_TABLE_PATTERNS = {
    "authentication": [
        Table(
            name="users",
            columns=[
                *BASE_COLUMNS,
                Column(name="email", type="string", unique=True),
                Column(name="password_hash", type="string"),
                Column(name="name", type="string"),
                Column(name="is_active", type="boolean", default="True"),
            ],
            relationships=[]
        )
    ],
    "auth": [  # Alias for authentication
        Table(
            name="users",
            columns=[
                *BASE_COLUMNS,
                Column(name="email", type="string", unique=True),
                Column(name="password_hash", type="string"),
                Column(name="name", type="string"),
                Column(name="is_active", type="boolean", default="True"),
            ],
            relationships=[]
        )
    ],
    "users": [
        Table(
            name="users",
            columns=[
                *BASE_COLUMNS,
                Column(name="email", type="string", unique=True),
                Column(name="password_hash", type="string"),
                Column(name="name", type="string"),
                Column(name="is_active", type="boolean", default="True"),
            ],
            relationships=[]
        )
    ],
    "blog": [  # Blog = posts
        Table(
            name="posts",
            columns=[
                *BASE_COLUMNS,
                Column(name="title", type="string"),
                Column(name="content", type="text"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="published", type="boolean", default="False"),
            ],
            relationships=["users"]
        )
    ],
    "articles": [  # Articles = posts
        Table(
            name="posts",
            columns=[
                *BASE_COLUMNS,
                Column(name="title", type="string"),
                Column(name="content", type="text"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="published", type="boolean", default="False"),
            ],
            relationships=["users"]
        )
    ],
    "posts": [
        Table(
            name="posts",
            columns=[
                *BASE_COLUMNS,
                Column(name="title", type="string"),
                Column(name="content", type="text"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="published", type="boolean", default="False"),
            ],
            relationships=["users"]
        )
    ],
    "todos": [  # Alias for tasks
        Table(
            name="todos",
            columns=[
                *BASE_COLUMNS,
                Column(name="title", type="string"),
                Column(name="description", type="text", nullable=True),
                Column(name="completed", type="boolean", default="False"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id", nullable=True),
            ],
            relationships=["users"]
        )
    ],
    "comments": [
        Table(
            name="comments",
            columns=[
                *BASE_COLUMNS,
                Column(name="content", type="text"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="post_id", type="foreign_key", foreign_key="posts.id"),
            ],
            relationships=["users", "posts"]
        )
    ],
    "projects": [
        Table(
            name="projects",
            columns=[
                *BASE_COLUMNS,
                Column(name="name", type="string"),
                Column(name="description", type="text", nullable=True),
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="status", type="string", default="'active'"),
            ],
            relationships=["users"]
        )
    ],
    "tasks": [
        Table(
            name="tasks",
            columns=[
                *BASE_COLUMNS,
                Column(name="title", type="string"),
                Column(name="description", type="text", nullable=True),
                Column(name="completed", type="boolean", default="False"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id", nullable=True),
                Column(name="project_id", type="foreign_key", foreign_key="projects.id", nullable=True),
            ],
            relationships=["users", "projects"]
        )
    ],
    "dashboard": [],  # No tables, just views
    "settings": [
        Table(
            name="settings",
            columns=[
                *BASE_COLUMNS,
                Column(name="key", type="string", unique=True),
                Column(name="value", type="text"),
                Column(name="user_id", type="foreign_key", foreign_key="users.id", nullable=True),
            ],
            relationships=["users"]
        )
    ],
    "payments": [
        Table(
            name="subscriptions",
            columns=[
                *BASE_COLUMNS,
                Column(name="user_id", type="foreign_key", foreign_key="users.id"),
                Column(name="plan", type="string"),
                Column(name="status", type="string", default="'active'"),
                Column(name="stripe_id", type="string", nullable=True),
                Column(name="expires_at", type="datetime", nullable=True),
            ],
            relationships=["users"]
        )
    ],
}


# ========== DB SCHEMA AGENT ==========

class DBSchemaAgent:
    """
    Generates SQLAlchemy models from architecture output.
    Deterministic keyword-based schema generation.
    """
    
    def __init__(self, architecture: Dict[str, Any]):
        self.architecture = architecture
        self.modules = architecture.get("modules", [])
    
    def generate_schema(self) -> SchemaOutput:
        """Main entry point - generates schema from architecture"""
        tables = []
        seen_tables = set()
        
        for module in self.modules:
            module_lower = module.lower()
            
            # Check if module has predefined tables
            if module_lower in MODULE_TABLE_PATTERNS:
                for table in MODULE_TABLE_PATTERNS[module_lower]:
                    if table.name not in seen_tables:
                        tables.append(table)
                        seen_tables.add(table.name)
        
        # Ensure users table exists if any FK references it
        if "users" not in seen_tables:
            for table in tables:
                for col in table.columns:
                    if col.foreign_key and "users.id" in col.foreign_key:
                        tables.insert(0, MODULE_TABLE_PATTERNS["users"][0])
                        seen_tables.add("users")
                        break
        
        return SchemaOutput(
            tables=tables,
            orm_models=True,
            migration_ready=True
        )
    
    def generate_sqlalchemy_code(self) -> str:
        """Generate SQLAlchemy model Python code"""
        schema = self.generate_schema()
        
        code_lines = [
            '"""',
            'SQLAlchemy Models - Auto-generated by VibeCober DB Schema Agent',
            '"""',
            '',
            'from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey',
            'from sqlalchemy.orm import relationship, declarative_base',
            'from datetime import datetime',
            '',
            'Base = declarative_base()',
            '',
        ]
        
        for table in schema.tables:
            code_lines.append(self._generate_model_class(table))
            code_lines.append('')
        
        return '\n'.join(code_lines)
    
    def _generate_model_class(self, table: Table) -> str:
        """Generate a single SQLAlchemy model class"""
        class_name = self._to_class_name(table.name)
        
        lines = [
            f'class {class_name}(Base):',
            f'    __tablename__ = "{table.name}"',
            '',
        ]
        
        # Generate columns
        for col in table.columns:
            lines.append(f'    {self._generate_column(col)}')
        
        # Generate relationships
        if table.relationships:
            lines.append('')
            for rel in table.relationships:
                rel_class = self._to_class_name(rel)
                lines.append(f'    # Relationship to {rel_class}')
        
        # Add repr
        lines.append('')
        lines.append(f'    def __repr__(self):')
        lines.append(f'        return f"<{class_name}(id={{self.id}})>"')
        
        return '\n'.join(lines)
    
    def _generate_column(self, col: Column) -> str:
        """Generate a single column definition"""
        type_map = {
            'integer': 'Integer',
            'string': 'String(255)',
            'text': 'Text',
            'boolean': 'Boolean',
            'datetime': 'DateTime',
            'foreign_key': 'Integer',
        }
        
        col_type = type_map.get(col.type, 'String(255)')
        
        parts = [f'{col.name} = Column({col_type}']
        
        if col.foreign_key:
            parts.append(f', ForeignKey("{col.foreign_key}")')
        
        if col.primary_key:
            parts.append(', primary_key=True')
        
        if col.unique:
            parts.append(', unique=True')
        
        if col.nullable:
            parts.append(', nullable=True')
        
        if col.default:
            if col.type == 'datetime':
                parts.append(f', default={col.default}')
            else:
                parts.append(f', default={col.default}')
        
        parts.append(')')
        
        return ''.join(parts)
    
    def _to_class_name(self, table_name: str) -> str:
        """Convert table_name to ClassName"""
        # users -> User, project_tasks -> ProjectTask
        parts = table_name.split('_')
        return ''.join(part.capitalize() for part in parts)


# ========== PUBLIC API ==========

def db_schema_agent(architecture: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for orchestrator.
    
    Args:
        architecture: Output from planner agent
        
    Returns:
        Dict with schema JSON and generated code
    """
    agent = DBSchemaAgent(architecture)
    schema = agent.generate_schema()
    code = agent.generate_sqlalchemy_code()
    
    return {
        "schema": schema.model_dump(),
        "code": code,
        "tables_count": len(schema.tables),
        "status": "success"
    }


# ========== EXAMPLE USAGE ==========

if __name__ == "__main__":
    # Test with sample architecture
    sample_architecture = {
        "project_type": "Web Application",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "modules": ["authentication", "users", "posts", "comments"]
    }
    
    result = db_schema_agent(sample_architecture)
    
    print("=" * 60)
    print("SCHEMA OUTPUT:")
    print("=" * 60)
    print(f"Tables: {result['tables_count']}")
    for table in result['schema']['tables']:
        print(f"  - {table['name']} ({len(table['columns'])} columns)")
    
    print("\n" + "=" * 60)
    print("GENERATED CODE:")
    print("=" * 60)
    print(result['code'])
