import pandas as pd
import re
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import sys
from tkinter import scrolledtext


# کلاس اصلی برای تحلیل داده‌ها
class RestaurantAnalyzer:
    def __init__(self, df):
        self.df = df
        self.clean_data()
        self.analyze_data()

    def clean_data(self):
        """پاکسازی داده‌ها"""
        print("🔍 در حال پاکسازی داده‌ها...")

        # نمایش اطلاعات اولیه
        print(f"تعداد داده‌ها قبل از پاکسازی: {len(self.df)}")
        print(f"ستون‌های موجود: {list(self.df.columns)}")

        # بررسی ستون‌های ضروری
        required_columns = ['restaurant_name', 'comment_text', 'date', 'rating']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"ستون ضروری '{col}' در فایل وجود ندارد")

        # تبدیل امتیاز به عدد
        self.df['rating_clean'] = self.df['rating'].apply(self.safe_convert_to_numeric)

        # حذف ردیف‌های بدون کامنت
        self.df = self.df[self.df['comment_text'].notna() & (self.df['comment_text'] != '')]

        # پر کردن مقادیر خالی
        self.df['comment_text'] = self.df['comment_text'].fillna('')
        self.df['restaurant_name'] = self.df['restaurant_name'].fillna('نامشخص')

        print(f"✅ تعداد داده‌ها پس از پاکسازی: {len(self.df)}")
        print(f"✅ امتیازهای معتبر: {self.df['rating_clean'].notna().sum()}")

    def safe_convert_to_numeric(self, value):
        """تبدیل امن به عدد"""
        if pd.isna(value) or value == '' or value == ' ':
            return np.nan
        try:
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    def analyze_data(self):
        """انجام تمام تحلیل‌ها"""
        print("📊 در حال تحلیل داده‌ها...")
        self.basic_stats = self.get_basic_statistics()
        self.all_restaurants_analysis = self.analyze_all_restaurants()
        self.best_restaurant = self.find_best_restaurant()
        print("✅ تحلیل داده‌ها کامل شد")

    def get_basic_statistics(self):
        """آمار پایه"""
        stats = {}
        valid_ratings = self.df['rating_clean'].dropna()

        stats['total_comments'] = len(self.df)
        stats['valid_ratings'] = len(valid_ratings)
        stats['average_rating'] = valid_ratings.mean() if len(valid_ratings) > 0 else 0
        stats['rating_distribution'] = valid_ratings.value_counts().sort_index().to_dict()
        stats['restaurant_count'] = self.df['restaurant_name'].nunique()
        stats['restaurant_names'] = sorted(self.df['restaurant_name'].unique().tolist())

        return stats

    def analyze_all_restaurants(self):
        """تحلیل کامل همه رستوران‌ها"""
        restaurants_analysis = {}

        for restaurant in self.df['restaurant_name'].unique():
            restaurant_data = self.df[self.df['restaurant_name'] == restaurant]
            ratings = restaurant_data['rating_clean'].dropna()
            comments = restaurant_data['comment_text'].tolist()

            # تحلیل احساسات
            sentiment_analysis = self.persian_sentiment_analysis_for_restaurant(comments)
            emotion_dist = Counter([item['emotion'] for item in sentiment_analysis])

            # تحلیل مشکلات
            common_issues = self.analyze_common_issues_for_restaurant(comments)

            # کلمات کلیدی
            top_positive_words = self.extract_top_words(comments, 'positive')
            top_negative_words = self.extract_top_words(comments, 'negative')

            # محاسبه درصدهای احساسات
            total_sentiments = len(sentiment_analysis)
            positive_percentage = (emotion_dist['مثبت'] / total_sentiments) * 100 if total_sentiments > 0 else 0
            negative_percentage = (emotion_dist['منفی'] / total_sentiments) * 100 if total_sentiments > 0 else 0
            neutral_percentage = (emotion_dist['خنثی'] / total_sentiments) * 100 if total_sentiments > 0 else 0

            restaurants_analysis[restaurant] = {
                'total_comments': len(restaurant_data),
                'average_rating': ratings.mean() if len(ratings) > 0 else 0,
                'rating_distribution': ratings.value_counts().sort_index().to_dict(),
                'sentiment_distribution': dict(emotion_dist),
                'sentiment_percentages': {
                    'مثبت': positive_percentage,
                    'منفی': negative_percentage,
                    'خنثی': neutral_percentage
                },
                'common_issues': common_issues,
                'positive_percentage': positive_percentage,
                'top_positive_words': top_positive_words,
                'top_negative_words': top_negative_words,
                'comments_sample': comments[:5]
            }

        return restaurants_analysis

    def persian_sentiment_analysis_for_restaurant(self, comments):
        """تحلیل احساسات برای یک رستوران"""
        positive_words = {
            'عالی', 'خوب', 'عالیه', 'خوشمزه', 'ممتاز', 'بینظیر', 'دستمریزاد',
            'خوش طعم', 'گرم', 'تازه', 'داغ', 'سریع', 'کیفیت', 'محترم', 'مودب',
            'لذیذ', 'تمیز', 'بهداشتی', 'منظم', 'پرخونه', 'متراکم', 'ترد',
            'مثل همیشه', 'طعم خوب', 'خوبی داشت', 'عالی بود', 'پیشنهاد', 'عالی'
        }

        negative_words = {
            'بد', 'ضعیف', 'افتضاح', 'بی‌مزه', 'سرد', 'نامرغوب', 'بدتر',
            'خشک', 'شور', 'نپخته', 'دیر', 'تاخیر', 'بی‌کیفیت', 'شرم‌آور',
            'بدمزه', 'ترش', 'شور', 'بیات', 'کهنه', 'خراب', 'ضعیف', 'گران',
            'قیمت بیشتر', 'حجم کمتر', 'پر شده', 'بد بود', 'ضعیف بود'
        }

        sentiment_results = []

        for comment in comments:
            comment_str = str(comment)
            words = comment_str.split()

            found_positive = [word for word in words if word in positive_words]
            found_negative = [word for word in words if word in negative_words]

            # جستجوی عبارات چندکلمه‌ای
            for phrase in ['مثل همیشه', 'طعم خوب', 'خوبی داشت', 'قیمت بیشتر', 'حجم کمتر', 'پر شده']:
                if phrase in comment_str:
                    if phrase in positive_words:
                        found_positive.append(phrase)
                    else:
                        found_negative.append(phrase)

            positive_count = len(found_positive)
            negative_count = len(found_negative)

            if positive_count > negative_count:
                emotion = 'مثبت'
            elif negative_count > positive_count:
                emotion = 'منفی'
            else:
                emotion = 'خنثی'

            sentiment_results.append({
                'comment': comment_str,
                'emotion': emotion,
                'positive_words': found_positive,
                'negative_words': found_negative
            })

        return sentiment_results

    def extract_top_words(self, comments, word_type='positive'):
        """استخراج کلمات کلیدی پرتکرار"""
        positive_words = {'عالی', 'خوب', 'عالیه', 'خوشمزه', 'ممتاز', 'بینظیر'}
        negative_words = {'بد', 'ضعیف', 'افتضاح', 'بی‌مزه', 'سرد', 'گران'}

        all_words = []
        for comment in comments:
            words = str(comment).split()
            if word_type == 'positive':
                filtered_words = [word for word in words if word in positive_words]
            else:
                filtered_words = [word for word in words if word in negative_words]
            all_words.extend(filtered_words)

        word_counts = Counter(all_words)
        return dict(word_counts.most_common(5))

    def analyze_common_issues_for_restaurant(self, comments):
        """تحلیل مشکلات برای یک رستوران"""
        issues_keywords = {
            'گران بودن': ['قیمت بیشتر', 'گران', 'قیمت بالا'],
            'حجم کم غذا': ['حجم کمتر', 'کم حجم', 'حجم کم'],
            'کیفیت پایین': ['بی‌کیفیت', 'ضعیف', 'افتضاح', 'بد', 'خراب'],
            'طعم نامناسب': ['بی‌مزه', 'شور', 'ترش', 'بدمزه'],
            'ترکیب نامناسب': ['پر شده', 'سیب‌زمینی'],
            'سرد بودن غذا': ['سرد', 'سرد شده'],
            'تاخیر در ارسال': ['دیر', 'تاخیر', 'طولانی']
        }

        issues_count = {}
        for issue, keywords in issues_keywords.items():
            count = 0
            for comment in comments:
                comment_text = str(comment).lower()
                if any(keyword in comment_text for keyword in keywords):
                    count += 1
            issues_count[issue] = count

        return issues_count

    def find_best_restaurant(self):
        """پیدا کردن بهترین رستوران"""
        best_restaurant = None
        best_score = -1

        for restaurant, analysis in self.all_restaurants_analysis.items():
            if analysis['total_comments'] >= 1:  # حداقل یک نظر
                score = analysis['average_rating'] * analysis['positive_percentage'] / 100
                if score > best_score:
                    best_score = score
                    best_restaurant = restaurant

        return best_restaurant

    def get_restaurant_report(self, restaurant_name):
        """گزارش برای یک رستوران خاص"""
        if restaurant_name not in self.all_restaurants_analysis:
            return None

        analysis = self.all_restaurants_analysis[restaurant_name]

        report = {
            'name': restaurant_name,
            'total_comments': analysis['total_comments'],
            'average_rating': analysis['average_rating'],
            'positive_percentage': analysis['positive_percentage'],
            'sentiment_percentages': analysis['sentiment_percentages'],
            'rating_distribution': analysis['rating_distribution'],
            'sentiment_distribution': analysis['sentiment_distribution'],
            'common_issues': {k: v for k, v in analysis['common_issues'].items() if v > 0},
            'top_positive_words': analysis['top_positive_words'],
            'top_negative_words': analysis['top_negative_words'],
            'comments_sample': analysis['comments_sample']
        }

        return report


