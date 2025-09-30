import sys
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from collections import defaultdict
import hashlib

# ——— Constants ———
USERS_FILE   = "users.csv"
EXPENSES_FILE= "expenses.csv"
BUDGETS_FILE = "budgets.csv"
STATS_FILE   = "user_stats.csv"

# ——— Helpers ———
def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def init_files():
    for fname, header in [
        (USERS_FILE, ["username","password"]),
        (EXPENSES_FILE, ["username","date","amount","category","description"]),
        (BUDGETS_FILE, ["username","budget"]),
        (STATS_FILE, ["username","total"])
    ]:
        if not os.path.exists(fname):
            with open(fname,"w",newline="") as f:
                csv.writer(f).writerow(header)

# ——— User & Data Logic ———
def register_user(username,password):
    with open(USERS_FILE,"r") as f:
        rows=list(csv.DictReader(f))
        if any(r["username"]==username for r in rows):
            return False,"Username already exists."
    with open(USERS_FILE,"a",newline="") as f:
        csv.writer(f).writerow([username,hash_pwd(password)])
    with open(BUDGETS_FILE,"a",newline="") as f:
        csv.writer(f).writerow([username,0])
    with open(STATS_FILE,"a",newline="") as f:
        csv.writer(f).writerow([username,0])
    return True,"Registered successfully."

def login_user(username,password):
    with open(USERS_FILE,"r") as f:
        for row in csv.DictReader(f):
            if row["username"]==username and row["password"]==hash_pwd(password):
                return True
    return False

def add_expense(username,amt,cat,desc):
    with open(EXPENSES_FILE,"a",newline="") as f:
        csv.writer(f).writerow([
            username,
            datetime.now().strftime("%Y-%m-%d"),
            amt,cat,desc
        ])
    update_stats(username)

def view_expenses(username):
    with open(EXPENSES_FILE,"r") as f:
        return [r for r in csv.DictReader(f) if r["username"]==username]

def search_expenses(username,kw):
    kw=kw.lower()
    return [e for e in view_expenses(username)
            if kw in e["category"].lower() or kw in e["description"].lower()]

def view_monthly_expenses(username,month):
    return [e for e in view_expenses(username) if e["date"].startswith(month)]

def get_budget(username):
    with open(BUDGETS_FILE,"r") as f:
        for row in csv.DictReader(f):
            if row["username"]==username:
                return float(row["budget"])
    return 0.0

