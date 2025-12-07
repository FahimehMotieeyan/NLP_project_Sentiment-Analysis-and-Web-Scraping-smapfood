import time
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import pandas as pd
import csv
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("سیستم جمع‌آوری داده‌های رستوران")
        self.root.geometry("500x400")
        self.root.configure(bg='#f5f5f5')

        self.setup_gui()
        self.driver = None
        self.current_csv_file = None
        self.current_dataframe = None

    def setup_gui(self):
        """تنظیم رابط گرافیکی"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)

        # عنوان
        title_label = ttk.Label(main_frame, text="🍽️ جمع‌آوری داده‌های رستوران",
                                font=('Tahoma', 16, 'bold'))
        title_label.pack(pady=(0, 30))

        # فیلد محله
        neighborhood_frame = ttk.Frame(main_frame)
        neighborhood_frame.pack(fill='x', pady=10)

        ttk.Label(neighborhood_frame, text="نام محله:", font=('Tahoma', 12)).pack(side='left')
        self.neighborhood_var = tk.StringVar()
        neighborhood_entry = ttk.Entry(neighborhood_frame, textvariable=self.neighborhood_var,
                                       font=('Tahoma', 12), width=30)
        neighborhood_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)

        # فیلد نوع غذا
        food_frame = ttk.Frame(main_frame)
        food_frame.pack(fill='x', pady=10)

        ttk.Label(food_frame, text="نوع غذا:", font=('Tahoma', 12)).pack(side='left')
        self.food_var = tk.StringVar()
        food_entry = ttk.Entry(food_frame, textvariable=self.food_var,
                               font=('Tahoma', 12), width=30)
        food_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)

        # دکمه شروع
        self.start_button = ttk.Button(main_frame, text="شروع جمع‌آوری داده‌ها",
                                       command=self.start_scraping)
        self.start_button.pack(pady=20)

        # نوار پیشرفت
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')

        # وضعیت
        self.status_var = tk.StringVar(value="آماده برای شروع...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                 font=('Tahoma', 10))
        status_label.pack(pady=10)

    def start_scraping(self):
        """شروع فرآیند اسکرپینگ در یک thread جداگانه"""
        neighborhood = self.neighborhood_var.get().strip()
        food = self.food_var.get().strip()

        if not neighborhood or not food:
            messagebox.showerror("خطا", "لطفاً نام محله و نوع غذا را وارد کنید")
            return

        # غیرفعال کردن دکمه و نمایش پیشرفت
        self.start_button.config(state='disabled')
        self.progress.pack(pady=10)
        self.progress.start()
        self.status_var.set("در حال راه‌اندازی مرورگر...")

        # اجرای اسکرپینگ در thread جداگانه
        thread = threading.Thread(target=self.run_scraping, args=(neighborhood, food))
        thread.daemon = True
        thread.start()

    def run_scraping(self, neighborhood, food):
        """اجرای فرآیند اسکرپینگ"""
        try:
            self.status_var.set("در حال راه‌اندازی مرورگر...")
            driver = setup_driver(neighborhood_name=neighborhood, food_name=food)

            if driver:
                self.status_var.set("در حال جمع‌آوری داده‌ها...")
                scraped_data = scraper(driver)

                if scraped_data:
                    self.status_var.set("در حال ذخیره داده‌ها...")
                    # پاکسازی داده‌ها
                    cleaned_data = clean_and_validate_data(scraped_data)

                    # ایجاد DataFrame
                    df = pd.DataFrame(cleaned_data)
                    self.current_dataframe = df  # ذخیره dataframe برای استفاده بعدی

                    # ذخیره فایل CSV
                    filename = f"{neighborhood}_{food}_structured.csv"
                    df.to_csv(filename, index=False, encoding='utf-8-sig')

                    # ذخیره نام فایل برای استفاده در تحلیل
                    self.current_csv_file = filename

                    self.status_var.set(f"داده‌ها با موفقیت ذخیره شد: {filename}")

                    # نمایش خلاصه داده‌ها
                    self.show_summary_page(df)

                else:
                    self.status_var.set("هیچ داده‌ای جمع‌آوری نشد")
                    messagebox.showinfo("اطلاع", "هیچ داده‌ای از رستوران‌ها جمع‌آوری نشد.")

            else:
                self.status_var.set("خطا در راه‌اندازی مرورگر")
                messagebox.showerror("خطا", "خطا در راه‌اندازی مرورگر")

        except Exception as e:
            self.status_var.set(f"خطا: {str(e)}")
            messagebox.showerror("خطا", f"خطا در جمع‌آوری داده‌ها: {str(e)}")
        finally:
            # بازگرداندن وضعیت به حالت عادی
            self.progress.stop()
            self.progress.pack_forget()
            self.start_button.config(state='normal')

    def show_summary_page(self, df):
        """نمایش صفحه خلاصه داده‌ها"""
        try:
            summary_window = tk.Toplevel(self.root)
            summary_window.title("خلاصه داده‌های جمع‌آوری شده")
            summary_window.geometry("600x500")
            summary_window.configure(bg='#f5f5f5')
            summary_window.transient(self.root)
            summary_window.grab_set()

            # عنوان
            title_label = ttk.Label(summary_window, text="📊 خلاصه داده‌های جمع‌آوری شده",
                                    font=('Tahoma', 16, 'bold'))
            title_label.pack(pady=20)

            # اطلاعات کلی در یک فریم
            info_frame = ttk.Frame(summary_window)
            info_frame.pack(fill='both', expand=True, padx=20, pady=10)

            # محاسبات آماری
            total_comments = len(df)
            total_restaurants = df['restaurant_name'].nunique()
            comments_with_rating = df[df['rating'] != ''].shape[0]

            # محاسبه میانگین امتیازها
            rating_data = df[df['rating'] != '']['rating']
            if not rating_data.empty:
                try:
                    # تبدیل به عدد
                    numeric_ratings = pd.to_numeric(rating_data, errors='coerce')
                    avg_rating = numeric_ratings.mean()
                except:
                    avg_rating = 0
            else:
                avg_rating = 0

            # ایجاد متن خلاصه
            summary_text = f"""
