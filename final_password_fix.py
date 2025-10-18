import sqlite3
import bcrypt

# Fix to match browser exactly: ".///" (3 characters)
conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

browser_password = ".///"  # Exactly what browser shows: 3 characters
print(f'Setting password to: "{browser_password}" (length: {len(browser_password)})')

password_hash = bcrypt.hashpw(browser_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Wai Tse'))
conn.commit()
conn.close()

print('✅ Password updated to match browser input!')
print('🌐 Try login again at: http://localhost:5000/multi-user')
