"""Obsługa bazy danych SQL dla aplikacji Talk Shop."""

# =====================================================================================
#                                    INCLUDES
# =====================================================================================

from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import String, Float, Integer, create_engine, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from collections.abc import Sequence


# =====================================================================================
#                                     DATA MODEL
# =====================================================================================
@dataclass
class Product:
    name: str
    price: float
    stock: int


example_data: list[Product] = [
    Product(name="Monorail", price=1449.99, stock=30),
    Product(name="Hewlett Packard", price=1849.99, stock=23),
    Product(name="COMPAQ", price=2399.99, stock=8),
]


# =====================================================================================
#                                  DATABASE INTERFACE
# =====================================================================================
class DatabaseModel(DeclarativeBase):
    pass


class ProductModel(DatabaseModel):
    __tablename__ = "products"
    # Kolumny tabeli w bazie danych:
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float())
    stock: Mapped[int] = mapped_column(Integer())

    # Metoda konwertująca obiekty z poziomu kodu aplikacji na wpis gotowy dla bazy danych
    @staticmethod
    def to_model(product: Product) -> ProductModel:
        return ProductModel(name=product.name, price=product.price, stock=product.stock)

    # Metoda konwertująca wpis z bazy danych z powrotem na obiekt Pythonowy Product
    def from_model(self) -> Product:
        return Product(name=self.name, price=self.price, stock=self.stock)

# Tworzy połączenie z lokalną bazą SQL oraz buduje wszystkie tabele, jeśli jeszcze nie istnieją
def prepare_db() -> Engine:
    engine = create_engine("sqlite:///local/demo.db")
    DatabaseModel.metadata.create_all(engine)
    return engine

# Wypełnia bazę początkowymi danymi z listy `example_data`
def populate_db(eng: Engine) -> None:
    with Session(eng) as session:
        for product in example_data:
            session.add(ProductModel.to_model(product)) # Dodaje każdy produkt do kolejki
        session.commit() # Zatwierdza zmiany w bazie danych

# Czyszczenie całej tabeli z produktami
def clear_db(eng: Engine)-> None:
    with Session(eng) as session:
        session.query(ProductModel).delete(synchronize_session="fetch") # Usuwa wszystkie rekordy z tabeli 'products'
        session.commit()

def retrieve_product_by_name(eng: Engine, name: str) -> list[Product]:
    prods: list[Product] = []
    with Session(eng) as session:
        products: Sequence[ProductModel] = session.scalars(
            select(ProductModel).where(ProductModel.name == name)
        ).all()
        for product in products:
            prods.append(product.from_model())
    return prods


# =====================================================================================
#                                  OPERACJE CRUD
# =====================================================================================
def add_product(eng: Engine, product: Product) -> None:
    """Add product."""
    with Session(eng) as session:
        session.add(ProductModel.to_model(product))
        session.commit()

def retrieve_product_by_name(eng: Engine, name: str) -> Product | None:
    """Find product."""
    with Session(eng) as session:
        product = session.scalars(
            select(ProductModel).where(
                ProductModel.name == name.strip().lower()
            )
        ).first()
        return product.from_model() if product else None

def update_product(eng: Engine, name: str, price: float, stock: int) -> bool:
    """Update product."""
    with Session(eng) as session:
        product = session.scalars(
            select(ProductModel).where(
                ProductModel.name == name.strip().lower()
            )
        ).first()
        if product:
            product.price = price
            product.stock = stock
            session.commit()
            return True
        return False

def delete_product(eng: Engine, name: str) -> bool:
    """Delete product."""
    with Session(eng) as session:
        product = session.scalars(
            select(ProductModel).where(
                ProductModel.name == name.strip().lower()
            )
        ).first()
        if product:
            session.delete(product)
            session.commit()
            return True
        return False

def get_all_products(eng: Engine) -> list[Product]:
    """Get all products."""
    with Session(eng) as session:
        products = session.scalars(select(ProductModel)).all()
        return [p.from_model() for p in products]


def main() -> None:
    eng = prepare_db()
    clear_db(eng)
    populate_db(eng)
    prods = retrieve_product_by_name(eng, "Monorail")
    for prod in prods:
        print(prod)


if __name__ == "__main__":
    main()