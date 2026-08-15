from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.user import User
from app.models.membership import MembershipType, MembershipBenefit, UserMembership
from app.models.voucher import Voucher
from app.services import user_service, category_service, membership_service
from app.schemas.user import UserCreate
from app.schemas.category import CategoryCreate
from app.core.config import settings

DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "Administrator dengan akses penuh",
    },
    {
        "name": "seller",
        "description": "Penjual yang dapat mengelola produk atau penjualan",
    },
    {
        "name": "user",
        "description": "Pengguna umum aplikasi",
    },
]

DEFAULT_CATEGORIES = [
    {
        "name": "Benang",
        "description": "Tali Benang",
    },
    {
        "name": "Bonus",
        "description": "Pemasukan tambahan atau bonus",
    },
    {
        "name": "Freelance",
        "description": "Pemasukan dari pekerjaan freelance",
    },
    {
        "name": "Makanan",
        "description": "Pengeluaran untuk makan dan minum",
    },
    {
        "name": "Transportasi",
        "description": "Pengeluaran untuk transportasi",
    },
    {
        "name": "Belanja",
        "description": "Pengeluaran untuk kebutuhan belanja",
    },
    {
        "name": "Tagihan",
        "description": "Pengeluaran untuk listrik, air, internet, dan tagihan lain",
    },
    {
        "name": "Hiburan",
        "description": "Pengeluaran untuk hiburan",
    },
    {
        "name": "Kesehatan",
        "description": "Pengeluaran untuk kesehatan",
    },
    {
        "name": "Pendidikan",
        "description": "Pengeluaran untuk pendidikan",
    },
    {
        "name": "Tabungan",
        "description": "Dana yang dialokasikan untuk tabungan",
    },
    {
        "name": "Investasi",
        "description": "Dana yang dialokasikan untuk investasi",
    },
    {
        "name": "Lainnya",
        "description": "Kategori lain di luar daftar utama",
    },
]

DEFAULT_VOUCHERS = [
    {
        "code": "HELLO10",
        "name": "Diskon 10%",
        "description": "Potongan 10% untuk semua pembelian",
        "discount_percent": 10,
        "max_discount": 50000,
        "min_purchase": 50000,
    },
    {
        "code": "DISKON20",
        "name": "Diskon 20%",
        "description": "Potongan 20% untuk pembelian minimal Rp 100.000",
        "discount_percent": 20,
        "max_discount": 100000,
        "min_purchase": 100000,
    },
]


def seed_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role_name: str,
):
    existing_user = user_service.get_user_by_email(db, email=email)
    role = user_service.get_role_by_name(db, name=role_name)

    if not existing_user:
        print(f"Seeding default {role_name} user: {email}")
        user_in = UserCreate(
            name=name,
            email=email,
            password=password,
            is_admin=role_name == "admin",
        )
        user_service.create_user(db, user=user_in, role_name=role_name)
        return

    if role and existing_user.role_id != role.id:
        existing_user.role_id = role.id
        existing_user.is_admin = role_name == "admin"
        db.commit()


def seed_db(db: Session):
    for role_data in DEFAULT_ROLES:
        existing_role = user_service.get_role_by_name(db, name=role_data["name"])
        if existing_role:
            continue

        print(f"Seeding default role: {role_data['name']}")
        db.add(Role(**role_data))
        db.commit()

    seed_user(
        db=db,
        name="Super Admin",
        email=settings.FIRST_USER_ADMIN_EMAIL,
        password=settings.FIRST_USER_ADMIN_PASSWORD,
        role_name="admin",
    )
    seed_user(
        db=db,
        name="Default Seller",
        email="seller@finsight.com",
        password="seller123",
        role_name="seller",
    )
    seed_user(
        db=db,
        name="Default User",
        email="user@finsight.com",
        password="user1234",
        role_name="user",
    )

    user_role = user_service.get_role_by_name(db, name="user")
    admin_role = user_service.get_role_by_name(db, name="admin")
    if user_role:
        users_without_role = db.query(User).filter(User.role_id.is_(None)).all()
        for db_user in users_without_role:
            db_user.role_id = admin_role.id if db_user.is_admin and admin_role else user_role.id
        if users_without_role:
            db.commit()

    for category_data in DEFAULT_CATEGORIES:
        existing_category = category_service.get_category_by_name(
            db,
            name=category_data["name"],
        )
        if existing_category:
            continue

        print(f"Seeding default category: {category_data['name']}")
        category_service.create_category(
            db,
            category=CategoryCreate(
                name=category_data["name"],
                description=category_data["description"],
                is_active=True,
            ),
        )

    membership_service.ensure_default_membership_types(db)

    for voucher_data in DEFAULT_VOUCHERS:
        existing = db.query(Voucher).filter(Voucher.code == voucher_data["code"]).first()
        if existing:
            continue
        print(f"Seeding default voucher: {voucher_data['code']}")
        db.add(Voucher(**voucher_data))
    db.commit()

    users_without_membership = (
        db.query(User)
        .filter(~User.id.in_(db.query(UserMembership.user_id)))
        .all()
    )
    for db_user in users_without_membership:
        membership_service.ensure_user_membership(db, db_user)
        print(f"Seeding user membership for: {db_user.email}")
