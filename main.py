import argparse
import sys
import json


class InvalidIdException(Exception): pass


class InvalidPriceException(Exception): pass


class Customer:
    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0: raise InvalidIdException("Invalid Customer ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __repr__(self):
        return f"Customer(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"


class Supplier:
    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0: raise InvalidIdException("Invalid Supplier ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __repr__(self):
        return f"Supplier(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"


class Product:
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
    def __init__(self):
        self.customers = {}
        self.suppliers = {}
        self.products = {}
        self.orders = {}
        self.next_order_id = 1

    def register_entity(self, entity, is_customer):
        if is_customer:
            if entity.id in self.customers: raise InvalidIdException("Customer ID exists")
            self.customers[entity.id] = entity
        else:
            if entity.id in self.suppliers: raise InvalidIdException("Supplier ID exists")
            self.suppliers[entity.id] = entity

    def add_or_update_product(self, product):
        if product.supplier_id not in self.suppliers:
            raise InvalidIdException("Supplier does not exist")
        if product.id in self.products and self.products[product.id].supplier_id != product.supplier_id:
            raise InvalidIdException("Product exists for a different supplier")
        self.products[product.id] = product

    def place_order(self, customer_id, product_id, quantity=1):
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

    def remove_object(self, id, class_type):
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
        results = [p for p in self.products.values() if query in p.name and p.quantity > 0]
        if max_price is not None:
            results = [p for p in results if p.price <= float(max_price)]
        return sorted(results)

    def export_system_to_file(self, path):
        with open(path, 'w') as f:
            for c in self.customers.values(): f.write(str(c) + '\n')
            for s in self.suppliers.values(): f.write(str(s) + '\n')
            for p in self.products.values(): f.write(str(p) + '\n')

    def export_orders(self, out_file):
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