# رابط گرافیکی
class RestaurantAnalysisGUI:
    def __init__(self, root, analyzer, csv_file_path=None):
        self.root = root
        self.analyzer = analyzer
        self.csv_file_path = csv_file_path
        self.current_restaurant = None
        self.setup_gui()

    def setup_gui(self):
        """تنظیم رابط گرافیکی"""
        self.root.title("سیستم تحلیل رستوران‌ها")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f5f5f5')

        # ایجاد فریم اصلی
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # فریم سمت چپ برای لیست رستوران‌ها - اندازه بزرگتر
        left_frame = ttk.Frame(main_frame, width=500)
        left_frame.pack(side='left', fill='y', padx=(0, 15))
        left_frame.pack_propagate(False)

        # فریم سمت راست برای نمایش اطلاعات
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        # تنظیمات فریم سمت چپ
        self.setup_restaurant_list(left_frame)

        # تنظیمات فریم سمت راست
        self.setup_display_area(right_frame)

        # نمایش بهترین رستوران به طور پیش‌فرض
        self.show_best_restaurant()

        # نمایش نام فایل CSV در عنوان
        if self.csv_file_path:
            file_name = os.path.basename(self.csv_file_path)
            self.root.title(f"سیستم تحلیل رستوران‌ها - {file_name}")

    def setup_restaurant_list(self, parent):
        """تنظیم لیست رستوران‌ها"""
        # عنوان
        title_label = ttk.Label(parent, text="🍽️ لیست رستوران‌ها",
                                font=('Tahoma', 14, 'bold'))
        title_label.pack(pady=(0, 15))

        # جستجو
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill='x', pady=(0, 15))

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                 font=('Tahoma', 11))
        search_entry.pack(fill='x', ipady=5)
        search_entry.bind('<KeyRelease>', self.filter_restaurants)

        # لیست رستوران‌ها
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)

        # ایجاد Treeview برای نمایش رستوران‌ها
        columns = ('name', 'rating', 'comments')
        self.restaurant_tree = ttk.Treeview(list_frame, columns=columns,
                                            show='headings', height=25)

        # تعریف ستون‌ها با عرض بیشتر
        self.restaurant_tree.heading('name', text='نام رستوران')
        self.restaurant_tree.heading('rating', text='امتیاز')
        self.restaurant_tree.heading('comments', text='تعداد نظرات')

        self.restaurant_tree.column('name', width=350)
        self.restaurant_tree.column('rating', width=100)
        self.restaurant_tree.column('comments', width=100)

        # اسکرول بار
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical',
                                  command=self.restaurant_tree.yview)
        self.restaurant_tree.configure(yscrollcommand=scrollbar.set)

        self.restaurant_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # پر کردن لیست
        self.populate_restaurant_list()

        # 绑定事件
        self.restaurant_tree.bind('<<TreeviewSelect>>', self.on_restaurant_select)

    def setup_display_area(self, parent):
        """تنظیم منطقه نمایش اطلاعات"""
        # عنوان پویا
        self.restaurant_title = tk.StringVar()
        title_label = ttk.Label(parent, textvariable=self.restaurant_title,
                                font=('Tahoma', 16, 'bold'))
        title_label.pack(pady=(0, 15))

        # ایجاد تب‌ها
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)

        # تب خلاصه
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="📊 خلاصه عملکرد")

        # تب آمار
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📈 آمار دقیق")

        # تب اطلاعات فایل
        self.file_info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_info_frame, text="📁 اطلاعات فایل")
        self.setup_file_info_tab()

    def setup_file_info_tab(self):
        """تنظیم تب اطلاعات فایل"""
        if self.csv_file_path:
            file_name = os.path.basename(self.csv_file_path)
            file_size = os.path.getsize(self.csv_file_path) / 1024  # KB
            file_mtime = os.path.getmtime(self.csv_file_path)
            from datetime import datetime
            file_date = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')

            info_text = f"""
📊 اطلاعات فایل CSV:

• نام فایل: {file_name}
• مسیر فایل: {self.csv_file_path}
• حجم فایل: {file_size:.2f} KB
• تاریخ ایجاد: {file_date}
• تعداد کل نظرات: {len(self.analyzer.df)}
• تعداد رستوران‌ها: {self.analyzer.df['restaurant_name'].nunique()}
• میانگین امتیاز کلی: {self.analyzer.basic_stats['average_rating']:.2f}

📈 آمار کلی:
• نظرات با امتیاز معتبر: {self.analyzer.basic_stats['valid_ratings']}
• توزیع امتیازها: {self.analyzer.basic_stats['rating_distribution']}
"""

            text_widget = scrolledtext.ScrolledText(self.file_info_frame,
                                                    font=('Tahoma', 11),
                                                    wrap=tk.WORD)
            text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            text_widget.insert('1.0', info_text)
            text_widget.config(state='disabled')

    def populate_restaurant_list(self):
        """پر کردن لیست رستوران‌ها"""
        # پاک کردن موارد قبلی
        for item in self.restaurant_tree.get_children():
            self.restaurant_tree.delete(item)

        # مرتب‌سازی رستوران‌ها بر اساس امتیاز
        sorted_restaurants = sorted(
            self.analyzer.all_restaurants_analysis.items(),
            key=lambda x: x[1]['average_rating'],
            reverse=True
        )

        for restaurant, analysis in sorted_restaurants:
            rating = analysis['average_rating']
            comments_count = analysis['total_comments']

            self.restaurant_tree.insert('', 'end', values=(
                restaurant,
                f"{rating:.1f}" if not pd.isna(rating) else "ندارد",
                comments_count
            ))

    def filter_restaurants(self, event=None):
        """فیلتر کردن لیست رستوران‌ها"""
        search_term = self.search_var.get().lower()

        for item in self.restaurant_tree.get_children():
            values = self.restaurant_tree.item(item)['values']
            restaurant_name = values[0].lower()

            if search_term in restaurant_name:
                self.restaurant_tree.item(item, tags=('visible',))
            else:
                self.restaurant_tree.item(item, tags=('hidden',))

    def on_restaurant_select(self, event):
        """وقتی رستورانی انتخاب شود"""
        selection = self.restaurant_tree.selection()
        if selection:
            item = selection[0]
            restaurant_name = self.restaurant_tree.item(item)['values'][0]
            self.show_restaurant_details(restaurant_name)

    def show_best_restaurant(self):
        """نمایش بهترین رستوران"""
        if self.analyzer.best_restaurant:
            self.show_restaurant_details(self.analyzer.best_restaurant)
            # انتخاب در لیست
            for item in self.restaurant_tree.get_children():
                if self.restaurant_tree.item(item)['values'][0] == self.analyzer.best_restaurant:
                    self.restaurant_tree.selection_set(item)
                    self.restaurant_tree.focus(item)
                    break

    def show_restaurant_details(self, restaurant_name):
        """نمایش جزئیات رستوران"""
        self.current_restaurant = restaurant_name
        report = self.analyzer.get_restaurant_report(restaurant_name)

        if not report:
            return

        # به‌روزرسانی عنوان
        self.restaurant_title.set(f"📊 تحلیل عملکرد: {restaurant_name}")

        # به‌روزرسانی تب‌ها
        self.update_summary_tab(report)
        self.update_stats_tab(report)

    def update_summary_tab(self, report):
        """به‌روزرسانی تب خلاصه"""
        # پاک کردن محتوای قبلی
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # ایجاد متن خلاصه
        summary_text = self.generate_clean_summary(report)

        text_widget = scrolledtext.ScrolledText(self.summary_frame,
                                                font=('Tahoma', 12),
                                                wrap=tk.WORD)
        text_widget.pack(fill='both', expand=True, padx=15, pady=15)
        text_widget.insert('1.0', summary_text)
        text_widget.config(state='disabled')

    def update_stats_tab(self, report):
        """به‌روزرسانی تب آمار"""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        stats_text = f"""
📈 آمار دقیق رستوران:

• تعداد کل نظرات: {report['total_comments']}
• میانگین امتیاز: {report['average_rating']:.2f} از 5

😊 تحلیل احساسات:
• مثبت: {report['sentiment_percentages']['مثبت']:.1f}%
• منفی: {report['sentiment_percentages']['منفی']:.1f}%
• خنثی: {report['sentiment_percentages']['خنثی']:.1f}%

⭐ توزیع امتیازها:
"""
        for rating, count in sorted(report['rating_distribution'].items()):
            percentage = (count / report['total_comments']) * 100
            stars = '⭐' * int(rating)
            stats_text += f"  {stars} امتیاز {rating}: {count} نظر ({percentage:.1f}%)\n"

        # کلمات کلیدی مثبت
        if report['top_positive_words']:
            stats_text += f"\n✅ کلمات مثبت پرتکرار:\n"
            for word, count in report['top_positive_words'].items():
                stats_text += f"• '{word}': {count} بار\n"

        # کلمات کلیدی منفی
        if report['top_negative_words']:
            stats_text += f"\n❌ کلمات منفی پرتکرار:\n"
            for word, count in report['top_negative_words'].items():
                stats_text += f"• '{word}': {count} بار\n"

        if report['common_issues']:
            stats_text += f"\n⚠️ مشکلات گزارش شده:\n"
            for issue, count in report['common_issues'].items():
                percentage = (count / report['total_comments']) * 100
                stats_text += f"• {issue}: {count} بار ({percentage:.1f}%)\n"

        # نمونه‌ای از نظرات
        if report['comments_sample']:
            stats_text += f"\n💬 نمونه‌ای از نظرات:\n"
            for i, comment in enumerate(report['comments_sample'][:3], 1):
                stats_text += f"{i}. {comment}\n\n"

        text_widget = scrolledtext.ScrolledText(self.stats_frame,
                                                font=('Tahoma', 11),
                                                wrap=tk.WORD)
        text_widget.pack(fill='both', expand=True, padx=15, pady=15)
        text_widget.insert('1.0', stats_text)
        text_widget.config(state='disabled')

    def generate_clean_summary(self, report):
        """تولید خلاصه تمیز"""
        summary = []

        summary.append(f"🎯 خلاصه عملکرد {report['name']}")
        summary.append("=" * 50)

        # آمار کلیدی
        summary.append(f"\n📊 آمار کلیدی:")
        summary.append(f"• میانگین امتیاز: {report['average_rating']:.1f}/5")
        summary.append(f"• نظرات مثبت: {report['sentiment_percentages']['مثبت']:.1f}%")
        summary.append(f"• نظرات منفی: {report['sentiment_percentages']['منفی']:.1f}%")
        summary.append(f"• نظرات خنثی: {report['sentiment_percentages']['خنثی']:.1f}%")
        summary.append(f"• تعداد نظرات: {report['total_comments']}")

        # نقاط قوت
        if report['top_positive_words']:
            summary.append(f"\n✅ نقاط قوت:")
            top_positive = list(report['top_positive_words'].keys())[:3]
            for word in top_positive:
                summary.append(f"• {word}")

        # مشکلات اصلی
        if report['common_issues']:
            top_issue = max(report['common_issues'].items(), key=lambda x: x[1])
            summary.append(f"\n⚠️ اصلی‌ترین مشکل: {top_issue[0]}")

        # وضعیت کلی
        summary.append(f"\n📈 وضعیت کلی:")
        if report['average_rating'] >= 4.0 and report['sentiment_percentages']['مثبت'] >= 70:
            summary.append("✅ عملکرد عالی - حفظ کیفیت فعلی توصیه می‌شود")
        elif report['average_rating'] >= 3.0 and report['sentiment_percentages']['مثبت'] >= 50:
            summary.append("⚠️ عملکرد قابل قبول - نیاز به بهبود جزئی")
        elif report['sentiment_percentages']['منفی'] >= 40:
            summary.append("❌ نیاز به بازنگری اساسی در کیفیت خدمات")
        else:
            summary.append("📊 عملکرد متوسط - نیاز به توجه بیشتر به بازخوردها")

        return "\n".join(summary)


