import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import tkinter.font as TkFont
import json
import urllib.request
import xml.etree.ElementTree as ET
import threading
import time
import datetime as dt


class LabelInput(tk.Frame):
    def __init__(self, parent, label, inp_cls, inp_args, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.label = tk.Label(self, text=label, anchor='w')
        self.input = inp_cls(self, **inp_args)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.label.grid(sticky=tk.E + tk.W)
        self.input.grid(row=0, column=1, sticky=tk.E + tk.W)


class ZipLabelInput(tk.Frame):
    def __init__(self, parent, label, inp_cls=tk.Entry, inp_args=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        if inp_args is None:
            inp_args = {}
        self.label = tk.Label(self, text=label, anchor='w')
        self.input = inp_cls(self, **inp_args)
        vcmd = (self.register(self.validate_entry), '%P')
        self.input.configure(validate="key", validatecommand=vcmd)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.label.grid(sticky=tk.E + tk.W)
        self.input.grid(row=0, column=1, sticky=tk.E + tk.W)

    def validate_entry(self, new_value):
        # Allow only up to 5 digits
        return new_value.isdigit() and len(new_value) <= 5 or new_value == ""


class Application(tk.Tk):
    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        # self.iconbitmap("test.ico")
        self._vars = {
            'zip_code': tk.StringVar(self),
            'lat_long': tk.StringVar(self),
            'progress': tk.IntVar(self),

        }
        self.zip_code = "00000"
        try:
            with open('latlong.txt', 'r') as file:
                json_file = file.read().strip()
                json_data = json.loads(json_file)
                self._vars['lat_long'].set(json_data['lat_long'])
                self._vars['zip_code'].set(json_data['zip_code'])
        except FileNotFoundError:
            pass  # File doesn't exist, proceed without loading
        self.create_widgets()

    def create_widgets(self):
        # self.zip_code = tk.Entry(self, textvariable=self._vars['zip_code'])
        self.input_zip_code = ZipLabelInput(self, 'Zip Code', tk.Entry, {
            'textvariable': self._vars['zip_code']})
        self.columnconfigure(0, weight=1)
        self.input_zip_code.grid(row=0, column=0, sticky="news")
        # tk.Canvas(self, width=10, height=1).grid(row=0,column=1)
        self.btn_get_lat_long = tk.Button(self, text="Get Lat/Long", command=self.get_lat_long_from_zip).grid(
            row=0, column=1, rowspan=2, padx=5, pady=5, sticky="ns")

        self.lat_long = LabelInput(
            self, "Lat/Long", tk.Entry, {'textvariable': self._vars['lat_long']})
        self.lat_long.grid(row=1, sticky="nesw")

        self.api_request_button = tk.Button(
            self, text="Request Data", command=self.get_json_data)
        self.api_request_button.grid(
            column=0, columnspan=2, pady=5, sticky="nsew")

        # ttk.Separator(self, orient=tk.HORIZONTAL).grid(
        #    columnspan=2, pady=5, sticky=tk.E+tk.W)

        self.result = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, bg="#000000", fg="#00ff00")
        # self.rowconfigure(4, weight=1)
        self.result.grid(columnspan=2, sticky="NESW")

        tv_cols = ("Sunrise", "Sunset", "Moon illum", "Moon Phase")
        tv_cols_widths = (300, 300, 300, 300)
        tv_cols_stretch = (False, False, False, False)
        self.style = ttk.Style()
        self.style.configure('mystyle.Treeview', background="#000",
                             foreground="#0f0", fieldbackground="#000")
        # derived from https://stackoverflow.com/q/63144552
        self.default_font = TkFont.nametofont('TkDefaultFont')
        self.default_font['size'] = self.default_font['size']+1
        self.bold_font = TkFont.nametofont('TkDefaultFont').copy()
        self.bold_font['weight'] = 'bold'
        self.style.configure("Treeview.Heading",
                             font=self.bold_font, foreground='#00f')
        self.tv = ttk.Treeview(
            self, style="mystyle.Treeview", columns=tv_cols, show="tree headings")
        self.tv.column("#0", width=0, stretch=False)
        for i, col in enumerate(tv_cols):
            self.tv.column(
                col, minwidth=tv_cols_widths[i], anchor='w', stretch=tv_cols_stretch[i])
            self.tv.heading(col, text=col, anchor='w')
        self.tv.grid(columnspan=2, sticky="NESW")

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            columnspan=2, sticky=tk.E+tk.W)
        self.quitButton = tk.Button(self, text="Quit", command=self.quit)
        self.quitButton.grid(columnspan=3)

        self.progress_bar = ttk.Progressbar(
            self, mode="indeterminate", maximum=10)
        self.rowconfigure(3, weight=1)
        self.progress_bar.grid(columnspan=3, sticky="nesw")

    def print_zip(self):
        print(self._vars['zip_code'].get())

    def get_lat_long_from_zip(self):
        self.thread_started = False

        def start_thread():
            if self.thread_started:
                return
            try:
                self.zip_code = self._vars['zip_code'].get()
                if not (len(self.zip_code) == 5 and self.zip_code.isdigit() and self.zip_code != '00000'):
                    self.result.delete('1.0', tk.END)
                    self.result.insert(
                        tk.END, f'Invalid ZIP code!\n')
                    return
                self.thread_started = True
                self.progress_bar.start(100)
                lat_long_lookup_url = f"https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList={self.zip_code}"
                zip_req = urllib.request.urlopen(lat_long_lookup_url)
                zip_data = zip_req.read()
                tree = ET.fromstring(zip_data)
                self.lat_long = tree.find('latLonList').text
                self._vars['lat_long'].set(self.lat_long)
                self.result.delete('1.0', tk.END)
                self.result.insert(
                    tk.END, f'Found {self.lat_long}\nPress <Request Data> to get astronomical information for this location.')
                with open('latlong.txt', 'w', encoding='utf-8') as f:
                    json_out = {'zip_code': self.zip_code,
                                'lat_long': self.lat_long}
                    f.write(json.dumps(json_out))
            except:
                self.result.insert(
                    tk.END, f'Error getting Lat/Long from ZIP code\n')
            self.thread_started = False
            self.progress_bar.stop()
        threading.Thread(target=start_thread).start()

    def get_json_data(self):
        self.thread_started = False

        def start_thread():
            if self.thread_started:
                return
            self.thread_started = True
            self.progress_bar.start(100)
            date = dt.datetime.today().strftime('%Y-%m-%d')
            api_url = f"https://aa.usno.navy.mil/api/rstt/oneday?date={date}&coords={self._vars['lat_long'].get()}&tz=-5&dst=true"
            req = urllib.request.urlopen(api_url)
            data = req.read()
            encoding = req.info().get_content_charset('utf-8')
            resp = json.loads(data.decode(encoding))
            self.result.delete('1.0', tk.END)
            self.result.insert(tk.END, json.dumps(resp, indent=2))
            self.tv.insert('', 'end', values=(
                resp['properties']['data']['sundata'][1]['time'].split(' ')[0], 
                resp['properties']['data']['sundata'][3]['time'].split(' ')[0], 
                resp['properties']['data']['fracillum'], resp['properties']['data']['curphase']))
            self.progress_bar.stop()
            self.thread_started = False
        threading.Thread(target=start_thread).start()


if __name__ == "__main__":
    app = Application("USNO API Client")
    app.mainloop()
