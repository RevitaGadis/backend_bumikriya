from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.role import Role
from app.models.user import User
from app.schemas.dashboard import OrderStatus, PaymentMethod, PaymentStatus
from app.services import user_service, category_service
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

DEFAULT_RECENT_ORDERS = [
    {
        "order_number": "ORD-089",
        "status": OrderStatus.DIPROSES,
        "subtotal": 235000,
    },
    {
        "order_number": "ORD-088",
        "status": OrderStatus.DIKIRIM,
        "subtotal": 335000,
    },
    {
        "order_number": "ORD-087",
        "status": OrderStatus.SELESAI,
        "subtotal": 485000,
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


def seed_orders(db: Session):
    if db.query(Order).first():
        return

    buyer_users = db.query(User).filter(User.is_admin.is_(False)).all()
    if not buyer_users:
        buyer_users = db.query(User).all()
    if not buyer_users:
        return

    products = db.query(Product).all()
    if not products:
        products = [
            Product(
                name="Benang Rajut Premium",
                price=25000,
                image="/images/products/default.jpg",
                stock=100,
                is_active=True,
            ),
            Product(
                name="Kain Katun Lembut",
                price=45000,
                image="/images/products/default.jpg",
                stock=50,
                is_active=True,
            ),
            Product(
                name="Pola Rajut Eksklusif",
                price=15000,
                image="/images/products/default.jpg",
                stock=80,
                is_active=True,
            ),
        ]
        db.add_all(products)
        db.commit()
        for product in products:
            db.refresh(product)

    now = datetime.now()
    shipping_cost = 15000

    def build_order(order_number, user, status, subtotal, created_at):
        order = Order(
            user_id=user.id,
            order_number=order_number,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_amount=subtotal + shipping_cost,
            status=status,
            shipping_address="Jl. Merdeka No. 10, Jakarta",
            created_at=created_at,
        )
        db.add(order)
        db.flush()

        product = products[abs(hash(order_number)) % len(products)]
        quantity = max(1, int(subtotal // product.price))
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                price=product.price,
                quantity=quantity,
                subtotal=product.price * quantity,
            )
        )
        paid = status in (OrderStatus.DIKIRIM, OrderStatus.SELESAI)
        db.add(
            Payment(
                order_id=order.id,
                method=PaymentMethod.CASH if status == OrderStatus.SELESAI else PaymentMethod.TRANSFER,
                amount=order.total_amount,
                status=PaymentStatus.PAID if paid else PaymentStatus.PENDING,
                transaction_id=f"TXN-{order_number}",
                paid_at=created_at + timedelta(minutes=5) if paid else None,
            )
        )
        return order

    orders = []
    for idx, order_data in enumerate(DEFAULT_RECENT_ORDERS):
        user = buyer_users[idx % len(buyer_users)]
        orders.append(
            build_order(
                order_data["order_number"],
                user,
                order_data["status"],
                order_data["subtotal"],
                now - timedelta(minutes=idx * 45),
            )
        )

    remaining_total = 15240000 - sum(order.total_amount for order in orders)
    remaining_orders = 21
    base_total = remaining_total // remaining_orders
    total_remainder = remaining_total % remaining_orders

    for idx in range(remaining_orders):
        order_number = f"ORD-{86 - idx:03d}"
        user = buyer_users[(idx + len(DEFAULT_RECENT_ORDERS)) % len(buyer_users)]
        orders.append(
            build_order(
                order_number,
                user,
                OrderStatus.SELESAI,
                base_total + (1 if idx < total_remainder else 0),
                now - timedelta(minutes=(idx + len(DEFAULT_RECENT_ORDERS)) * 45),
            )
        )

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

    seed_orders(db)
