import argparse
import sys
import json

class InvalidIdException(Exception): pass

class InvalidPriceException(Exception): pass

class Customer:
    """
    Represents a customer in the Matamazon system.

    Required fields (per specification):
        - id (int): Unique non-negative integer identifier.
        - name (str): Customer name.
        - city (str): Customer city.
        - address (str): Customer shipping address.

    Exceptions:
        InvalidIdException: If 'id' is not valid according to the specification.

    Printing:
        Must support printing in the following format (example):
            Customer(id=42, name='Daniel Elgarici', city='Karmiel, address='123 Main Street')
        Exact formatting requirements appear in the assignment PDF.
    """

    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0: raise InvalidIdException("Invalid Customer ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __repr__(self):
        return f"Customer(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"

class Supplier:
    """
    Represents a supplier in the Matamazon system.

    Required fields (per specification):
        - id (int): Unique non-negative integer identifier.
        - name (str): Supplier name.
        - city (str): Warehouse city (origin city for shipping).
        - address (str): Warehouse address.

    Exceptions:
        InvalidIdException: If 'id' is not valid according to the specification.

    Printing:
        Must support printing in the following format (example):
            Supplier(id=42, name='Yinon Goldshtein', city='Haifa, address='32 David Rose Street')
    """

    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0: raise InvalidIdException("Invalid Supplier ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __repr__(self):
        return f"Supplier(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"


class Product:
    """
    Represents a product sold on the Matamazon website.

    Required fields (per specification):
        - id (int): Unique non-negative integer identifier.
        - name (str): Product name.
        - price (float): Non-negative price.
        - supplier_id (int): ID of the supplier that provides the product.
        - quantity (int): Non-negative quantity in stock.

    Exceptions:
        InvalidIdException:
            - If id/supplier_id/quantity is invalid per specification.
        InvalidPriceException:
            - If price is invalid (e.g., negative).

    Printing:
        Must support printing in the following format (example):
            Product(id=101, name='Harry Potter Cushion', price=29.99, supplier_id=42, quantity=555)
    """

    def __init__(self, id, name, price, supplier_id, quantity):
        if any(not isinstance(val, int) or val < 0 for val in (id, supplier_id, quantity)):
            raise InvalidIdException("Invalid Product IDs or quantity")
        if not isinstance(price, (int, float)) or price < 0:
            raise InvalidPriceException("Invalid Product price")
        self.id = id
        self.name = name
        self.price = float(price)
        self.supplier_id = supplier_id
        self.quantity = quantity

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price}, supplier_id={self.supplier_id}, quantity={self.quantity})"

    def __lt__(self, other):
        return self.price < other.price


class Order:
    """
    Represents a placed order.

    Required fields (per specification):
        - id (int): Unique non-negative integer identifier (assigned by the system).
        - customer_id (int): ID of the customer who placed the order.
        - product_id (int): ID of the ordered product.
        - quantity (int): Ordered quantity (non-negative integer).
        - total_price (float): Total price for the order (non-negative).

    Exceptions:
        InvalidIdException:
            - If one of the ID fields is invalid.
        InvalidPriceException:
            - If total_price is invalid.

    Printing:
        Must support printing in the following format (example):
            Order(id=1, customer_id=42, product_id=101, quantity=10, total_price=299.9)

    """

    def __init__(self, id, customer_id, product_id, quantity, total_price):
        if any(not isinstance(val, int) or val < 0 for val in (id, customer_id, product_id, quantity)):
            raise InvalidIdException("Invalid Order IDs or quantity")
        if not isinstance(total_price, (int, float)) or total_price < 0:
            raise InvalidPriceException("Invalid Order price")
        self.id = id
        self.customer_id = customer_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = float(total_price)

    def __repr__(self):
        return f"Order(id={self.id}, customer_id={self.customer_id}, product_id={self.product_id}, quantity={self.quantity}, total_price={self.total_price})"


