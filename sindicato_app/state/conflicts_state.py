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