def set_budget(username,amt):
    rows=[]
    with open(BUDGETS_FILE,"r") as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        if r["username"]==username:
            r["budget"]=str(amt)
    with open(BUDGETS_FILE,"w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["username","budget"])
        writer.writeheader(); writer.writerows(rows)

def calculate_total(username):
    expenses=view_expenses(username)
    total=sum(float(e["amount"]) for e in expenses)
    budget=get_budget(username)
    status="Under Budget" if total<=budget else "Over Budget"
    return total,budget,status

def delete_expense(username,index):
    expenses=[]
    with open(EXPENSES_FILE,"r") as f:
        expenses=list(csv.DictReader(f))
    user_exp=[e for e in expenses if e["username"]==username]
    if 0<=index-1<len(user_exp):
        target=user_exp[index-1]
        expenses.remove(target)
    with open(EXPENSES_FILE,"w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["username","date","amount","category","description"])
        writer.writeheader(); writer.writerows(expenses)
    update_stats(username)

def update_stats(username):
    total=sum(float(e["amount"]) for e in view_expenses(username))
    rows=[]
    with open(STATS_FILE,"r") as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        if r["username"]==username:
            r["total"]=str(total)
    with open(STATS_FILE,"w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["username","total"])
        writer.writeheader(); writer.writerows(rows)

def show_expenses_pie_chart(username):
    d=defaultdict(float)
    for e in view_expenses(username):
        d[e["category"]]+=float(e["amount"])
    if not d:
        messagebox.showinfo("No Data","No expenses to show.")
        return
    plt.pie(d.values(),labels=d.keys(),autopct="%1.1f%%")
    plt.title("Expenses by Category")
    plt.show()

# ——— GUI App ———
class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("900x600")
        init_files()
        self.current_user=None
        self.content=ttk.Frame(self)
        self.content.place(relx=0.5,rely=0.5,anchor="center")
        self.login_screen()

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def login_screen(self):
        self.clear()
        ttk.Label(self.content,text="Login / Register",font=("Arial",18)).pack(pady=10)
        ttk.Label(self.content,text="Username:").pack()
        self.ent_user=ttk.Entry(self.content); self.ent_user.pack(pady=5)
        ttk.Label(self.content,text="Password:").pack()
        self.ent_pwd=ttk.Entry(self.content,show="*"); self.ent_pwd.pack(pady=5)
        ttk.Button(self.content,text="Login",command=self.do_login).pack(pady=5)
        ttk.Button(self.content,text="Register",command=self.do_register).pack()

    def do_register(self):
        u,p=self.ent_user.get(),self.ent_pwd.get()
        ok,msg=register_user(u,p)
        messagebox.showinfo("Register",msg) if ok else messagebox.showerror("Register",msg)

    def do_login(self):
        u,p=self.ent_user.get(),self.ent_pwd.get()
        if login_user(u,p):
            self.current_user=u
            self.menu_screen()
        else:
            messagebox.showerror("Login Failed","Invalid credentials.")

    def menu_screen(self):
        self.clear()
        ttk.Label(self.content,text=f"Welcome, {self.current_user}",font=("Arial",16)).pack(pady=10)
        for opt in [
            "Add Expense","View Expenses","Search Expenses",
            "Monthly Expenses","Set Budget","Calculate Total",
            "View Pie Chart","Logout"
        ]:
            ttk.Button(self.content,text=opt,width=30,
                       command=lambda o=opt:self.handle(o)).pack(pady=3)

    def show_expenses_table(self,expenses):
        self.clear()
        ttk.Button(self.content,text="Back to Menu",command=self.menu_screen).pack(pady=5,anchor="w")
        ttk.Label(self.content,text="Your Expenses",font=("Arial",16)).pack(pady=10)
        frame=ttk.Frame(self.content); frame.pack(fill='both',expand=True,padx=20,pady=10)
        scroll_y=ttk.Scrollbar(frame); scroll_y.pack(side='right',fill='y')
        scroll_x=ttk.Scrollbar(frame,orient='horizontal'); scroll_x.pack(side='bottom',fill='x')
        self.tree=ttk.Treeview(frame,yscrollcommand=scroll_y.set,xscrollcommand=scroll_x.set,
                      columns=("index","date","amount","category","description"),selectmode='browse')
        self.tree.pack(fill='both',expand=True)
        scroll_y.config(command=self.tree.yview); scroll_x.config(command=self.tree.xview)
        self.tree.column("#0",width=0,stretch=tk.NO)
        for col,w in [("index",60),("date",100),("amount",100),("category",150),("description",300)]:
            self.tree.column(col,width=w,anchor='center')
            self.tree.heading(col,text=col.capitalize())
        for idx,e in enumerate(expenses,start=1):
            self.tree.insert("",'end',values=(idx,e['date'],f"₹{e['amount']}",e['category'],e['description']))
        total=sum(float(e['amount']) for e in expenses)
        ttk.Label(self.content,text=f"Total Expenses: ₹{total:.2f}",font=("Arial",12,'bold')).pack(pady=10)

        # Add Delete Selected button
        ttk.Button(self.content, text="Delete Selected", command=self.delete_selected_row).pack(pady=5)

    def delete_selected_row(self):
        selected=self.tree.selection()
        if not selected:
            messagebox.showwarning("Delete","No row selected.")
            return
        idx=int(self.tree.item(selected[0])['values'][0])
        confirm=messagebox.askyesno("Confirm Delete",f"Delete expense #{idx}?")
        if confirm:
            delete_expense(self.current_user, idx)
            messagebox.showinfo("Deleted","Expense deleted successfully.")
            self.show_expenses_table(view_expenses(self.current_user))

    def handle(self,opt):
        u=self.current_user
        if opt=="Add Expense":
            amt=simpledialog.askfloat("Amount","Enter amount:",parent=self)
            cat=simpledialog.askstring("Category","Enter category:",parent=self)
            desc=simpledialog.askstring("Description","Enter description:",parent=self)
            if amt and cat and desc: add_expense(u,amt,cat,desc)
        elif opt=="View Expenses":
            ex=view_expenses(u)
            messagebox.showinfo("Expenses","No expenses to show.") if not ex else self.show_expenses_table(ex)
        elif opt=="Search Expenses":
            kw=simpledialog.askstring("Search","Keyword:") or ""
            res=search_expenses(u,kw)
            messagebox.showinfo("Results","\n".join(f"{e['date']} ₹{e['amount']} {e['category']}" for e in res) or "No matches.")
        elif opt=="Monthly Expenses":
            m=simpledialog.askstring("Month","YYYY-MM:") or ""
            res=view_monthly_expenses(u,m)
            messagebox.showinfo("Monthly","\n".join(f"{e['date']} ₹{e['amount']} {e['category']}" for e in res) or "No records.")
        elif opt=="Set Budget":
            b=simpledialog.askfloat("Budget","Enter budget:")
            set_budget(u,b) if b is not None else None
        elif opt=="Calculate Total":
            tot,bud,st=calculate_total(u)
            messagebox.showinfo("Budget Status",f"Total: ₹{tot}\nBudget: ₹{bud}\n{st}")
        elif opt=="View Pie Chart":
            show_expenses_pie_chart(u)
        elif opt=="Logout":
            self.current_user=None
            self.login_screen()

if __name__=="__main__":
    app=ExpenseApp()
    app.mainloop()
