import tkinter as tk
from tkinter import ttk, messagebox
import requests

class CongressApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Congress.gov Explorer")

        self.member_id_map = {}
        self.bill_details_map = {}

        # API Key Entry
        self.api_key_label = tk.Label(root, text="Congress.gov API Key:")
        self.api_key_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.api_key_entry = tk.Entry(root, width=50)
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # State Selection
        self.state_label = tk.Label(root, text="Select State:")
        self.state_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.state_combobox = ttk.Combobox(root, values=self.get_states(), state="readonly")
        self.state_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.state_combobox.bind("<<ComboboxSelected>>", self.on_state_selected)

        # Set default state to Texas ('TX')
        self.state_combobox.set('TX')

        # Current Members Checkbox
        self.current_members_var = tk.BooleanVar(value=True)
        self.current_members_check = tk.Checkbutton(root, text="Current Members Only", variable=self.current_members_var)
        self.current_members_check.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.current_members_check.bind("<ButtonRelease-1>", self.on_state_selected)

        # Members Listbox
        self.members_label = tk.Label(root, text="Members:")
        self.members_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.members_listbox = tk.Listbox(root, width=50, height=10)
        self.members_listbox.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.members_listbox.bind("<<ListboxSelect>>", self.on_member_selected)

        # Bills Listbox
        self.bills_label = tk.Label(root, text="Bills:")
        self.bills_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.bills_listbox = tk.Listbox(root, width=50, height=10)
        self.bills_listbox.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        self.bills_listbox.bind("<<ListboxSelect>>", self.on_bill_selected)

        # Bill Details Textbox
        self.bill_details_label = tk.Label(root, text="Bill Details:")
        self.bill_details_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.bill_details_text = tk.Text(root, width=50, height=10, wrap="word")
        self.bill_details_text.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Bind events
        self.members_listbox.bind("<<ListboxSelect>>", self.on_member_selected)
        self.bills_listbox.bind("<<ListboxSelect>>", self.on_bill_selected)

    def get_states(self):
        # List of state abbreviations
        return [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]

    def on_state_selected(self, event):
        self.members_listbox.delete(0, tk.END)
        self.bills_listbox.delete(0, tk.END)
        self.bill_details_text.delete(1.0, tk.END)
        state = self.state_combobox.get()
        current_only = self.current_members_var.get()
        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Congress.gov API key.")
            return
        if state:
            self.fetch_members(state, current_only, api_key)

    def fetch_members(self, state, current_only, api_key):
        url = f"https://api.congress.gov/v3/member/{state}?limit=250&api_key={api_key}"
        if current_only:
            url += "&current=true"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                members = data.get('members', [])
                self.members_listbox.delete(0, tk.END)  # Clear existing entries
                self.member_id_map.clear()  # Clear existing mappings
                for member in members:
                    name = member['name']
                    bioguide_id = member['bioguideId']
                    self.members_listbox.insert(tk.END, name)
                    self.member_id_map[name] = bioguide_id
            else:
                messagebox.showerror("Error", f"Failed to fetch members: {response.status_code}")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"An error occurred: {e}")


    def on_member_selected(self, event):
        selected_index = self.members_listbox.curselection()
        if not selected_index:
            return
        member_name = self.members_listbox.get(selected_index)
        bioguide_id = self.member_id_map.get(member_name)
        if bioguide_id:
            api_key = self.api_key_entry.get()
            if not api_key:
                messagebox.showerror("Error", "Please enter your Congress.gov API key.")
                return
            self.fetch_bills(bioguide_id, api_key)
        else:
            messagebox.showerror("Error", "Member ID not found.")


    def fetch_bills(self, bioguide_id, api_key):
        # Define the base URL for fetching legislation
        base_url = f"https://api.congress.gov/v3/member/{bioguide_id}/"
        endpoints = ['sponsored-legislation', 'cosponsored-legislation']
        
        # Clear existing entries in the listbox and the details map
        self.bills_listbox.delete(0, tk.END)
        self.bill_details_map = {}
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}?limit=250&api_key={api_key}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Determine the key based on the endpoint
                    bills_key = 'sponsoredLegislation' if 'sponsored' in endpoint else 'cosponsoredLegislation'
                    bills = data.get(bills_key, [])
                    for bill in bills:
                        # Extract bill details
                        bill_title = bill.get('title', 'No Title')
                        bill_congress = bill.get('congress')
                        bill_type = bill.get('type')
                        bill_number = bill.get('number')
                        
                        # Create a display title for the listbox
                        display_title = f"{bill_title} ({bill_type} {bill_number})"
                        
                        # Insert the bill title into the listbox
                        index = self.bills_listbox.size()
                        self.bills_listbox.insert(tk.END, display_title)
                        
                        # Map the listbox index to the bill details
                        self.bill_details_map[index] = {
                            'congress': bill_congress,
                            'type': bill_type,
                            'number': bill_number
                        }
                else:
                    messagebox.showerror("Error", f"Failed to fetch bills: {response.status_code}")
            except requests.RequestException as e:
                messagebox.showerror("Error", f"An error occurred: {e}")



    def on_bill_selected(self, event):
        # Clear previous bill details
        self.bill_details_text.delete(1.0, tk.END)
        
        # Get the selected bill's index
        selected_index = self.bills_listbox.curselection()
        if not selected_index:
            return
        
        # Retrieve the bill details using the selected index
        bill_details = self.bill_details_map.get(selected_index[0])
        if not bill_details:
            messagebox.showerror("Error", "Bill details not found.")
            return
        
        # Retrieve the API key
        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Congress.gov API key.")
            return
        
        # Fetch and display the bill details
        self.fetch_bill_details(bill_details, api_key)


    def fetch_bill_details(self, bill_details, api_key):
        # Construct the URL for fetching bill details
        congress = bill_details['congress']
        bill_type = bill_details['type']
        bill_number = bill_details['number']
        url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}?limit=250&api_key={api_key}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                bill_data = response.json()
                self.display_bill_details(bill_data)
            else:
                messagebox.showerror("Error", f"Failed to fetch bill details: {response.status_code}")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"An error occurred: {e}")


    def display_bill_details(self, bill_data):
        # Clear any existing content in the text widget
        self.bill_details_text.delete(1.0, tk.END)
        
        # Extract the bill's title
        title = bill_data.get('bill', {}).get('title', 'No title available')
        
        # Extract the latest action details
        latest_action = bill_data.get('bill', {}).get('latestAction', {})
        action_date = latest_action.get('actionDate', 'No action date available')
        action_text = latest_action.get('text', 'No action text available')
       
        # Format the details string
        details = f"Title: {title}\n\nLatest Action Date: {action_date}\nLatest Action: {action_text}"
        
        # Insert the details into the text widget
        self.bill_details_text.insert(tk.END, details)


if __name__ == "__main__":
    root = tk.Tk()
    app = CongressApp(root)
    root.mainloop()