class MatamazonSystem:
    """
    Main system class that stores and manages customers, suppliers, products and orders.

    The system must support:
        - Registering customers/suppliers (with unique IDs across both types).
        - Adding/updating products (must validate supplier existence).
        - Placing orders (validate product existence and stock).
        - Removing objects by ID and type (with dependency constraints).
        - Searching products by name/query and optional max price.
        - Exporting system state to a text file (customers/suppliers/products only).
        - Exporting orders to JSON grouped by supplier origin city.

    Notes:
        - The specification does not require specific internal fields. Any data structures are allowed,
          as long as the behaviors match the spec.
        - A parameterless constructor is required.
    """

    def __init__(self):
        """
        Initialize an empty Matamazon system.

        Requirements:
            - Must be parameterless.
            - Internal collections may be chosen freely (dict/list, etc.).
        """
        self.customers = {}
        self.suppliers = {}
        self.products = {}
        self.orders = {}
        self.next_order_id = 1

    def register_entity(self, entity, is_customer):
        """
        Register a Customer or Supplier in the system.

        Args:
            entity: A Customer or Supplier object.
            is_customer (bool): True if entity is Customer, False if entity is Supplier.

        Raises:
            InvalidIdException:
                - If the entity ID is invalid.
                - If the entity ID already exists in the system (note: IDs must be unique across
                  customers AND suppliers).
        """
        if is_customer:
            if entity.id in self.customers: raise InvalidIdException("Customer ID exists")
            self.customers[entity.id] = entity
        else:
            if entity.id in self.suppliers: raise InvalidIdException("Supplier ID exists")
            self.suppliers[entity.id] = entity

    def add_or_update_product(self, product):
        """
        Add a new product or update an existing product.

        Behavior:
            - If product does not exist in system: add it.
            - If product exists:
                - It must belong to the same supplier as the existing one (same supplier_id),
                  otherwise raise InvalidIdException.
                - Update the stored product's fields according to the new product.

        Args:
            product: A Product object.

        Raises:
            InvalidIdException:
                - If the supplier_id does not exist in the system.
                - If attempting to update a product but supplier_id differs from the existing product.
        """
        if product.supplier_id not in self.suppliers:
            raise InvalidIdException("Supplier does not exist")
        if product.id in self.products and self.products[product.id].supplier_id != product.supplier_id:
            raise InvalidIdException("Product exists for a different supplier")
        self.products[product.id] = product

    def place_order(self, customer_id, product_id, quantity=1):
        """
        Place an order for a product by a customer.

        Args:
            customer_id (int): Customer ID.
            product_id (int): Product ID.
            quantity (int, optional): Quantity to order. Defaults to 1.

        Returns:
            str: Status message according to specification:
                - "The order has been accepted in the system"
                - "The product does not exist in the system"
                - "The quantity requested for this product is greater than the quantity in stock"

        Behavior:
            - If product does not exist: return the relevant message.
            - If quantity requested > stock: return the relevant message.
            - Otherwise:
                - Decrease product stock by quantity.
                - Create a new Order with an auto-incremented system ID (starting at 1).
                - Store the order in the system.
                - Return success message.

        Notes:
            - The specification assumes quantity is an integer.
        """
        if customer_id not in self.customers or product_id not in self.products:
            raise InvalidIdException("Customer or Product missing")
        product = self.products[product_id]
        if product.quantity >= quantity:
            product.quantity -= quantity
            total_price = product.price * quantity
            order = Order(self.next_order_id, customer_id, product_id, quantity, total_price)
            self.orders[self.next_order_id] = order
            self.next_order_id += 1
            return "The order has been accepted in the system"
        else:
            return "The quantity requested for this product is greater than the quantity in stock"

    def remove_object(self, _id, class_type):
        """
        Remove an object from the system by ID and type.

        Args:
            _id (int): Object ID to remove.
            class_type (str): One of: "Customer", "Supplier", "Product", "Order"
                              (exact casing/spelling per assignment).

        Returns:
            int | None:
                - If removing an Order: return the ordered quantity of that order (to restore stock).
                - Otherwise: no return value required.

        Raises:
            InvalidIdException:
                - If _id is not a valid non-negative integer.
                - If attempting to remove a Customer/Supplier/Product that still has dependent orders
                  in the system (i.e., orders that were not removed).
                - Additional InvalidIdException conditions as required by specification.
        """
        if not isinstance(id, int) or id < 0: raise InvalidIdException("Invalid ID")
        class_type = class_type.strip().lower()

        if class_type == 'order':
            if id not in self.orders: raise InvalidIdException("Order not found")
            order = self.orders.pop(id)
            if order.product_id in self.products:
                self.products[order.product_id].quantity += order.quantity
        elif class_type == 'customer':
            if id not in self.customers: raise InvalidIdException("Customer not found")
            if any(o.customer_id == id for o in self.orders.values()): raise InvalidIdException(
                "Customer has existing order")
            self.customers.pop(id)
        elif class_type == 'supplier':
            if id not in self.suppliers: raise InvalidIdException("Supplier not found")
            if any(self.products.get(o.product_id, Product(0, '', 0, 0, 0)).supplier_id == id for o in
                   self.orders.values()):
                raise InvalidIdException("Supplier has active order")
            self.suppliers.pop(id)
        elif class_type == 'product':
            if id not in self.products: raise InvalidIdException("Product not found")
            if any(o.product_id == id for o in self.orders.values()): raise InvalidIdException("Product in order")
            self.products.pop(id)

    def search_products(self, query, max_price=None):
        """
        Search products by query in the product name, and optionally filter by max_price.

        Args:
            query (str): Product name or part of product name.
            max_price (float, optional): If provided, only return products with price <= max_price.

        Returns:
            list[Product]:
                - Products that match the query and have quantity != 0,
                - Sorted by ascending price.
                - If no matching products exist, return an empty list.
        """
        results = [p for p in self.products.values() if query in p.name and p.quantity > 0]
        if max_price is not None:
            results = [p for p in results if p.price <= float(max_price)]
        return sorted(results)

    def export_system_to_file(self, path):
        """
        Export system state (customers, suppliers, products) to a text file.

        Args:
            path (str): Output file path.

        Behavior:
            - Write each object on its own line, using the object's print/str representation.
            - Orders must NOT be included.
            - No constraint on the ordering of objects in the output.

        Raises:
            OSError (or any file-open exception): Must be propagated to the caller.
        """
        with open(path, 'w') as f:
            for c in self.customers.values(): f.write(str(c) + '\n')
            for s in self.suppliers.values(): f.write(str(s) + '\n')
            for p in self.products.values(): f.write(str(p) + '\n')

    def export_orders(self, out_file):
        """
        Export orders in JSON format grouped by origin city.

        Args:
            out_file (file-like)

        Behavior (per specification):
            - Produce a JSON object where:
                - Keys: origin city (supplier city) for each order.
                - Values: list of strings representing orders (format as specified in section 4.1.4).
            - Order lists can be in any order.
            - No requirement on key ordering.

        Raises:
            Any exception during writing: Must be propagated to the caller.

        Notes:
            - The order origin city is the supplier city of the ordered product.
        """
        out_dict = {}
        for order in self.orders.values():
            if order.product_id in self.products:
                supplier_id = self.products[order.product_id].supplier_id
                city = self.suppliers[supplier_id].city
                if city not in out_dict:
                    out_dict[city] = []
                out_dict[city].append(str(order))
        json.dump(out_dict, out_file)


