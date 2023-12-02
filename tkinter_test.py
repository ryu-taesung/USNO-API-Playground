import tkinter as tk
from tkinter import scrolledtext
import urllib.request
import json

def fetch_data():
    url = entry_url.get()
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            json_data = json.loads(data)
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.END, json.dumps(json_data, indent=4))
    except Exception as e:
        text_area.delete('1.0', tk.END)
        text_area.insert(tk.END, str(e))

# Define colors for the night theme
bg_color = "#000000" #"#263D42"
text_color = "#CCCCCC" #"#FFFFFF"
button_color = "#06041b" #"#1E6262"

# Create the main window with the night theme
root = tk.Tk()
root.title("HTTP Requester")
root.configure(bg=bg_color)

# Create a frame to hold the Entry and Button widgets, apply the theme
frame = tk.Frame(root, bg=bg_color)
frame.pack(fill=tk.X)

# Create and pack widgets in the frame, apply the theme
entry_url = tk.Entry(frame, width=50, bg=text_color, fg=bg_color)
entry_url.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)

button_fetch = tk.Button(frame, text="Fetch Data", command=fetch_data, bg=button_color, fg=text_color)
button_fetch.pack(side=tk.RIGHT, pady=10)

# Create and pack the ScrolledText widget, apply the theme
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg=bg_color, fg=text_color)
text_area.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

# Start the GUI loop
root.mainloop()