# تابع اصلی
def main(csv_file_path=None):
    try:
        if csv_file_path is None:
            # اگر فایل مستقیم داده نشد، از طریق رابط کاربری انتخاب شود
            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(
                title="لطفا فایل CSV را انتخاب کنید",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not file_path:
                print("❌ هیچ فایلی انتخاب نشد!")
                return
        else:
            file_path = csv_file_path

        # خواندن داده‌ها
        print("📁 در حال خواندن فایل CSV...")
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"✅ فایل با موفقیت خوانده شد. تعداد سطرها: {len(df)}")

        # ایجاد تحلیل‌گر
        analyzer = RestaurantAnalyzer(df)

        print(f"🏆 بهترین رستوران: {analyzer.best_restaurant}")
        print(f"📊 تعداد رستوران‌های تحلیل شده: {len(analyzer.all_restaurants_analysis)}")

        # ایجاد رابط گرافیکی
        print("🎨 در حال ایجاد رابط گرافیکی...")
        root = tk.Tk()
        app = RestaurantAnalysisGUI(root, analyzer, file_path)

        print("🚀 برنامه آماده اجراست!")
        root.mainloop()

    except Exception as e:
        messagebox.showerror("خطا", f"خطا در اجرای برنامه: {str(e)}")
        print(f"❌ خطا: {e}")