📈 اطلاعات کلی داده‌ها:

• 🏢 تعداد رستوران‌ها: {total_restaurants} 
• 💬 تعداد کل نظرات: {total_comments}
• ⭐ نظرات دارای امتیاز: {comments_with_rating}
• 📊 میانگین امتیازها: {avg_rating:.2f}
• 💾 فایل ذخیره شده: {self.current_csv_file}

📋 لیست رستوران‌ها:
"""

            # اضافه کردن نام رستوران‌ها
            restaurants = df['restaurant_name'].unique()
            for i, restaurant in enumerate(restaurants[:10], 1):  # فقط 10 رستوران اول
                restaurant_comments = df[df['restaurant_name'] == restaurant].shape[0]
                summary_text += f"  {i}. {restaurant} ({restaurant_comments} نظر)\n"

            if len(restaurants) > 10:
                summary_text += f"  ... و {len(restaurants) - 10} رستوران دیگر"

            # نمایش متن خلاصه
            text_widget = scrolledtext.ScrolledText(info_frame,
                                                    font=('Tahoma', 11),
                                                    wrap=tk.WORD,
                                                    height=15)
            text_widget.pack(fill='both', expand=True)
            text_widget.insert('1.0', summary_text)
            text_widget.config(state='disabled')

            # فریم برای دکمه‌ها
            button_frame = ttk.Frame(summary_window)
            button_frame.pack(pady=20)

            # دکمه تحلیل دقیق‌تر
            analyze_button = ttk.Button(button_frame,
                                        text="تحلیل دقیق‌تر داده‌ها",
                                        command=lambda: self.open_detailed_analysis(summary_window),
                                        style='Accent.TButton')
            analyze_button.pack(side='left', padx=10)

            # دکمه بستن
            close_button = ttk.Button(button_frame,
                                      text="بستن",
                                      command=summary_window.destroy)
            close_button.pack(side='left', padx=10)

            # استایل برای دکمه اصلی
            style = ttk.Style()
            style.configure('Accent.TButton', font=('Tahoma', 11, 'bold'))

        except Exception as e:
            print(f"خطا در نمایش صفحه خلاصه: {e}")

    def open_detailed_analysis(self, summary_window):
        """باز کردن تحلیل دقیق‌تر"""
        if not self.current_csv_file:
            messagebox.showerror("خطا", "هیچ فایل داده‌ای برای تحلیل وجود ندارد")
            return

        try:
            # بستن پنجره خلاصه
            summary_window.destroy()

            self.status_var.set("در حال اجرای تحلیل دقیق‌تر...")

            # اضافه کردن مسیر ماژول دوم به sys.path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)

            # ایمپورت و اجرای ماژول تحلیل
            from nlp2 import run_analysis_from_scraper

            # ایجاد یک thread جدید برای اجرای تحلیل
            analysis_thread = threading.Thread(target=self.execute_analysis, args=(self.current_csv_file,))
            analysis_thread.daemon = True
            analysis_thread.start()

        except ImportError as e:
            self.status_var.set(f"خطا در ایمپورت ماژول تحلیل: {str(e)}")
            messagebox.showerror("خطا", f"ماژول تحلیل داده‌ها یافت نشد: {str(e)}")
        except Exception as e:
            self.status_var.set(f"خطا در اجرای تحلیل: {str(e)}")
            messagebox.showerror("خطا", f"خطا در اجرای تحلیل داده‌ها: {str(e)}")

    def execute_analysis(self, csv_file):
        """اجرای تحلیل داده‌ها"""
        try:
            from nlp2 import run_analysis_from_scraper
            # اجرای مستقیم تحلیل بدون نیاز به انتخاب فایل
            run_analysis_from_scraper(csv_file)

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"خطا در تحلیل: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("خطا", f"خطا در تحلیل داده‌ها: {str(e)}"))


# region Driver Setup
def setup_driver(neighborhood_name, food_name):
    url = "https://www.snappfood.ir/"
    driver = webdriver.Edge()
    driver.get(url)
    driver.maximize_window()
    time.sleep(5)

    try:
        neighborhood_search_box_xpath = '''//*[@id="__next"]/div/div/main/div[1]/div[2]/div[2]/div[3]/div/p'''
        neighborhood_search_box = driver.find_element(By.XPATH, neighborhood_search_box_xpath)
        neighborhood_search_box.click()
        time.sleep(10)

        neighborhood_finder_xpath = '''//*[@id="modal-backdrop"]/div/section/div/section/form/div[2]/div/input'''
        neighborhood_finder = driver.find_element(By.XPATH, neighborhood_finder_xpath)
        neighborhood_finder.click()
        neighborhood_finder.clear()
        neighborhood_finder.send_keys(neighborhood_name + ' ')
        time.sleep(10)

        neighborhood_search_result_xpath = '''//*[@id="modal-backdrop"]/div/section/div/section/div/button[1]/p[2]'''
        neighborhood_search_result = driver.find_element(By.XPATH, neighborhood_search_result_xpath)
        neighborhood_search_result.click()
        time.sleep(5)
        # دکمه تایید ادرس
        neighborhood_confirmation_button_xpath = '''//*[@id="modal-backdrop"]/div/form/div/button'''
        neighborhood_confirmation_button = driver.find_element(By.XPATH, neighborhood_confirmation_button_xpath)
        neighborhood_confirmation_button.click()
        time.sleep(10)

        food_search_box_xpath = '''//*[@id="__next"]/div/div/div[1]/header/div[1]/div[2]/p'''
        food_search_box = driver.find_element(By.XPATH, food_search_box_xpath)
        food_search_box.click()
        time.sleep(2)
        # قسمت سرچ
        food_input_xpath = '''//*[@id="modal-backdrop"]/div/div/div[1]/input'''
        food_input = driver.find_element(By.XPATH, food_input_xpath)
        food_input.click()
        food_input.send_keys(food_name + ' ')
        time.sleep(5)

        view_all_xpath = '''//*[@id="modal-backdrop"]/div/div/div[2]/div[2]/div/a/div/span'''
        view_all = driver.find_element(By.XPATH, view_all_xpath)
        view_all.click()
        time.sleep(10)

        return driver

    except NoSuchElementException:
        print("The page requested is not found.")
        return None


# endregion Driver Setup

def extract_comments_grouped(comments_elements):
    """
    استخراج نظرات به صورت گروه‌بندی شده (هر نظر در 3 خط)
    """
    grouped_comments = []

    for i in range(0, len(comments_elements), 3):
        if i + 2 < len(comments_elements):
            # سه خط مربوط به یک نظر
            date_line = comments_elements[i].text.strip()
            rating_line = comments_elements[i + 1].text.strip()
            comment_line = comments_elements[i + 2].text.strip()

            # استخراج ریتینگ از خط دوم
            rating = None
            if rating_line.isdigit() and 1 <= int(rating_line) <= 5:
                rating = int(rating_line)
            elif 'ستاره' in rating_line or 'از' in rating_line:
                # استخراج ریتینگ از متن
                numbers = re.findall(r'\d+', rating_line)
                if numbers and 1 <= int(numbers[0]) <= 5:
                    rating = int(numbers[0])

            grouped_comments.append({
                'date': date_line,
                'rating': rating,
                'comment': comment_line
            })

    return grouped_comments


# region Scraper Function
def scraper(driver):
    # --- Your scrolling logic ---
    last_height = driver.execute_script('return document.body.scrollHeight')
    while True:
        driver.execute_script('window.scrollBy(0,800)')
        time.sleep(2)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == last_height:
            print("Reached bottom of page.")
            break
        last_height = new_height

    # --- Setup for the loop ---
    div_container_xpath = '''//*[@id="__next"]/div/main/div[1]'''
    item_css_selector = ".sc-citwmv.jOCtGV"  # Corrected: space replaced with dot
    wait = WebDriverWait(driver, 10)

    wait.until(ec.visibility_of_element_located((By.XPATH, div_container_xpath)))
    num_items = len(driver.find_elements(By.CSS_SELECTOR, item_css_selector))

    if num_items == 0:
        print("No items found.")
        return []  # Return an empty list

    print(f"Found {num_items} items. Starting loop...")

    all_comments_data = []
    original_window = driver.current_window_handle

    # --- Use the "Index Loop" ---
    for i in range(num_items):
        print(f"--- Processing item {i + 1} of {num_items} ---")
        try:
            all_items = driver.find_elements(By.CSS_SELECTOR, item_css_selector)

            if i >= len(all_items):
                print("   > Item list changed. Stopping.")
                break
            item_to_click = all_items[i]

            print("   > Opening in new tab...")
            ActionChains(driver) \
                .key_down(Keys.CONTROL) \
                .click(item_to_click) \
                .key_up(Keys.CONTROL) \
                .perform()

            wait.until(ec.number_of_windows_to_be(2))
            new_tab = [window for window in driver.window_handles if window != original_window][0]
            driver.switch_to.window(new_tab)

            print(f"   > Switched to new tab: {driver.title}")

            try:
                ITEM_NAME_SELECTOR = (By.TAG_NAME, "h1")
                comment_container_xpath = '''//*[@id="modal-backdrop"]/div/div[2]/div[3]'''
                comment_selector_css = ".sc-hKgILt.hmsjTi"

                item_name_element = wait.until(ec.visibility_of_element_located(ITEM_NAME_SELECTOR))
                item_name = item_name_element.text

                comment_container = wait.until(ec.visibility_of_element_located((By.XPATH, comment_container_xpath)))

                comment_elements = comment_container.find_elements(By.CSS_SELECTOR, comment_selector_css)
                print(f"   > Found {len(comment_elements)} comment lines for '{item_name}'.")

                # استخراج نظرات به صورت گروه‌بندی شده
                grouped_comments = extract_comments_grouped(comment_elements)
                print(f"   > Extracted {len(grouped_comments)} complete comments.")

                for comment_data in grouped_comments:
                    all_comments_data.append({
                        "restaurant_name": item_name,
                        "comment_text": comment_data['comment'],
                        "date": comment_data['date'],
                        "rating": comment_data['rating'] if comment_data['rating'] else ""
                    })

            except Exception as e:
                print(f"   > Error scraping details from new tab: {e}")

            driver.close()
            driver.switch_to.window(original_window)
            print("   > Closed tab and returned to main page.")
        except Exception as e:
            print(f"   > Error on item {i + 1}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(original_window)
        time.sleep(1)
    print("Loop finished.")
    return all_comments_data


# endregion Scraper Function

def clean_and_validate_data(data):
    """
    پاکسازی و اعتبارسنجی داده‌ها
    """
    cleaned_data = []

    for item in data:
        # فقط مواردی که حداقل نام رستوران و متن نظر را دارند نگه می‌داریم
        if item.get('restaurant_name') and item.get('comment_text'):
            cleaned_data.append({
                "restaurant_name": item["restaurant_name"].strip(),
                "comment_text": item["comment_text"].strip(),
                "date": item.get("date", "").strip(),
                "rating": item.get("rating", "")
            })

    return cleaned_data


def main():
    """تابع اصلی برای اجرای رابط گرافیکی"""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()