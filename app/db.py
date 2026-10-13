import os
import sqlite3
import click
from flask import current_app, g
from app.seed_data import SAMPLE_CATEGORIES, SAMPLE_PRODUCTS


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        # Ensure parent directory exists for file-based databases
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Clears existing data and creates new tables from schema.sql."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, mode='r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()


def seed_db():
    """Populates categories and products from seed_data.py or updates existing products with updated pricing."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM categories")
    has_categories = cursor.fetchone()['count'] > 0
    
    if not has_categories:
        # Insert categories
        category_map = {}
        for cat in SAMPLE_CATEGORIES:
            cursor.execute(
                "INSERT INTO categories (name, slug, icon) VALUES (?, ?, ?)",
                (cat['name'], cat['slug'], cat['icon'])
            )
            category_map[cat['slug']] = cursor.lastrowid
            
        # Insert products
        for prod in SAMPLE_PRODUCTS:
            cat_id = category_map.get(prod['category_slug'])
            if cat_id:
                cursor.execute(
                    """
                    INSERT INTO products (category_id, name, slug, description, price, stock, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cat_id,
                        prod['name'],
                        prod['slug'],
                        prod['description'],
                        prod['price'],
                        prod['stock'],
                        prod['image_url']
                    )
                )
    else:
        # Update existing products with latest price/description from seed data
        for prod in SAMPLE_PRODUCTS:
            cursor.execute(
                "UPDATE products SET price = ?, description = ? WHERE slug = ?",
                (prod['price'], prod['description'], prod['slug'])
            )
            
    db.commit()


@click.command('init-db')
def init_db_command():
    """Clear existing data, create new tables, and seed initial products."""
    init_db()
    seed_db()
    click.echo("Initialized and seeded the ShopSphere database.")


def ensure_users_table(db):
    """Safely migrate database to ensure users table and index exist without disturbing existing data."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    db.commit()


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    
    # Auto-initialize and seed database on startup if database table is missing
    with app.app_context():
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            table_exists = cursor.fetchone()
            if not table_exists:
                init_db()
                seed_db()
            else:
                ensure_users_table(db)
        except Exception as exc:
            app.logger.warning(f"Database bootstrap warning: {exc}")

