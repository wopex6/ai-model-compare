"""
Team Manager

Generalizes the "team" concept: a user can assemble ANY registered domain
characters (including the built-in deliberation agents) into a named team with
a chosen coordinator. Each team runs the same blind, coordinator-mediated
negotiation implemented by DeliberationTeam.

Persistence: `teams` table in the smart-response DB.

Reuses:
- CharacterManager      -> validates members exist, resolves display names
- DomainCharacterAI     -> real AI calls (budget-aware, free-exempt)
- DeliberationTeam      -> the orchestration engine (roster-driven)
- CharacterCollaborationSystem (optional) -> event logging
"""

import json
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

from .deliberation_team import (
    DeliberationTeam, TEAM_AGENT_IDS, COORDINATOR_ID
)

BUILTIN_TEAM_ID = "builtin_deliberation"


class TeamManager:
    """CRUD + execution for user-defined and built-in teams."""

    def __init__(self, db_connection: sqlite3.Connection, character_manager,
                 domain_character_ai, collaboration_system=None):
        self.db = db_connection
        self.manager = character_manager
        self.ai = domain_character_ai
        self.collaboration_system = collaboration_system
        self._init_table()
        self._seed_builtin()

    # ------------------------------------------------------------------
    # Schema / seeding
    # ------------------------------------------------------------------
    def _init_table(self):
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                owner_user_id INTEGER,
                member_ids TEXT NOT NULL,
                coordinator_id TEXT NOT NULL DEFAULT 'coordinator',
                mode TEXT NOT NULL DEFAULT 'blind',
                batch INTEGER NOT NULL DEFAULT 1,
                is_builtin INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teams_owner ON teams(owner_user_id)')
        self.db.commit()

    def _seed_builtin(self):
        """Create the built-in deliberation team if it doesn't exist."""
        cursor = self.db.cursor()
        cursor.execute('SELECT id FROM teams WHERE id = ?', (BUILTIN_TEAM_ID,))
        if cursor.fetchone():
            return
        cursor.execute('''
            INSERT INTO teams (id, name, description, owner_user_id, member_ids,
                               coordinator_id, mode, batch, is_builtin)
            VALUES (?, ?, ?, NULL, ?, ?, 'blind', 1, 1)
        ''', (
            BUILTIN_TEAM_ID,
            "Deliberation Team",
            "5 thinking-style agents (Contrarian, First-Principles, Expansionist, "
            "Outsider, Executor) that debate and negotiate a unified answer.",
            json.dumps(list(TEAM_AGENT_IDS)),
            COORDINATOR_ID,
        ))
        self.db.commit()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _registered_ids(self) -> set:
        return set(getattr(self.manager, 'characters', {}).keys())

    def _find_by_name(self, name: str, user_id: int, exclude_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        name = (name or '').strip().lower()
        if not name:
            return None
        cursor = self.db.cursor()
        sql = (
            'SELECT * FROM teams WHERE LOWER(name) = ? AND owner_user_id = ?'
            ' AND is_builtin = 0'
        )
        params = [name, user_id]
        if exclude_id:
            sql += ' AND id != ?'
            params.append(exclude_id)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def _validate_roster(self, member_ids: List[str], coordinator_id: str):
        """
        Returns (clean_members, clean_coordinator, error).
        Members must be registered characters, distinct from the coordinator,
        and number at least 2.
        """
        registered = self._registered_ids()
        coordinator_id = coordinator_id or COORDINATOR_ID
        if coordinator_id not in registered:
            return None, None, f"Coordinator '{coordinator_id}' is not a registered character."

        # De-dupe, preserve order, drop unknown ids and the coordinator itself
        seen = set()
        clean = []
        for mid in (member_ids or []):
            if mid in seen or mid == coordinator_id:
                continue
            if mid not in registered:
                return None, None, f"Unknown character '{mid}'."
            seen.add(mid)
            clean.append(mid)

        if len(clean) < 2:
            return None, None, "A team needs at least 2 distinct members (excluding the coordinator)."
        return clean, coordinator_id, None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def _row_to_dict(self, row) -> Dict[str, Any]:
        (tid, name, description, owner, member_json, coordinator_id, mode,
         batch, is_builtin, created_at, updated_at) = row
        member_ids = json.loads(member_json) if member_json else []
        registered = getattr(self.manager, 'characters', {})

        def display(cid):
            ch = registered.get(cid)
            return ch.display_name if ch else cid

        return {
            'id': tid,
            'name': name,
            'description': description or '',
            'owner_user_id': owner,
            'member_ids': member_ids,
            'members': [{'id': m, 'display_name': display(m)} for m in member_ids],
            'coordinator_id': coordinator_id,
            'coordinator_name': display(coordinator_id),
            'batch': bool(batch),
            'is_builtin': bool(is_builtin),
            'created_at': created_at,
            'updated_at': updated_at,
        }

    def list_teams(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return built-in teams plus the given user's teams."""
        cursor = self.db.cursor()
        if user_id is None:
            cursor.execute('SELECT * FROM teams WHERE is_builtin = 1 ORDER BY name')
        else:
            cursor.execute(
                'SELECT * FROM teams WHERE is_builtin = 1 OR owner_user_id = ? '
                'ORDER BY is_builtin DESC, name',
                (user_id,)
            )
        return [self._row_to_dict(r) for r in cursor.fetchall()]

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM teams WHERE id = ?', (team_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def create_team(self, user_id: int, name: str, member_ids: List[str],
                    description: str = '', coordinator_id: str = COORDINATOR_ID,
                    batch: bool = True) -> Dict[str, Any]:
        name = (name or '').strip()
        if not name:
            return {'error': 'Team name is required.'}
        existing = self._find_by_name(name, user_id)
        if existing:
            return {'error': f'You already have a team named "{name}".'}

        clean_members, clean_coord, err = self._validate_roster(member_ids, coordinator_id)
        if err:
            return {'error': err}

        team_id = f"team_{uuid.uuid4().hex[:12]}"
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO teams (id, name, description, owner_user_id, member_ids,
                               coordinator_id, mode, batch, is_builtin)
            VALUES (?, ?, ?, ?, ?, ?, 'blind', ?, 0)
        ''', (
            team_id, name, description.strip(), user_id,
            json.dumps(clean_members), clean_coord, 1 if batch else 0
        ))
        self.db.commit()
        return self.get_team(team_id)

    def update_team(self, team_id: str, user_id: int, is_admin: bool = False,
                    **fields) -> Dict[str, Any]:
        team = self.get_team(team_id)
        if not team:
            return {'error': 'Team not found.'}
        if team['is_builtin']:
            return {'error': 'Built-in teams cannot be modified.'}
        if team['owner_user_id'] != user_id and not is_admin:
            return {'error': 'You can only modify your own teams.'}

        name = fields.get('name', team['name'])
        description = fields.get('description', team['description'])
        batch = fields.get('batch', team['batch'])
        member_ids = fields.get('member_ids', team['member_ids'])
        coordinator_id = fields.get('coordinator_id', team['coordinator_id'])

        name = (name or '').strip()
        if not name:
            return {'error': 'Team name is required.'}
        existing = self._find_by_name(name, user_id, exclude_id=team_id)
        if existing:
            return {'error': f'You already have another team named "{name}".'}

        clean_members, clean_coord, err = self._validate_roster(member_ids, coordinator_id)
        if err:
            return {'error': err}

        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE teams SET name = ?, description = ?, member_ids = ?,
                   coordinator_id = ?, batch = ?, updated_at = ?
            WHERE id = ?
        ''', (
            name, (description or '').strip(), json.dumps(clean_members),
            clean_coord, 1 if batch else 0, datetime.now(), team_id
        ))
        self.db.commit()
        return self.get_team(team_id)

    def delete_team(self, team_id: str, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        team = self.get_team(team_id)
        if not team:
            return {'error': 'Team not found.'}
        if team['is_builtin']:
            return {'error': 'Built-in teams cannot be deleted.'}
        if team['owner_user_id'] != user_id and not is_admin:
            return {'error': 'You can only delete your own teams.'}
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM teams WHERE id = ?', (team_id,))
        self.db.commit()
        return {'success': True, 'deleted': team_id}

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def build_engine(self, team: Dict[str, Any]) -> DeliberationTeam:
        """Instantiate a roster-driven DeliberationTeam from a team dict."""
        return DeliberationTeam(
            character_manager=self.manager,
            domain_character_ai=self.ai,
            collaboration_system=self.collaboration_system,
            batch=team.get('batch', True),
            agent_ids=team.get('member_ids'),
            coordinator_id=team.get('coordinator_id', COORDINATOR_ID),
        )

    def run_team(self, team_id: str, message: str, user_id: Optional[int] = None,
                 reveal_attribution: bool = False, batch: Optional[bool] = None,
                 is_admin: bool = False, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Look up a team and run its deliberation."""
        team = self.get_team(team_id)
        if not team:
            return {'error': 'Team not found.'}
        engine = self.build_engine(team)
        result = engine.deliberate(
            message=message, context=context or {},
            reveal_attribution=reveal_attribution, user_id=user_id,
            batch=batch, is_admin=is_admin,
        )
        result['team_id'] = team_id
        result['team_name'] = team['name']
        return result


def create_team_manager(db_connection, character_manager, domain_character_ai,
                        collaboration_system=None) -> TeamManager:
    """Factory for a TeamManager."""
    return TeamManager(db_connection, character_manager, domain_character_ai,
                       collaboration_system)
