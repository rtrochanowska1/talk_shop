"""Talk Shop - Chatbot"""

# ======================================================================================
#                                    INCLUDES
# ======================================================================================
from dataclasses import dataclass #do szybkiego tworzenia struktur danych
from lark import Lark, Token, Tree
import argparse #do czytania poleceń wpisanych w konsoli przy uruchamianiu
from data_shop import (
    Product,
    add_product,
    clear_db,
    delete_product,
    get_all_products,
    populate_db,
    prepare_db,
    retrieve_product_by_name,
    update_product,
)


# ======================================================================================
#                                     DATA MODEL
# ======================================================================================
# Dekorator @dataclass pełni rolę szablonu formularza.
# Zrób klasę reprezentującą produkt, która przechowywać będzie
# nazwę, cenę oraz stan magazynowy, (Python sam dba o resztę logiki w tle)
@dataclass  
class Product:
    name: str
    price: float
    stock: int


# Baza danych sklepu (magazyn).
# Używamy słownika, gdzie kluczem jest identyfikator przedmiotu (np. "compaq"),
# a wartością jest obiekt klasy Product zawierający jego szczegóły.
products: dict[str, Product] = {
    "monorail": Product(name="Monorail", price=1449.99, stock=30),
    "hewlett_packard": Product(name="Hewlett Packard", price=1849.99, stock=23),
    "compaq": Product(name="COMPAQ", price=2399.99, stock=8),
}


# ======================================================================================
#                                     NLP
# ======================================================================================
# Funkcja pomocnicza do wizualizacji drzewa rozbioru gramatycznego.
# Pokazuje, jak analizator podzielił zdanie wpisane przez użytkownika na mniejsze elementy.
def print_tree(node: Tree | Token, depth: int = 0) -> None: # Zdefiniuj funkcję 'print_tree', która przyjmuje węzeł zdania oraz poziom wcięcia (domyślnie 0):
    if isinstance(node, Token): # Jeśli sprawdzany element 'node' JEST pojedynczym słówkiem (typu Token):
        print(" " * depth + f"{node.type} = {node.value}")
        return
    print(" " * depth + node.data) # W przeciwnym razie (gdy jest to gałąź Tree) wypisz nazwę tej gałęzi:
    for subtree in node.children: # Dla każdego dziecka znajdującego się w tej gałęzi:
        print_tree(subtree, depth + 1) # Uruchom ponownie tę samą funkcję print_tree dla dziecka, zwiększając wcięcie o 1


# Główna funkcja przetwarzająca zapytanie użytkownika:
# 1. Analizuje tekst wejściowy zgodnie z zdefiniowaną wyżej gramatyką.
# 2. Tworzy drzewo składniowe i wyciąga z niego kluczowe słowo (nazwę produktu).
# 3. Odnajduje produkt w magazynie (słowniku `products`) i zwraca sformatowaną odpowiedź.
def process_query(query: str, grammar: str) -> str:
    parser = Lark(grammar, parser="earley") #Tworzy analizatora (zwanego parserem)

    query_clean = query.strip().lower() # zmiana inputu na małe litery

    # Sprawdzenie pustego wejścia (obsłużenie na plus)
    if not query_clean:
        return "Please enter a query."
    
    try:
        tree = parser.parse(query) #rozbija zdanie na slowa
    except Exception:
        return "Input is incorrect"
    #print_tree(tree)
    query_node: Tree | Token = tree.children[0] #sprawdza pierwszy element (slowo)
    if isinstance(query_node, Token): #Jeśli nasz obiekt query_node jest typu Token...
        return "ERROR"

    if query_node.data == "price_question":
        item = list(query_node.find_token("ITEM"))[0] # "Znajdź w drzewie słowo oznaczone jako 'ITEM', weź pierwsze z listy i przypisz do 'item'
        try:
            price = products[item.value].price
            return f"The price of {item.value} is {price}"
        except KeyError:
            return "There is no such product"

    if query_node.data == "in_stock_question":
        item = list(query_node.find_token("ITEM"))[0]
        try:
            stock = products[item.value].stock
            if stock >= 0:
                return f"The {item.value} is in stock"
            return f"The {item.value} is not in stock"
        except KeyError:
            return "There is no such product"

    if query_node.data == "number_question":
        item = list(query_node.find_token("ITEM"))[0]
        try:
            stock = products[item.value].stock
            return f"The number of {item.value} is {stock}"
        except KeyError:
            return "There is no such product"
        
    return "ERROR" # Jeśli zapytanie pasowało do gramatyki, ale nie obsłużyliśmy go powyżej


