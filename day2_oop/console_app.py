"""
+ Design a Human Resource Management (HRM) System using OOP (Console app)
+ Features: Register, Login, CRUD employees, Statistics
+ Requirements: OOP + Inheritance, Context manager, Decorator, Synthetic data
"""

from datetime import datetime, date
from functools import wraps
from pathlib import Path
from typing import Optional, List, Dict
import csv
import json
import os


RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"


def ok(message: str) -> str:
    return f"{GREEN}[OK]{RESET} {message}"


def error(message: str) -> str:
    return f"{RED}[ERROR]{RESET} {message}"


# ============== DECORATOR ==============
def login_required(role_required: List[str] = None):
    """Decorator: Kiểm tra quyền truy cập"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                print(error("You are not logged in! Please login first."))
                return
            
            if role_required and self.current_user['role'] not in role_required:
                print(error(f"Access denied! Only {', '.join(role_required)} are allowed."))
                return
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# ============== CONTEXT MANAGER ==============
class FileManager:
    """Context manager for reading/writing files"""
    def __init__(self, filename: str, mode: str = 'r', encoding: str = 'utf-8'):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filename, self.mode, encoding=self.encoding)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return False


# ============== CLASS ==============
class Account:
    """Class to manage user accounts"""
    def __init__(self, username: str, password: str, role: str):
        self.username = username
        self.password = password
        self.role = role  # Manager, Director
    
    def to_dict(self):
        return {"username": self.username, "password": self.password, "role": self.role}
    
    @staticmethod
    def from_dict(data: dict):
        return Account(data['username'], data['password'], data['role'])


class Employee:
    """Class representing an employee"""
    def __init__(self, emp_id: str, name: str, birth_year: int, department: str, 
                 salary: float, position: str, start_date: str):
        self.emp_id = emp_id
        self.name = name
        self.birth_year = birth_year
        self.department = department  # IT, Marketing, Media
        self.salary = salary
        self.position = position  # Intern, Employee, Manager, Director
        self.start_date = start_date  # YYYY-MM-DD
    
    def to_list(self):
        return [self.emp_id, self.name, self.birth_year, self.department, 
                self.salary, self.position, self.start_date]
    
    def to_dict(self):
        return {
            'emp_id': self.emp_id,
            'name': self.name,
            'birth_year': self.birth_year,
            'department': self.department,
            'salary': self.salary,
            'position': self.position,
            'start_date': self.start_date
        }


class BaseHRM:
    """Base class for HRM system"""
    def __init__(self):
        self.hrm_file = "hrm.txt"
        self.employee_file = "employee.csv"
        self.current_user: Optional[Dict] = None
    
    def _load_accounts(self) -> Dict[str, dict]:
        """Load accounts from hrm.txt"""
        accounts = {}
        try:
            with FileManager(self.hrm_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        username, password, role = line.split('|')
                        accounts[username] = {"password": password.strip(), "role": role.strip()}
        except FileNotFoundError:
            pass
        return accounts
    
    def _save_account(self, username: str, password: str, role: str):
        """Save account to hrm.txt"""
        with FileManager(self.hrm_file, 'a') as f:
            f.write(f"{username}|{password}|{role}\n")
    
    def _load_employees(self) -> List[Employee]:
        """Load employees from employee.csv"""
        employees = []
        try:
            with FileManager(self.employee_file, 'r') as f:
                reader = csv.reader(f)
                try:
                    next(reader)  # Skip header
                except StopIteration:
                    return []  # File is empty
                for row in reader:
                    if row:
                        emp = Employee(row[0], row[1], int(row[2]), row[3], 
                                     float(row[4]), row[5], row[6])
                        employees.append(emp)
        except FileNotFoundError:
            pass
        return employees
    
    def _save_employees(self, employees: List[Employee]):
        """Save employees to employee.csv"""
        with FileManager(self.employee_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['emp_id', 'name', 'birth_year', 'department', 'salary', 'position', 'start_date'])
            for emp in employees:
                writer.writerow(emp.to_list())


class HRM(BaseHRM):
    """Class to manage the HRM system"""
    
    def register(self, username: str, password: str, role: str):
        """Register a new account"""
        accounts = self._load_accounts()
        
        if username in accounts:
            print(error(f"Account '{username}' already exists!"))
            return
        
        if role not in ['Manager', 'Director']:
            print(error("Invalid role! Only Manager and Director are allowed."))
            return
        
        self._save_account(username, password, role)
        print(ok(f"Registration successful! Username: {username}, Role: {role}"))
    
    def login(self, username: str, password: str):
        """Login to the system"""
        accounts = self._load_accounts()
        
        if username not in accounts:
            print(error("Account does not exist!"))
            return False
        
        if accounts[username]['password'] != password:
            print(error("Password is incorrect!"))
            return False
        
        role = accounts[username]['role']
        
        self.current_user = {'username': username, 'role': role}
        print(f"\n{ok(f'Login successful! Hello {username} ({role})')}")
        return True
    
    def logout(self):
        """Logout from the system"""
        if not self.current_user:
            print(error("You are not logged in!"))
            return
        
        username = self.current_user['username']
        self.current_user = None
        print(ok(f"{username} has logged out successfully!"))
    
    @login_required(role_required=['Manager', 'Director'])
    def create_employee(self, emp_id: str, name: str, birth_year: int, 
                       department: str, salary: float, position: str, start_date: str):
        """Create a new employee profile"""
        employees = self._load_employees()
        
        if any(e.emp_id == emp_id for e in employees):
            print(error(f"Employee with ID '{emp_id}' already exists!"))
            return
        
        if department not in ['IT', 'Marketing', 'Media']:
            print(error("Invalid department! (IT, Marketing, Media)"))
            return
        
        emp = Employee(emp_id, name, birth_year, department, salary, position, start_date)
        employees.append(emp)
        self._save_employees(employees)
        print(ok(f"Employee created successfully! ID: {emp_id}, Name: {name}"))
    
    @login_required(role_required=['Manager', 'Director'])
    def delete_employee(self, emp_id: str):
        """Delete employee information"""
        employees = self._load_employees()
        original_count = len(employees)
        employees = [e for e in employees if e.emp_id != emp_id]
        
        if len(employees) == original_count:
            print(error(f"Employee with ID '{emp_id}' not found!"))
            return
        
        self._save_employees(employees)
        print(ok(f"Employee ID '{emp_id}' deleted successfully!"))
    
    @login_required(role_required=['Manager', 'Director'])
    def view_employee_salary(self, emp_id: str):
        """View salary of an employee"""
        employees = self._load_employees()
        
        for emp in employees:
            if emp.emp_id == emp_id:
                print(f"\n[INFO] Employee Salary Information:")
                print(f"   ID: {emp.emp_id}")
                print(f"   Name: {emp.name}")
                print(f"   Salary: ${emp.salary:,.2f}")
                return
        
        print(error(f"Employee with ID '{emp_id}' not found!"))
    
    @login_required(role_required=['Manager', 'Director'])
    def count_employees_by_department(self):
        """View employee count by department"""
        employees = self._load_employees()
        dept_count = {}
        
        for emp in employees:
            dept_count[emp.department] = dept_count.get(emp.department, 0) + 1
        
        if not dept_count:
            print(error("No employees found!"))
            return
        
        print("\n[INFO] Employee Statistics by Department:")
        print("-" * 40)
        for dept, count in sorted(dept_count.items()):
            print(f"   {dept}: {count} employees")
        print(f"   Total: {len(employees)} employees")
        print("-" * 40)
    
    @login_required(role_required=['Manager', 'Director'])
    def update_employee_salary(self, emp_id: str, new_salary: float):
        """Update employee salary"""
        employees = self._load_employees()
        
        for emp in employees:
            if emp.emp_id == emp_id:
                old_salary = emp.salary
                emp.salary = new_salary
                self._save_employees(employees)
                print(ok("Salary updated successfully!"))
                print(f"   ID: {emp_id}, Name: {emp.name}")
                print(f"   Old salary: ${old_salary:,.2f} -> New salary: ${new_salary:,.2f}")
                return
        
            print(error(f"Employee with ID '{emp_id}' not found!"))
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("     HUMAN RESOURCE MANAGEMENT SYSTEM (HRM)")
        print("="*50)
        print("1. Register Account")
        print("2. Login")
        print("3. Create New Employee Profile")
        print("4. Delete Employee Information")
        print("5. View Employee Salary")
        print("6. Employee Statistics by Department")
        print("7. Update Employee Salary")
        print("8. Logout")
        print("0. Exit Program")
        print("="*50)
        print(f"Status: {ok('Logged In') if self.current_user else error('Not Logged In')}")
        if self.current_user:
            print(f"User: {self.current_user['username']} ({self.current_user['role']})")
        print("="*50)
    
    def run(self):
        """Run the application"""
        print("\n[INFO] Welcome to the HRM System!")
        
        while True:
            self.show_menu()
            choice = input("\n[INPUT] Select option (0-8): ").strip()
            
            if choice == '1':
                print("\n[ACTION] REGISTER ACCOUNT")
                print("-" * 50)
                username = input("Enter username: ").strip()
                password = input("Enter password: ").strip()
                print("Position: 1.Manager, 2.Director")
                role_choice = input("Choose position (1-2): ").strip()
                role_map = {'1': 'Manager', '2': 'Director'}
                role = role_map.get(role_choice)
                if role:
                    self.register(username, password, role)
                else:
                    print(error("Invalid position selection! Only Manager or Director are allowed."))
            
            elif choice == '2':
                if self.current_user:
                    print(error("You are already logged in! Please logout first."))
                else:
                    print("\n[ACTION] LOGIN")
                    print("-" * 50)
                    username = input("Enter username: ").strip()
                    password = input("Enter password: ").strip()
                    self.login(username, password)
            
            elif choice == '3':
                print("\n[ACTION] CREATE NEW EMPLOYEE PROFILE")
                print("-" * 50)
                try:
                    emp_id = input("Enter employee ID: ").strip()
                    name = input("Enter employee name: ").strip()
                    birth_year = int(input("Enter birth year: "))
                    print("Department: 1.IT, 2.Marketing, 3.Media")
                    dept_choice = input("Choose department (1-3): ").strip()
                    dept_map = {'1': 'IT', '2': 'Marketing', '3': 'Media'}
                    department = dept_map.get(dept_choice)
                    salary = float(input("Enter salary ($): "))
                    print("Position: 1.Intern, 2.Employee, 3.Manager, 4.Director")
                    pos_choice = input("Choose position (1-4): ").strip()
                    pos_map = {'1': 'Intern', '2': 'Employee', '3': 'Manager', '4': 'Director'}
                    position = pos_map.get(pos_choice)
                    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                    
                    if department and position:
                        self.create_employee(emp_id, name, birth_year, department, salary, position, start_date)
                    else:
                        print(error("Invalid input!"))
                except ValueError:
                    print(error("Invalid data entered!"))
            
            elif choice == '4':
                print("\n[ACTION] DELETE EMPLOYEE INFORMATION")
                print("-" * 50)
                emp_id = input("Enter employee ID to delete: ").strip()
                self.delete_employee(emp_id)
            
            elif choice == '5':
                print("\n[ACTION] VIEW EMPLOYEE SALARY")
                print("-" * 50)
                emp_id = input("Enter employee ID: ").strip()
                self.view_employee_salary(emp_id)
            
            elif choice == '6':
                self.count_employees_by_department()
            
            elif choice == '7':
                print("\n[ACTION] UPDATE EMPLOYEE SALARY")
                print("-" * 50)
                try:
                    emp_id = input("Enter employee ID: ").strip()
                    new_salary = float(input("Enter new salary ($): "))
                    self.update_employee_salary(emp_id, new_salary)
                except ValueError:
                    print(error("Salary must be a number!"))
            
            elif choice == '8':
                self.logout()
            
            elif choice == '0':
                print("\n[INFO] Thank you for using the HRM system. Goodbye!")
                break
            
            else:
                print(error("Invalid option!"))



# ============== MAIN ==============
if __name__ == "__main__":
    
    hrm = HRM()
    hrm.run()