from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: str) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_name(db: Session, name: str) -> Optional[Product]:
    return db.query(Product).filter(Product.name == name).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate, seller_id: str) -> Product:
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        image=product.image,
        color=product.color,
        material=product.material,
        fits=product.fits,
        stock=product.stock,
        category_id=product.category_id,
        seller_id=seller_id,
        is_active=product.is_active,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: str, product: ProductUpdate) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: str) -> bool:
    db_product = get_product(db, product_id)
    if not db_product:
        return False
    db.delete(db_product)
    db.commit()
    return True


# --- khusus seller (ownership-scoped) ---

def get_products_by_seller(db: Session, seller_id: str, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).filter(Product.seller_id == seller_id).offset(skip).limit(limit).all()


def get_related_products(db: Session, product: Product, limit: int = 3) -> List[Product]:
    return (
        db.query(Product)
        .filter(
            Product.id != product.id,
            Product.is_active == True,  # noqa: E711
            ((Product.seller_id == product.seller_id) | (Product.category_id == product.category_id)),
        )
        .limit(limit)
        .all()
    )


def get_product_owned_by_seller(db: Session, product_id: str, seller_id: str) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id, Product.seller_id == seller_id).first()


def update_seller_product(db: Session, product_id: str, seller_id: str, product: ProductUpdate) -> Optional[Product]:
    db_product = get_product_owned_by_seller(db, product_id, seller_id)
    if not db_product:
        return None
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_seller_product(db: Session, product_id: str, seller_id: str) -> bool:
    db_product = get_product_owned_by_seller(db, product_id, seller_id)
    if not db_product:
        return False
    db.delete(db_product)
    db.commit()
    return True


def update_seller_product_stock(db: Session, product_id: str, seller_id: str, new_stock: int) -> Optional[Product]:
    db_product = get_product_owned_by_seller(db, product_id, seller_id)
    if not db_product:
        return None
    db_product.stock = new_stock
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product