def run_admin_menu(eng) -> None:
    while True:
        print("\n=== ADMIN MENU ===")
        print("1 - Add product")
        print("2 - Find product")
        print("3 - Update product")
        print("4 - Delete product")
        print("5 - List products")
        print("6 - Clear database")
        print("0 - Exit admin mode")

        choice = input("\nSelect option: ").strip() #odcina zbedne spacje

        # 1 - Dodaj produkt
        if choice == "1":
            name = input("Product name: ").strip()
            price = float(input("Price: "))
            stock = int(input("Stock: "))
            add_product(eng, Product(name=name, price=price, stock=stock))
            print(f"Product '{name}' added successfully.")

        # 2 - Znajdź produkt
        elif choice == "2":
            name = input("Enter product name to find: ").strip()
            prod = retrieve_product_by_name(eng, name)
            if prod:
                print(
                    f"Found: {prod.name.title()} | Price: {prod.price} | Stock: {prod.stock}"
                )
            else:
                print("Product not found.")

        # 3 - Zmień produkt
        elif choice == "3":
            name = input("Enter product name to update: ").strip()
            price = float(input("New price: "))
            stock = int(input("New stock quantity: "))
            if update_product(eng, name, price, stock):
                print(f"Product '{name}' updated successfully.")
            else:
                print("Product not found.")

        # 4 - Usuń produkt
        elif choice == "4":
            name = input("Enter product name to delete: ").strip()
            if delete_product(eng, name):
                print(f"Product '{name}' deleted successfully.")
            else:
                print("Product not found.")

        # 5 - Lista produktów
        elif choice == "5":
            products = get_all_products(eng)
            print("\n--- DATABASE PRODUCTS ---")
            if not products:
                print("(Database is empty)")
            for p in products:
                print(f"{p.name.title()}: Price = {p.price}, Stock = {p.stock}")

        # 6 - Wyczyść bazę danych
        elif choice == "6":
            clear_db(eng)
            print("Database cleared successfully!")

        elif choice == "0":
            print("Exiting admin mode.")
            break
        else:
            print("Invalid option, please try again.")

# ======================================================================================
#                                   MAIN
# ======================================================================================
# Punkt wejścia do programu.
# Pobiera dane od użytkownika za pomocą input(), przekazuje je do przetworzenia
# i wyświetla wynik w konsoli.
def main():
    parser = argparse.ArgumentParser(description="Talk Shop App")
    parser.add_argument(
        "-g",
        "--grammar",
        default="src/talk_shop/static/grammar.txt", # domyslna sciezka, jeśli użytkownik nie poda własnej
        help="Ścieżka do pliku gramatyki",
    )
    parser.add_argument(
        "--admin", action="store_true", help="Uruchom w trybie administratora"
    )
    # sprawdza, z jakimi flagami uruchomiono program w terminalu
    args = parser.parse_args()
    
    # Przygotowanie i wstępne wypełnienie bazy danych przy starcie
    eng = prepare_db()
    populate_db(eng)

    if args.admin:
        run_admin_menu(eng)
    else:
    # Otwiera plik podany we fladze -g i czyta z niego całą gramatykę
        with open(args.grammar, "r") as f:
            loaded_grammar = f.read()

        print("Welcome to Talk Shop Chatbot!")
        print("You can ask about prices, stock, or quantities.")
        print("Type 'END' to exit the program.")

        while True: # pętla, aby program konczyl się dopiero po wpisaniu end
            user_input = input().strip().lower() # zamienia input na male litery => progrma nie wywali sie jesli uzytkownik bedzie pisal capslockiem
            if user_input == 'end':
                break
            response = process_query(user_input, loaded_grammar)
            print(response)


# Standardowa konstrukcja w Pythonie: uruchamia funkcję main() tylko wtedy,
# gdy plik jest wykonywany bezpośrednio (a nie importowany jako moduł).
if __name__ == "__main__":
    main()
