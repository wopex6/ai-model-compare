"""
Admin Utilities for Agent Management

Provides tools to manage simulated user agents:
- Upgrade agent roles (guest → paid) for unlimited messaging
- Check agent status and quotas
- Reset agent message counts

Can work via API (with admin credentials) or direct DB access (local only).
"""

import requests
import sqlite3
import os
import sys
from typing import List, Dict, Optional, Tuple

# Simulated user names (must match simulated_users.py)
SIM_USER_NAMES = [
    'SimUser_Alex', 'SimUser_Maya', 'SimUser_Jordan', 
    'SimUser_Priya', 'SimUser_Marcus'
]


def upgrade_roles_via_db(db_path: str, role: str = 'paid') -> List[Dict]:
    """Upgrade simulated user roles directly in the database (local only).
    
    Args:
        db_path: Path to integrated_users.db
        role: Target role ('paid', 'user', etc.)
    
    Returns:
        List of upgrade results
    """
    results = []
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return results
    
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    cursor = conn.cursor()
    
    for name in SIM_USER_NAMES:
        try:
            cursor.execute('SELECT id, user_role FROM users WHERE username = ?', (name,))
            row = cursor.fetchone()
            
            if not row:
                results.append({'user': name, 'success': False, 'message': 'Not found'})
                continue
            
            user_id, current_role = row
            
            if current_role == role:
                results.append({
                    'user': name, 'user_id': user_id, 'success': True,
                    'message': f'Already {role}'
                })
                continue
            
            cursor.execute('UPDATE users SET user_role = ? WHERE id = ?', (role, user_id))
            conn.commit()
            
            results.append({
                'user': name, 'user_id': user_id, 'success': True,
                'message': f'{current_role} → {role}'
            })
            
        except Exception as e:
            results.append({'user': name, 'success': False, 'message': str(e)})
    
    conn.close()
    return results


def upgrade_roles_via_api(base_url: str, admin_username: str, admin_password: str,
                          role: str = 'paid') -> List[Dict]:
    """Upgrade simulated user roles via the admin API.
    
    Requires admin credentials to authenticate.
    
    Args:
        base_url: API base URL
        admin_username: Admin account username
        admin_password: Admin account password
        role: Target role
    
    Returns:
        List of upgrade results
    """
    results = []
    session = requests.Session()
    
    # Authenticate as admin
    try:
        r = session.post(f"{base_url}/api/auth/login", json={
            'username': admin_username, 'password': admin_password
        }, timeout=30)
        
        if r.status_code != 200:
            print(f"❌ Admin login failed: {r.status_code}")
            return results
        
        token = r.json().get('token')
        if token:
            session.headers['Authorization'] = f'Bearer {token}'
    except Exception as e:
        print(f"❌ Admin auth error: {e}")
        return results
    
    # Get user list to find sim user IDs
    try:
        r = session.get(f"{base_url}/api/admin/users", timeout=15)
        if r.status_code != 200:
            print(f"❌ Cannot list users (admin access required): {r.status_code}")
            return results
        
        users = r.json().get('users', [])
        sim_users = {u['username']: u for u in users if u['username'] in SIM_USER_NAMES}
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return results
    
    # Upgrade each sim user
    for name in SIM_USER_NAMES:
        user = sim_users.get(name)
        if not user:
            results.append({'user': name, 'success': False, 'message': 'Not found'})
            continue
        
        user_id = user['id']
        current_role = user.get('user_role', 'guest')
        
        if current_role == role:
            results.append({
                'user': name, 'user_id': user_id, 'success': True,
                'message': f'Already {role}'
            })
            continue
        
        try:
            r = session.post(f"{base_url}/api/admin/users/{user_id}/role",
                           json={'role': role}, timeout=15)
            if r.status_code == 200:
                results.append({
                    'user': name, 'user_id': user_id, 'success': True,
                    'message': f'{current_role} → {role}'
                })
            else:
                results.append({
                    'user': name, 'user_id': user_id, 'success': False,
                    'message': f'API error: {r.status_code}'
                })
        except Exception as e:
            results.append({'user': name, 'user_id': user_id, 'success': False, 'message': str(e)})
    
    return results


def check_agent_status(db_path: str) -> List[Dict]:
    """Check current status of all simulated users in the database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    cursor = conn.cursor()
    status = []
    
    for name in SIM_USER_NAMES:
        try:
            cursor.execute('''
                SELECT u.id, u.username, u.user_role, u.created_at,
                       (SELECT COUNT(*) FROM ai_conversations WHERE user_id = u.id) as convos,
                       (SELECT COUNT(*) FROM messages m 
                        JOIN ai_conversations c ON m.conversation_id = c.id 
                        WHERE c.user_id = u.id AND m.sender_type = 'user') as msgs,
                       (SELECT message_count FROM message_usage 
                        WHERE user_id = u.id AND date = date('now')) as today_msgs
                FROM users u WHERE u.username = ?
            ''', (name,))
            row = cursor.fetchone()
            
            if row:
                user_id, username, role, created, convos, msgs, today = row
                limit = 'unlimited' if role in ('administrator', 'master', 'paid') else '20/day'
                status.append({
                    'user': username, 'user_id': user_id, 'role': role,
                    'conversations': convos, 'total_messages': msgs,
                    'today_messages': today or 0, 'limit': limit,
                    'created': created
                })
            else:
                status.append({'user': name, 'user_id': None, 'role': 'not_registered'})
        except Exception as e:
            status.append({'user': name, 'error': str(e)})
    
    conn.close()
    return status


def print_results(results: List[Dict], title: str = "Results"):
    """Pretty-print operation results."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    
    for r in results:
        icon = '✅' if r.get('success', False) else '❌' if r.get('success') is False else 'ℹ️'
        uid = f" (id={r['user_id']})" if r.get('user_id') else ""
        msg = r.get('message', r.get('role', ''))
        extra = ""
        if r.get('conversations') is not None:
            extra = f" | {r['conversations']} convos, {r['total_messages']} msgs, today: {r['today_messages']}/{r['limit']}"
        print(f"  {icon} {r['user']:20s}{uid} — {msg}{extra}")
    
    success = sum(1 for r in results if r.get('success', False))
    print(f"\n  {success}/{len(results)} succeeded")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Agent Admin Utilities')
    parser.add_argument('action', choices=['upgrade', 'status', 'check'],
                       help='Action: upgrade roles, check status')
    parser.add_argument('--role', default='paid', help='Target role for upgrade')
    parser.add_argument('--db', default=None, help='Database path')
    parser.add_argument('--url', default=None, help='API URL (for remote upgrade)')
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--admin-user', default=None, help='Admin username (for API upgrade)')
    parser.add_argument('--admin-pass', default=None, help='Admin password (for API upgrade)')
    
    args = parser.parse_args()
    
    db = args.db or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'integrated_users.db'
    )
    
    if args.action in ('status', 'check'):
        results = check_agent_status(db)
        print_results(results, "SIMULATED USER AGENT STATUS")
        return
    
    if args.action == 'upgrade':
        if args.url or args.production:
            url = 'https://trabcd.pythonanywhere.com' if args.production else args.url
            if not args.admin_user or not args.admin_pass:
                print("❌ --admin-user and --admin-pass required for API upgrade")
                sys.exit(1)
            results = upgrade_roles_via_api(url, args.admin_user, args.admin_pass, args.role)
        else:
            results = upgrade_roles_via_db(db, args.role)
        
        print_results(results, f"ROLE UPGRADE → {args.role.upper()}")


if __name__ == '__main__':
    main()
