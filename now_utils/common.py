from attrs import define
from enum import Enum


class Variable:
    class Direction(Enum):
        IN = 0
        OUT = 1
    class Type(Enum):
        SCALAR = 0
        VECTOR = 1
    class VectorType(Enum):
        ASCENDING = 0
        DESCENDING = 1


@define
class Entity:
    name: str = None
    port_name: str = None
    direction: Variable.Direction = None
    var_type: Variable.Type = None
    vector_type: Variable.VectorType = None
    vector_size: int = None

    def __str__(self):
        dir_str = "IN" if self.direction == Variable.Direction.IN else "OUT"
        type_str = "std_logic_vector" if self.var_type == Variable.Type.VECTOR else "std_logic"
        var_len = f', {self.vector_size}' if self.var_type == Variable.Type.VECTOR else ""
        return f'{self.port_name:40} -> {self.name:40}, {dir_str}, {type_str}{var_len}'
