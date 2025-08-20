from typing import List, Dict, Optional
from dataclasses import dataclass, field
from state.base import ReactiveValue

@dataclass
class ConflictsState:
    """State management for conflicts view"""

    conflicts: List[Dict] = field(default_factory=list)
    selected_conflict_id: ReactiveValue = field(default_factory=lambda: ReactiveValue())
    selected_conflict: Optional[Dict] = None
    history: List[Dict] = field(default_factory=list)

    def set_conflicts(self, conflicts: List[Dict]):
        """Set conflicts list"""
        self.conflicts = conflicts

    def set_selected_conflict(self, conflict: Optional[Dict]):
        """Set selected conflict"""
        self.selected_conflict = conflict
        if conflict:
            self.selected_conflict_id.set(conflict.get('id'))
        else:
            self.selected_conflict_id.set(None)

    def set_history(self, history: List[Dict]):
        """Set conflict history"""
        self.history = sorted(
            history,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

    def get_conflict_by_id(self, conflict_id: int) -> Optional[Dict]:
        """Get conflict by ID"""
        return next(
            (c for c in self.conflicts if c['id'] == conflict_id),
            None
        )

    def get_conflict_options(self) -> Dict[int, str]:
        """Get conflict options for select dropdown"""
        options = {}
        for conflict in self.conflicts:
            descripcion = (
                conflict.get('descripcion') or
                conflict.get('causa') or
                'Sin descripción'
            )
            desc_preview = (
                descripcion[:50] + "..."
                if len(descripcion) > 50
                else descripcion
            )
            label = f"ID {conflict['id']}: {desc_preview}"
            if conflict.get('fecha_apertura'):
                label += f" ({conflict['fecha_apertura']})"
            options[conflict['id']] = label
        return options

    def can_add_diario_conflicto(self, conflict: Optional[Dict]) -> bool:
        """
        Determine if a diario_conflicto can be added for the given conflict.

        Logic:
        - diario_conflicto can be added if:
          - The conflict has an 'afiliada_id' (i.e., it's related to an 'Afiliada').
          - The conflict is not closed (assuming there's a 'estado' field where 'Cerrado' means closed).

        :param conflict: The conflict dictionary, typically from the selected_conflict.
        :return: True if diario_conflicto can be added, False otherwise.
        """
        if not conflict:
            return False

        # Check if the conflict has an 'afiliada_id' and is not closed
        return (
            conflict.get('afiliada_id') is not None and
            conflict.get('estado') != 'Cerrado'
        )

# Example usage in your view logic:
# from state.conflicts_state import ConflictsState
# conflicts_state = ConflictsState()
# if conflicts_state.can_add_diario_conflicto(selected_conflict):
#     # Show diario_conflictos UI
# else:
#     # Hide or disable diario_conflictos UI