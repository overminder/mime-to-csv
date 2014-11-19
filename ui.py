# encoding: utf-8

import sys
import tkinter.filedialog
import tkinter.ttk
import tkinter as tk
from threading import Thread

from conv import run, ensure_dir

class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.master.title('MIME (*.eml) 格式批量转换器')
        self.create_widgets()

    def create_widgets(self):
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        input_frame = tk.Frame(self)
        output_frame = tk.Frame(self)

        self.choose_input_btn = tk.Button(
                input_frame, text='选择输入目录', command=self.choose_input)
        self.choose_input_btn.pack(side='left')

        self.input_dir_entry = tk.Entry(input_frame,
                textvariable=self.input_dir, width=100)
        self.input_dir_entry.pack(side='left')

        input_frame.pack()

        self.choose_output_btn = tk.Button(
                output_frame, text='选择导出目录', command=self.choose_output)
        self.choose_output_btn.pack(side='left')

        self.output_dir_entry = tk.Entry(output_frame,
                textvariable=self.output_dir, width=100)
        self.output_dir_entry.pack(side='left')

        output_frame.pack()

        convert_frame = tk.Frame(self)

        self.convert_btn = tk.Button(convert_frame,
                text='转换', command=self.convert)
        self.convert_btn.pack(side='left')

        self.progress_bar = tk.ttk.Progressbar(convert_frame)
        self.progress_bar.pack(side='left')

        self.old_progress = 0.0

        convert_frame.pack()

        self.progress_label = tk.Label(self, text='(转换进度)')
        self.progress_label.pack(side='bottom')

    def choose_input(self):
        self.input_dir.set(tk.filedialog.askdirectory())

    def choose_output(self):
        self.output_dir.set(tk.filedialog.askdirectory())

    def convert(self):
        csv_out_dir = self.output_dir.get() + '/'
        attach_out_dir = csv_out_dir + 'attachments/'
        ensure_dir(attach_out_dir)

        t = Thread(target=run, args=[self.input_dir.get() + '/',
                csv_out_dir, attach_out_dir, self.on_progress])
        t.start()
        # XXX: Disable buttons

    def on_progress(self, title, percent):
        if percent == 1:
            self.progress_label['text'] = '完成'
        else:
            self.progress_label['text'] = title

        if percent >= 1:
            prog = 0.999
        prog = (percent - self.old_progress) * 100
        self.progress_bar.step(prog)
        self.old_progress = percent

    @staticmethod
    def main():
        root = tk.Tk()
        app = App(master=root)

        prog_name, *args = sys.argv
        if args == ['--help']:
            print('Usage: %s <in-dir> <out-dir>' % prog_name)
            sys.exit(-1)

        if len(args) == 2:
            (in_dir, out_dir) = args
            app.input_dir.set(in_dir)
            app.output_dir.set(out_dir)
            app.convert()
        app.mainloop()

if __name__ == '__main__':
    App.main()

