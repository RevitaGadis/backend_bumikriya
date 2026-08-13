"""seed default roles categories and users

Revision ID: 1761c4ba48ca
Revises: 064d1b4131c1
Create Date: 2026-08-12 19:18:29.257866

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1761c4ba48ca'
down_revision: Union[str, Sequence[str], None] = '064d1b4131c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_ADMIN_ID = "11111111-1111-1111-1111-111111111111"
ROLE_SELLER_ID = "22222222-2222-2222-2222-222222222222"
ROLE_USER_ID = "33333333-3333-3333-3333-333333333333"
ADMIN_USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SELLER_USER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
USER_USER_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"

ROLES = [
    {"id": ROLE_ADMIN_ID, "name": "admin", "description": "Administrator dengan akses penuh"},
    {"id": ROLE_SELLER_ID, "name": "seller", "description": "Penjual yang dapat mengelola produk atau penjualan"},
    {"id": ROLE_USER_ID, "name": "user", "description": "Pengguna umum aplikasi"},
]

USERS = [
    {
        "id": ADMIN_USER_ID,
        "name": "Super Admin",
        "email": "admin@bumikriya.com",
        "hashed_password": "$pbkdf2-sha256$29000$cs4Z47xXqjVmLAWgFOIcIw$VSykpz7ncDhBGJOtCrBuWH00AqttF4Jc12sKQwr0xkE",
        "is_admin": True,
        "role_id": ROLE_ADMIN_ID,
        "status": "active",
        "is_verified": True,
    },
    {
        "id": SELLER_USER_ID,
        "name": "Default Seller",
        "email": "seller@finsight.com",
        "hashed_password": "$pbkdf2-sha256$29000$pFSqdc5Zay0lxFgLAYDw/g$EHnRt2fqd5SiZwZNnBkTfeJp6pOApU22yiGbSDO.FZY",
        "is_admin": False,
        "role_id": ROLE_SELLER_ID,
        "status": "active",
        "is_verified": True,
    },
    {
        "id": USER_USER_ID,
        "name": "Default User",
        "email": "user@finsight.com",
        "hashed_password": "$pbkdf2-sha256$29000$x1iL8d67N6aUstYaw7hXag$hSdojJ2ZoXW32PhfJNfCZSTl2px1WVX3FLM5LBGE5/A",
        "is_admin": False,
        "role_id": ROLE_USER_ID,
        "status": "active",
        "is_verified": True,
    },
]

CATEGORIES = [
    {"name": "Benang", "description": "Tali Benang"},
    {"name": "Bonus", "description": "Pemasukan tambahan atau bonus"},
    {"name": "Freelance", "description": "Pemasukan dari pekerjaan freelance"},
    {"name": "Makanan", "description": "Pengeluaran untuk makan dan minum"},
    {"name": "Transportasi", "description": "Pengeluaran untuk transportasi"},
    {"name": "Belanja", "description": "Pengeluaran untuk kebutuhan belanja"},
    {"name": "Tagihan", "description": "Pengeluaran untuk listrik, air, internet, dan tagihan lain"},
    {"name": "Hiburan", "description": "Pengeluaran untuk hiburan"},
    {"name": "Kesehatan", "description": "Pengeluaran untuk kesehatan"},
    {"name": "Pendidikan", "description": "Pengeluaran untuk pendidikan"},
    {"name": "Tabungan", "description": "Dana yang dialokasikan untuk tabungan"},
    {"name": "Investasi", "description": "Dana yang dialokasikan untuk investasi"},
    {"name": "Lainnya", "description": "Kategori lain di luar daftar utama"},
]

CATEGORY_IDS = {
    name: str(uuid.uuid4()) for name in (c["name"] for c in CATEGORIES)
}


def upgrade() -> None:
    conn = op.get_bind()

    roles = conn.execute(sa.text("SELECT id FROM roles WHERE name = 'admin'")).fetchall()
    if not roles:
        for role in ROLES:
            conn.execute(
                sa.text("INSERT INTO roles (id, name, description) VALUES (:id, :name, :description) "
                        "ON CONFLICT (name) DO NOTHING"),
                role,
            )

    for cat in CATEGORIES:
        conn.execute(
            sa.text("INSERT INTO categories (id, name, description, is_active) VALUES (:id, :name, :description, TRUE) "
                    "ON CONFLICT (name) DO NOTHING"),
            {"id": CATEGORY_IDS[cat["name"]], "name": cat["name"], "description": cat["description"]},
        )

    for user in USERS:
        conn.execute(
            sa.text("INSERT INTO users (id, name, email, hashed_password, is_admin, role_id, status, is_verified) "
                    "VALUES (:id, :name, :email, :hashed_password, :is_admin, :role_id, :status, :is_verified) "
                    "ON CONFLICT (email) DO NOTHING"),
            user,
        )


def downgrade() -> None:
    conn = op.get_bind()
    for email in ("admin@bumikriya.com", "seller@finsight.com", "user@finsight.com"):
        conn.execute(sa.text("DELETE FROM users WHERE email = :email"), {"email": email})
    for name in ["Benang", "Bonus", "Freelance", "Makanan", "Transportasi", "Belanja", "Tagihan", "Hiburan", "Kesehatan", "Pendidikan", "Tabungan", "Investasi", "Lainnya"]:
        conn.execute(sa.text("DELETE FROM categories WHERE name = :name"), {"name": name})
    for name in ("admin", "seller", "user"):
        conn.execute(sa.text("DELETE FROM roles WHERE name = :name"), {"name": name})