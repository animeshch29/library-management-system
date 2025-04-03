import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import heapq
from collections import defaultdict, OrderedDict

class Book:
    def __init__(self, book_id, title, author, total_copies):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.reservations = []  # Priority queue for reservations

    def __str__(self):
        return f"{self.title} by {self.author} (ID: {self.book_id}, Available: {self.available_copies}/{self.total_copies})"

class Member:
    def __init__(self, member_id, name, email):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.borrowed_books = {}  # book_id: due_date
        self.fines = 0

    def __str__(self):
        return f"{self.name} (ID: {self.member_id}, Fines: ${self.fines:.2f})"

class Library:
    def __init__(self):
        self.books = {}  # book_id: Book object
        self.members = {}  # member_id: Member object
        self.title_index = defaultdict(set)
        self.author_index = defaultdict(set)
        self.catalog = OrderedDict()
        self.LOAN_PERIOD = 14  # days
        self.FINE_PER_DAY = 0.50  # dollars

    def add_book(self, book_id, title, author, total_copies):
        if book_id in self.books:
            return False, "Book ID already exists."
        
        book = Book(book_id, title, author, total_copies)
        self.books[book_id] = book
        self.title_index[title.lower()].add(book_id)
        self.author_index[author.lower()].add(book_id)
        self.catalog[book_id] = book
        return True, f"Book '{title}' added successfully."

    def register_member(self, member_id, name, email):
        if member_id in self.members:
            return False, "Member ID already exists."
        
        member = Member(member_id, name, email)
        self.members[member_id] = member
        return True, f"Member '{name}' registered successfully."

    def borrow_book(self, member_id, book_id):
        if member_id not in self.members:
            return False, "Invalid member ID."
        
        if book_id not in self.books:
            return False, "Invalid book ID."
        
        member = self.members[member_id]
        book = self.books[book_id]
        
        if len(member.borrowed_books) >= 5:
            return False, "Member has reached the maximum borrowing limit (5 books)."
        
        if book.available_copies > 0:
            due_date = datetime.now() + timedelta(days=self.LOAN_PERIOD)
            member.borrowed_books[book_id] = due_date
            book.available_copies -= 1
            return True, f"Book '{book.title}' borrowed successfully. Due date: {due_date.strftime('%Y-%m-%d')}"
        else:
            return False, "All copies of this book are currently checked out."

    def return_book(self, member_id, book_id):
        if member_id not in self.members:
            return False, "Invalid member ID."
        
        if book_id not in self.books:
            return False, "Invalid book ID."
        
        member = self.members[member_id]
        book = self.books[book_id]
        
        if book_id not in member.borrowed_books:
            return False, "This member hasn't borrowed this book."
        
        # Calculate fines if overdue
        due_date = member.borrowed_books[book_id]
        fine = 0
        if datetime.now() > due_date:
            days_overdue = (datetime.now() - due_date).days
            fine = days_overdue * self.FINE_PER_DAY
            member.fines += fine
        
        # Return the book
        del member.borrowed_books[book_id]
        book.available_copies += 1
        
        # Process next reservation if any
        reservation_msg = ""
        if book.reservations:
            next_member_id = heapq.heappop(book.reservations)[1]
            success, msg = self.borrow_book(next_member_id, book_id)
            if success:
                reservation_msg = f"\nBook automatically checked out to reserved member (ID: {next_member_id})"
        
        return True, f"Book '{book.title}' returned successfully. Fine: ${fine:.2f}{reservation_msg}"

    def reserve_book(self, member_id, book_id):
        if member_id not in self.members:
            return False, "Invalid member ID."
        
        if book_id not in self.books:
            return False, "Invalid book ID."
        
        book = self.books[book_id]
        reservation_time = datetime.now()
        ''' hepa'''
        heapq.heappush(book.reservations, (reservation_time, member_id))
        return True, f"Book '{book.title}' reserved successfully. You'll be notified when available."

    def search_books(self, title="", author=""):
        results = []
        
        if title:
            title = title.lower()
            if title in self.title_index:
                for book_id in self.title_index[title]:
                    results.append(self.books[book_id])
        
        if author:
            author = author.lower()
            if author in self.author_index:
                for book_id in self.author_index[author]:
                    results.append(self.books[book_id])
        
        return list(set(results))  # Remove duplicates if any

    def get_overdue_books(self):
        overdue = []
        today = datetime.now()
        
        for member in self.members.values():
            for book_id, due_date in member.borrowed_books.items():
                if today > due_date:
                    book = self.books[book_id]
                    days_overdue = (today - due_date).days
                    fine = days_overdue * self.FINE_PER_DAY
                    overdue.append({
                        'member': member,
                        'book': book,
                        'due_date': due_date,
                        'days_overdue': days_overdue,
                        'fine': fine
                    })
        
        return overdue

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("1000x700")
        
        self.library = Library()
        
        # Add some sample data
        self._add_sample_data()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        self.tab_books = ttk.Frame(self.tab_control)
        self.tab_members = ttk.Frame(self.tab_control)
        self.tab_transactions = ttk.Frame(self.tab_control)
        self.tab_search = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_books, text="Books")
        self.tab_control.add(self.tab_members, text="Members")
        self.tab_control.add(self.tab_transactions, text="Transactions")
        self.tab_control.add(self.tab_search, text="Search")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Setup each tab
        self._setup_books_tab()
        self._setup_members_tab()
        self._setup_transactions_tab()
        self._setup_search_tab()
    
    def _add_sample_data(self):
        # Add sample books
        books = [
            ("B001", "The Great Gatsby", "F. Scott Fitzgerald", 3),
            ("B002", "To Kill a Mockingbird", "Harper Lee", 2),
            ("B003", "1984", "George Orwell", 4),
            ("B004", "Pride and Prejudice", "Jane Austen", 3),
            ("B005", "The Hobbit", "J.R.R. Tolkien", 2)
        ]
        
        for book in books:
            self.library.add_book(*book)
        
        # Add sample members
        members = [
            ("M001", "Alice Johnson", "alice@example.com"),
            ("M002", "Bob Smith", "bob@example.com"),
            ("M003", "Charlie Brown", "charlie@example.com")
        ]
        
        for member in members:
            self.library.register_member(*member)
    
    def _setup_books_tab(self):
        # Add Book Frame
        add_frame = ttk.LabelFrame(self.tab_books, text="Add New Book", padding=10)
        add_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_frame, text="Book ID:").grid(row=0, column=0, sticky="e")
        self.book_id_entry = ttk.Entry(add_frame)
        self.book_id_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Title:").grid(row=1, column=0, sticky="e")
        self.title_entry = ttk.Entry(add_frame)
        self.title_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Author:").grid(row=2, column=0, sticky="e")
        self.author_entry = ttk.Entry(add_frame)
        self.author_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Copies:").grid(row=3, column=0, sticky="e")
        self.copies_entry = ttk.Entry(add_frame)
        self.copies_entry.grid(row=3, column=1, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Add Book", command=self.add_book).grid(row=4, column=1, pady=5)
        
        # Book List Frame
        list_frame = ttk.LabelFrame(self.tab_books, text="Book Catalog", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("ID", "Title", "Author", "Available", "Total")
        self.book_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.book_tree.heading(col, text=col)
            self.book_tree.column(col, width=120, anchor="center")
        
        self.book_tree.column("Title", width=200)
        self.book_tree.column("Author", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=scrollbar.set)
        
        self.book_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_book_list()
    
    def _setup_members_tab(self):
        # Add Member Frame
        add_frame = ttk.LabelFrame(self.tab_members, text="Register New Member", padding=10)
        add_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_frame, text="Member ID:").grid(row=0, column=0, sticky="e")
        self.member_id_entry = ttk.Entry(add_frame)
        self.member_id_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Name:").grid(row=1, column=0, sticky="e")
        self.member_name_entry = ttk.Entry(add_frame)
        self.member_name_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Email:").grid(row=2, column=0, sticky="e")
        self.member_email_entry = ttk.Entry(add_frame)
        self.member_email_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Register Member", command=self.register_member).grid(row=3, column=1, pady=5)
        
        # Member List Frame
        list_frame = ttk.LabelFrame(self.tab_members, text="Member Directory", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("ID", "Name", "Email", "Borrowed", "Fines")
        self.member_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.member_tree.heading(col, text=col)
            self.member_tree.column(col, width=120, anchor="center")
        
        self.member_tree.column("Name", width=150)
        self.member_tree.column("Email", width=200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.member_tree.yview)
        self.member_tree.configure(yscrollcommand=scrollbar.set)
        
        self.member_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_member_list()
    
    def _setup_transactions_tab(self):
        # Borrow Book Frame
        borrow_frame = ttk.LabelFrame(self.tab_transactions, text="Borrow Book", padding=10)
        borrow_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(borrow_frame, text="Member ID:").grid(row=0, column=0, sticky="e")
        self.borrow_member_entry = ttk.Entry(borrow_frame)
        self.borrow_member_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(borrow_frame, text="Book ID:").grid(row=1, column=0, sticky="e")
        self.borrow_book_entry = ttk.Entry(borrow_frame)
        self.borrow_book_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(borrow_frame, text="Borrow Book", command=self.borrow_book).grid(row=2, column=1, pady=5)
        
        # Return Book Frame
        return_frame = ttk.LabelFrame(self.tab_transactions, text="Return Book", padding=10)
        return_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(return_frame, text="Member ID:").grid(row=0, column=0, sticky="e")
        self.return_member_entry = ttk.Entry(return_frame)
        self.return_member_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(return_frame, text="Book ID:").grid(row=1, column=0, sticky="e")
        self.return_book_entry = ttk.Entry(return_frame)
        self.return_book_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(return_frame, text="Return Book", command=self.return_book).grid(row=2, column=1, pady=5)
        
        # Reserve Book Frame
        reserve_frame = ttk.LabelFrame(self.tab_transactions, text="Reserve Book", padding=10)
        reserve_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(reserve_frame, text="Member ID:").grid(row=0, column=0, sticky="e")
        self.reserve_member_entry = ttk.Entry(reserve_frame)
        self.reserve_member_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(reserve_frame, text="Book ID:").grid(row=1, column=0, sticky="e")
        self.reserve_book_entry = ttk.Entry(reserve_frame)
        self.reserve_book_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(reserve_frame, text="Reserve Book", command=self.reserve_book).grid(row=2, column=1, pady=5)
    
    def _setup_search_tab(self):
        # Search Frame
        search_frame = ttk.LabelFrame(self.tab_search, text="Search Books", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="Title:").grid(row=0, column=0, sticky="e")
        self.search_title_entry = ttk.Entry(search_frame)
        self.search_title_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(search_frame, text="Author:").grid(row=1, column=0, sticky="e")
        self.search_author_entry = ttk.Entry(search_frame)
        self.search_author_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(search_frame, text="Search", command=self.search_books).grid(row=2, column=1, pady=5)
        
        # Results Frame
        results_frame = ttk.LabelFrame(self.tab_search, text="Search Results", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("ID", "Title", "Author", "Available", "Total")
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120, anchor="center")
        
        self.search_tree.column("Title", width=200)
        self.search_tree.column("Author", width=150)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        
        self.search_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def add_book(self):
        book_id = self.book_id_entry.get()
        title = self.title_entry.get()
        author = self.author_entry.get()
        
        try:
            copies = int(self.copies_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for copies")
            return
        
        success, msg = self.library.add_book(book_id, title, author, copies)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_book_list()
            self.book_id_entry.delete(0, tk.END)
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.copies_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)
    
    def register_member(self):
        member_id = self.member_id_entry.get()
        name = self.member_name_entry.get()
        email = self.member_email_entry.get()
        
        success, msg = self.library.register_member(member_id, name, email)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_member_list()
            self.member_id_entry.delete(0, tk.END)
            self.member_name_entry.delete(0, tk.END)
            self.member_email_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)
    
    def borrow_book(self):
        member_id = self.borrow_member_entry.get()
        book_id = self.borrow_book_entry.get()
        
        success, msg = self.library.borrow_book(member_id, book_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_book_list()
            self.refresh_member_list()
            self.borrow_member_entry.delete(0, tk.END)
            self.borrow_book_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)
    
    def return_book(self):
        member_id = self.return_member_entry.get()
        book_id = self.return_book_entry.get()
        
        success, msg = self.library.return_book(member_id, book_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_book_list()
            self.refresh_member_list()
            self.return_member_entry.delete(0, tk.END)
            self.return_book_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)
    
    def reserve_book(self):
        member_id = self.reserve_member_entry.get()
        book_id = self.reserve_book_entry.get()
        
        success, msg = self.library.reserve_book(member_id, book_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.reserve_member_entry.delete(0, tk.END)
            self.reserve_book_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)
    
    def search_books(self):
        title = self.search_title_entry.get()
        author = self.search_author_entry.get()
        
        results = self.library.search_books(title, author)
        
        # Clear previous results
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        if not results:
            messagebox.showinfo("Search Results", "No books found matching your criteria")
            return
        
        for book in results:
            self.search_tree.insert("", "end", values=(
                book.book_id,
                book.title,
                book.author,
                book.available_copies,
                book.total_copies
            ))
    
    def refresh_book_list(self):
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        
        for book in self.library.books.values():
            self.book_tree.insert("", "end", values=(
                book.book_id,
                book.title,
                book.author,
                book.available_copies,
                book.total_copies
            ))
    
    def refresh_member_list(self):
        for item in self.member_tree.get_children():
            self.member_tree.delete(item)
        
        for member in self.library.members.values():
            self.member_tree.insert("", "end", values=(
                member.member_id,
                member.name,
                member.email,
                len(member.borrowed_books),
                f"${member.fines:.2f}"
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
