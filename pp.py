import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import csv
import threading
from concurrent.futures import ThreadPoolExecutor

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Malgun Gothic", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

scraping_thread = None

def scrape_page(i, target_user_id, gallery_id, base_url, base_article_url, headers):
    try:
        params = {'id': gallery_id, 'page': i}
        session = requests.Session()  # Use a session for faster repeated requests
        response = session.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        if soup.find('tbody') is None:
            return []

        article_list = soup.find('tbody').find_all('tr')
        results = []

        for tr_item in article_list:
            user_tag = tr_item.find('td', {'class': 'gall_writer'})
            if user_tag and user_tag.get('data-uid') == target_user_id:
                title_tag = tr_item.find('a', href=True)
                if title_tag:
                    title = title_tag.text.strip()
                    link = base_article_url + title_tag['href']
                    results.append([title, link])

        return results

    except Exception as e:
        print(f"Error on page {i}: {e}")
        return []

def start_scraping():
    try:
        target_user_id = user_id_entry.get()
        start_page = int(start_page_entry.get())
        end_page = int(end_page_entry.get())
        gallery_id = gallery_id_entry.get()

        base_url = "https://gall.dcinside.com/mgallery/board/lists"
        base_article_url = "https://gall.dcinside.com"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

        results = []
        num_workers = 10  # Number of threads (increase for faster results)
        log_text.insert(tk.END, f"{num_workers}개 쓰레드로 스크레이핑 중...\n")

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(scrape_page, i, target_user_id, gallery_id, base_url, base_article_url, headers)
                for i in range(start_page, end_page + 1)
            ]
            for future in futures:
                page_results = future.result()
                results.extend(page_results)
                log_text.insert(tk.END, f"{start_page + futures.index(future)} 페이지를 탐색했습니다.\n")
                log_text.see(tk.END)

        # Write to CSV after all pages are processed
        with open('search_result.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['제목', '주소'])
            writer.writerows(results)

        messagebox.showinfo(
            "완료", 
            "검색 결과를 search_result.csv 파일로 저장하였습니다. \n"
            "만약 인코딩 오류로 글자가 깨졌다면 메모장 프로그램으로 열어봐 주세요."
        )

    except Exception as e:
        messagebox.showerror("오류", str(e))
    finally:
        start_button.config(state=tk.NORMAL)

def start_scraping_thread():
    global scraping_thread
    start_button.config(state=tk.DISABLED)
    scraping_thread = threading.Thread(target=start_scraping)
    scraping_thread.start()

def on_closing():
    global scraping_thread
    if messagebox.askokcancel("종료", "정말 종료하시겠습니까?"):
        if scraping_thread and scraping_thread.is_alive():
            messagebox.showwarning("경고", 
                                   "스크래핑 작업이 진행 중입니다.\n"
                                   "작업이 완료될 때까지 기다려주세요.")
        else:
            root.destroy()

# GUI 설정
root = tk.Tk()
root.title("Ruby.")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

info_label = ttk.Label(frame, text="귀찮아서 마갤용만 만듦", anchor='center')
info_label.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=5)

gallery_id_label = ttk.Label(frame, text="갤러리 ID (?)")
gallery_id_label.grid(row=1, column=0, sticky=tk.W, pady=5)
gallery_id_entry = ttk.Entry(frame, width=20)
gallery_id_entry.grid(row=1, column=1, pady=5)
ToolTip(gallery_id_label, "ex: 티갤이면 tcggame")  # 갤러리 ID 라벨에 툴팁 추가

user_id_label = ttk.Label(frame, text="사용자 ID (?)")
user_id_label.grid(row=2, column=0, sticky=tk.W, pady=5)
user_id_entry = ttk.Entry(frame, width=20)
user_id_entry.grid(row=2, column=1, pady=5)
ToolTip(user_id_label, "ex: 식별 코드 id1234")  # 사용자 ID 라벨에 툴팁 추가

start_page_label = ttk.Label(frame, text="시작 페이지 (?)")
start_page_label.grid(row=3, column=0, sticky=tk.W, pady=5)
start_page_entry = ttk.Entry(frame, width=20)
start_page_entry.grid(row=3, column=1, pady=5)
ToolTip(start_page_label, "해당 갤러리 여기 페이지부터 시작해서") 

end_page_label = ttk.Label(frame, text="끝 페이지 (?)")
end_page_label.grid(row=4, column=0, sticky=tk.W, pady=5)
end_page_entry = ttk.Entry(frame, width=20)
end_page_entry.grid(row=4, column=1, pady=5)
ToolTip(end_page_label, "여기 페이지까지 탐색함") 

start_button = ttk.Button(frame, text="시작", command=start_scraping_thread)
start_button.grid(row=5, column=0, columnspan=2, pady=10)

log_text = tk.Text(frame, width=50, height=10)
log_text.grid(row=6, column=0, columnspan=2, pady=5)

# 창 닫기 이벤트 바인딩
root.protocol("WM_DELETE_WINDOW", on_closing)

# main loop
root.mainloop()