def load_system_from_file(path):
    """
    Load a MatamazonSystem from an input file.

    Args:
        path (str): Path to a text file containing customers, suppliers and products.

    Returns:
        MatamazonSystem: Initialized system with the data found in the file.

    Behavior:
        - The file lines contain objects in the format produced by export_system_to_file (section 4.2).
        - Lines may appear in any order (e.g., product lines can appear before supplier lines).
        - Illegal lines may be ignored.
        - If an exception occurs during the creation of any required object due to invalid data,
          the function should stop and propagate the exception (as specified).

    Notes:
        - The assignment hints that eval() may be used.
    """
    sys_obj = MatamazonSystem()
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                obj = eval(line)
                if isinstance(obj, Customer):
                    sys_obj.register_entity(obj, True)
                elif isinstance(obj, Supplier):
                    sys_obj.register_entity(obj, False)
                elif isinstance(obj, Product):
                    sys_obj.add_or_update_product(obj)
            except Exception as e:
                raise e
    return sys_obj

class CustomParser(argparse.ArgumentParser):
    def error(self, message):
        print(
            "Usage: python3 matamazon.py -l <matamazon_log> -s <matamazon_system> -o <output_file> -os <out_matamazon_system>",
            file=sys.stderr)
        sys.exit(1)


def main():
    parser = CustomParser(add_help=False)
    parser.add_argument('-l', required=True)
    parser.add_argument('-s', required=False)
    parser.add_argument('-o', required=False)
    parser.add_argument('-os', required=False)

    try:
        args, unknown = parser.parse_known_args()
        if unknown:
            raise ValueError("Unknown arguments")
    except Exception:
        print(
            "Usage: python3 matamazon.py -l <matamazon_log> -s <matamazon_system> -o <output_file> -os <out_matamazon_system>",
            file=sys.stderr)
        sys.exit(1)

    try:
        system = load_system_from_file(args.s) if args.s else MatamazonSystem()
        with open(args.l, 'r') as log_file:
            for line in log_file:
                parts = line.strip().split()
                if not parts: continue
                cmd = parts[0]

                if cmd == 'register':
                    is_cust = parts[1] == 'customer'
                    entity_class = Customer if is_cust else Supplier
                    system.register_entity(
                        entity_class(int(parts[2]), parts[3].replace('_', ' '), parts[4].replace('_', ' '),
                                     parts[5].replace('_', ' ')), is_cust)
                elif cmd in ('add', 'update'):
                    system.add_or_update_product(
                        Product(int(parts[1]), parts[2].replace('_', ' '), float(parts[3]), int(parts[4]),
                                int(parts[5])))
                elif cmd == 'order':
                    system.place_order(int(parts[1]), int(parts[2]), int(parts[3]) if len(parts) > 3 else 1)
                elif cmd == 'remove':
                    system.remove_object(int(parts[2]), parts[1])
                elif cmd == 'search':
                    max_p = float(parts[2]) if len(parts) > 2 else None
                    print(system.search_products(parts[1].replace('_', ' '), max_p))

        if args.o:
            with open(args.o, 'w') as out_f:
                system.export_orders(out_f)
        else:
            system.export_orders(sys.stdout)
            print()

        if args.os:
            system.export_system_to_file(args.os)

    except Exception:
        print("The matamazon script has encountered an error")
        sys.exit(1)


if __name__ == "__main__":
    main()