# تابع برای اجرای مستقیم از ماژول اول
def run_analysis_from_scraper(csv_file_path):
    """اجرای تحلیل مستقیماً از ماژول اسکرپر"""
    try:
        print(f"📁 در حال خواندن فایل CSV: {csv_file_path}")

        # بررسی وجود فایل
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"فایل {csv_file_path} یافت نشد")

        df = pd.read_csv(csv_file_path, encoding='utf-8')
        print(f"✅ فایل با موفقیت خوانده شد. تعداد سطرها: {len(df)}")

        # بررسی ساختار فایل
        required_columns = ['restaurant_name', 'comment_text', 'date', 'rating']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"ستون‌های ضروری وجود ندارند: {missing_columns}")

        # ایجاد تحلیل‌گر
        analyzer = RestaurantAnalyzer(df)

        print(f"🏆 بهترین رستوران: {analyzer.best_restaurant}")
        print(f"📊 تعداد رستوران‌های تحلیل شده: {len(analyzer.all_restaurants_analysis)}")

        # ایجاد رابط گرافیکی
        print("🎨 در حال ایجاد رابط گرافیکی...")
        root = tk.Tk()
        app = RestaurantAnalysisGUI(root, analyzer, csv_file_path)

        print("🚀 برنامه تحلیل داده‌ها آماده اجراست!")
        root.mainloop()

    except FileNotFoundError as e:
        print(f"❌ خطا: {e}")
        messagebox.showerror("خطا", f"فایل CSV یافت نشد: {e}")
    except pd.errors.EmptyDataError:
        print("❌ خطا: فایل CSV خالی است")
        messagebox.showerror("خطا", "فایل CSV خالی است")
    except Exception as e:
        print(f"❌ خطا در تحلیل داده‌ها: {e}")
        messagebox.showerror("خطا", f"خطا در تحلیل داده‌ها: {str(e)}")
        raise


if __name__ == "__main__":
    # اگر ماژول مستقیماً اجرا شود
    main()