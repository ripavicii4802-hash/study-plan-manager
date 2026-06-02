

"""
AI 기반 공부 계획 평가 시스템

프로그램 목적:
- 학생이 공부 계획을 입력하면 공부 시간, 우선순위, 마감일, 완료 여부를 관리할 수 있다.
- 입력된 공부 계획을 바탕으로 전체 공부 시간과 완료율을 분석한다.
- 과목별 공부 시간을 그래프로 보여준다.
- OpenAI API를 연결하여 AI가 공부 계획의 현실성, 우선순위, 마감 위험, 개선 방향을 직접 분석한다.
- 데이터를 study_data.json 파일에 저장하고 다시 불러올 수 있다.

사용 기술:
- Python
- Tkinter
- JSON
- Matplotlib
- OpenAI API
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

import json
import os
import sys
import threading
from datetime import datetime, date


def get_program_folder():
    """
    현재 프로그램이 실행되는 폴더 위치를 구하는 함수이다.
    일반 Python 실행과 exe 실행 상황을 모두 고려하였다.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


PROGRAM_FOLDER = get_program_folder()
DATA_FILE = os.path.join(PROGRAM_FOLDER, "study_data.json")


class StudyPlanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 기반 공부 계획 평가 시스템")
        self.root.geometry("1050x700")
        self.root.resizable(False, False)

        # 공부 계획들이 저장되는 리스트
        self.tasks = []

        # 화면 만들기
        self.create_widgets()

        # 저장된 데이터 불러오기
        self.load_data()

        # 기본 분석 결과 표시
        self.update_analysis()

    def create_widgets(self):
        """
        Tkinter를 이용하여 전체 GUI 화면을 구성하는 함수이다.
        """

        title_label = tk.Label(
            self.root,
            text="AI 기반 공부 계획 평가 시스템",
            font=("맑은 고딕", 20, "bold")
        )
        title_label.pack(pady=10)

        # 입력 영역
        input_frame = tk.LabelFrame(
            self.root,
            text="공부 계획 입력",
            font=("맑은 고딕", 11, "bold"),
            padx=10,
            pady=10
        )
        input_frame.pack(fill="x", padx=15, pady=5)

        # 할 일 입력
        tk.Label(input_frame, text="할 일", font=("맑은 고딕", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = tk.Entry(input_frame, width=25)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        # 과목 입력
        tk.Label(input_frame, text="과목", font=("맑은 고딕", 10)).grid(row=0, column=2, padx=5, pady=5)
        self.subject_entry = tk.Entry(input_frame, width=15)
        self.subject_entry.grid(row=0, column=3, padx=5, pady=5)

        # 공부 시간 입력
        tk.Label(input_frame, text="공부 시간", font=("맑은 고딕", 10)).grid(row=0, column=4, padx=5, pady=5)
        self.hours_entry = tk.Entry(input_frame, width=10)
        self.hours_entry.grid(row=0, column=5, padx=5, pady=5)

        # 우선순위 선택
        tk.Label(input_frame, text="우선순위", font=("맑은 고딕", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.priority_combo = ttk.Combobox(
            input_frame,
            values=["높음", "보통", "낮음"],
            width=22,
            state="readonly"
        )
        self.priority_combo.set("보통")
        self.priority_combo.grid(row=1, column=1, padx=5, pady=5)

        # 마감일 입력
        tk.Label(input_frame, text="마감일", font=("맑은 고딕", 10)).grid(row=1, column=2, padx=5, pady=5)
        self.deadline_entry = tk.Entry(input_frame, width=15)
        self.deadline_entry.insert(0, "2026-06-04")
        self.deadline_entry.grid(row=1, column=3, padx=5, pady=5)

        # 완료 여부 체크
        self.completed_var = tk.BooleanVar()
        self.completed_check = tk.Checkbutton(
            input_frame,
            text="완료",
            variable=self.completed_var,
            font=("맑은 고딕", 10)
        )
        self.completed_check.grid(row=1, column=4, padx=5, pady=5)

        # 추가 버튼
        add_button = tk.Button(
            input_frame,
            text="공부 계획 추가",
            width=15,
            command=self.add_task
        )
        add_button.grid(row=1, column=5, padx=5, pady=5)

        # 버튼 영역
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=15, pady=5)

        tk.Button(
            button_frame,
            text="완료/미완료 변경",
            width=18,
            command=self.toggle_complete
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="선택 항목 삭제",
            width=15,
            command=self.delete_task
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="전체 저장",
            width=12,
            command=self.save_data
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="기본 분석 보기",
            width=15,
            command=self.show_summary
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="그래프 보기",
            width=12,
            command=self.show_graph
        ).pack(side="left", padx=5)

        self.ai_button = tk.Button(
            button_frame,
            text="AI 분석 받기",
            width=15,
            command=self.start_ai_analysis
        )
        self.ai_button.pack(side="left", padx=5)

        # 목록 영역
        list_frame = tk.LabelFrame(
            self.root,
            text="공부 계획 목록",
            font=("맑은 고딕", 11, "bold"),
            padx=10,
            pady=10
        )
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("title", "subject", "hours", "priority", "deadline", "completed")

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=13
        )

        self.tree.heading("title", text="할 일")
        self.tree.heading("subject", text="과목")
        self.tree.heading("hours", text="공부 시간")
        self.tree.heading("priority", text="우선순위")
        self.tree.heading("deadline", text="마감일")
        self.tree.heading("completed", text="완료 여부")

        self.tree.column("title", width=300)
        self.tree.column("subject", width=120, anchor="center")
        self.tree.column("hours", width=90, anchor="center")
        self.tree.column("priority", width=90, anchor="center")
        self.tree.column("deadline", width=120, anchor="center")
        self.tree.column("completed", width=100, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 분석 결과 영역
        analysis_frame = tk.LabelFrame(
            self.root,
            text="자동 분석 결과",
            font=("맑은 고딕", 11, "bold"),
            padx=10,
            pady=10
        )
        analysis_frame.pack(fill="x", padx=15, pady=5)

        self.analysis_label = tk.Label(
            analysis_frame,
            text="분석 결과가 여기에 표시됩니다.",
            font=("맑은 고딕", 10),
            justify="left"
        )
        self.analysis_label.pack(anchor="w")

    def add_task(self):
        """
        사용자가 입력한 공부 계획을 리스트에 추가하는 함수이다.
        """

        title = self.title_entry.get().strip()
        subject = self.subject_entry.get().strip()
        hours_text = self.hours_entry.get().strip()
        priority = self.priority_combo.get()
        deadline = self.deadline_entry.get().strip()
        completed = self.completed_var.get()

        # 할 일 검사
        if title == "":
            messagebox.showwarning("입력 오류", "할 일을 입력하세요.")
            return

        # 과목 검사
        if subject == "":
            messagebox.showwarning("입력 오류", "과목을 입력하세요.")
            return

        # 공부 시간 검사
        try:
            hours = float(hours_text)
            if hours <= 0:
                messagebox.showwarning("입력 오류", "공부 시간은 0보다 커야 합니다.")
                return
        except ValueError:
            messagebox.showwarning("입력 오류", "공부 시간은 숫자로 입력하세요.")
            return

        # 마감일 형식 검사
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("입력 오류", "마감일은 YYYY-MM-DD 형식으로 입력하세요.")
            return

        task = {
            "title": title,
            "subject": subject,
            "hours": hours,
            "priority": priority,
            "deadline": deadline,
            "completed": completed
        }

        self.tasks.append(task)

        self.refresh_tree()
        self.save_data(show_message=False)
        self.update_analysis()
        self.clear_inputs()

    def clear_inputs(self):
        """
        입력창을 초기화하는 함수이다.
        """

        self.title_entry.delete(0, tk.END)
        self.subject_entry.delete(0, tk.END)
        self.hours_entry.delete(0, tk.END)
        self.priority_combo.set("보통")
        self.deadline_entry.delete(0, tk.END)
        self.deadline_entry.insert(0, "2026-06-04")
        self.completed_var.set(False)

    def refresh_tree(self):
        """
        Treeview에 표시된 공부 계획 목록을 새로고침하는 함수이다.
        """

        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, task in enumerate(self.tasks):
            completed_text = "완료" if task["completed"] else "미완료"

            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    task["title"],
                    task["subject"],
                    task["hours"],
                    task["priority"],
                    task["deadline"],
                    completed_text
                )
            )

    def delete_task(self):
        """
        선택한 공부 계획을 삭제하는 함수이다.
        """

        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("선택 오류", "삭제할 항목을 선택하세요.")
            return

        answer = messagebox.askyesno("삭제 확인", "선택한 항목을 삭제하시겠습니까?")

        if not answer:
            return

        selected_indexes = sorted([int(item) for item in selected_items], reverse=True)

        for index in selected_indexes:
            del self.tasks[index]

        self.refresh_tree()
        self.save_data(show_message=False)
        self.update_analysis()

    def toggle_complete(self):
        """
        선택한 항목의 완료 상태를 변경하는 함수이다.
        완료 → 미완료, 미완료 → 완료로 변경된다.
        """

        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("선택 오류", "상태를 바꿀 항목을 선택하세요.")
            return

        for item in selected_items:
            index = int(item)
            self.tasks[index]["completed"] = not self.tasks[index]["completed"]

        self.refresh_tree()
        self.save_data(show_message=False)
        self.update_analysis()

    def save_data(self, show_message=True):
        """
        공부 계획 데이터를 JSON 파일로 저장하는 함수이다.
        """

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=4)

            if show_message:
                messagebox.showinfo("저장 완료", "공부 계획이 저장되었습니다.")

        except Exception as error:
            messagebox.showerror("저장 오류", "데이터 저장 중 오류가 발생했습니다.\n" + str(error))

    def load_data(self):
        """
        저장된 JSON 파일을 불러오는 함수이다.
        """

        if not os.path.exists(DATA_FILE):
            self.tasks = []
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                self.tasks = json.load(file)

            self.refresh_tree()

        except Exception:
            self.tasks = []
            messagebox.showwarning(
                "불러오기 오류",
                "기존 데이터 파일을 불러오지 못했습니다. 새로 시작합니다."
            )

    def update_analysis(self):
        """
        조건문을 이용해 기본 분석 결과를 화면에 보여주는 함수이다.
        이 기능은 API 없이도 작동한다.
        """

        total_count = len(self.tasks)

        if total_count == 0:
            self.analysis_label.config(
                text="아직 입력된 공부 계획이 없습니다. 공부 계획을 추가해 주세요."
            )
            return

        total_hours = 0
        completed_count = 0
        high_priority_count = 0
        overdue_count = 0

        today = date.today()

        for task in self.tasks:
            total_hours += float(task["hours"])

            if task["completed"]:
                completed_count += 1

            if task["priority"] == "높음":
                high_priority_count += 1

            deadline_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()

            if not task["completed"] and deadline_date < today:
                overdue_count += 1

        progress = completed_count / total_count * 100

        feedback = self.make_basic_feedback(
            total_hours,
            progress,
            high_priority_count,
            overdue_count
        )

        result_text = (
            f"전체 공부 계획 수: {total_count}개\n"
            f"완료한 계획 수: {completed_count}개\n"
            f"전체 예상 공부 시간: {total_hours:.1f}시간\n"
            f"완료율: {progress:.1f}%\n"
            f"마감일이 지난 미완료 항목: {overdue_count}개\n"
            f"기본 피드백: {feedback}"
        )

        self.analysis_label.config(text=result_text)

    def make_basic_feedback(self, total_hours, progress, high_priority_count, overdue_count):
        """
        API 없이 조건문으로 간단한 피드백을 만드는 함수이다.
        AI API 연결이 안 되는 상황에서도 기본 분석은 가능하다.
        """

        if overdue_count > 0:
            return "마감일이 지난 항목이 있습니다. 급한 과제부터 먼저 처리하세요."

        if progress >= 80:
            return "공부 계획이 매우 잘 진행되고 있습니다."

        if progress >= 50:
            return "절반 이상 완료했습니다. 남은 항목의 우선순위를 확인하세요."

        if high_priority_count >= 3:
            return "우선순위가 높은 항목이 많습니다. 중요한 항목부터 나누어 공부하세요."

        if total_hours >= 10:
            return "공부 시간이 많은 편입니다. 쉬는 시간을 포함하는 것이 좋습니다."

        return "아직 완료율이 낮습니다. 작은 목표부터 하나씩 완료해 보세요."

    def show_summary(self):
        """
        과목별 공부 시간을 계산하여 보여주는 함수이다.
        """

        if len(self.tasks) == 0:
            messagebox.showinfo("분석 결과", "분석할 공부 계획이 없습니다.")
            return

        subject_hours = {}

        for task in self.tasks:
            subject = task["subject"]
            hours = float(task["hours"])

            if subject in subject_hours:
                subject_hours[subject] += hours
            else:
                subject_hours[subject] = hours

        most_subject = max(subject_hours, key=subject_hours.get)
        least_subject = min(subject_hours, key=subject_hours.get)

        summary = "과목별 공부 시간 분석\n\n"

        for subject, hours in subject_hours.items():
            summary += f"{subject}: {hours:.1f}시간\n"

        summary += "\n"
        summary += f"가장 많이 공부한 과목: {most_subject}\n"
        summary += f"가장 적게 공부한 과목: {least_subject}\n"

        messagebox.showinfo("기본 분석 결과", summary)

    def show_graph(self):
        """
        matplotlib을 사용하여 과목별 공부 시간을 막대그래프로 보여주는 함수이다.
        """

        if len(self.tasks) == 0:
            messagebox.showinfo("그래프", "그래프로 표시할 공부 계획이 없습니다.")
            return

        try:
            import matplotlib.pyplot as plt

            # Windows에서 한글 깨짐 방지
            plt.rcParams["font.family"] = "Malgun Gothic"
            plt.rcParams["axes.unicode_minus"] = False

            subject_hours = {}

            for task in self.tasks:
                subject = task["subject"]
                hours = float(task["hours"])

                if subject in subject_hours:
                    subject_hours[subject] += hours
                else:
                    subject_hours[subject] = hours

            subjects = list(subject_hours.keys())
            hours = list(subject_hours.values())

            plt.figure(figsize=(8, 5))
            plt.bar(subjects, hours)
            plt.title("과목별 공부 시간")
            plt.xlabel("과목")
            plt.ylabel("공부 시간")
            plt.tight_layout()
            plt.show()

        except ModuleNotFoundError:
            messagebox.showerror(
                "라이브러리 오류",
                "matplotlib 라이브러리가 설치되어 있지 않습니다.\n\n"
                "아래 명령어를 입력하세요.\n"
                "pip install matplotlib"
            )

        except Exception as error:
            messagebox.showerror("그래프 오류", "그래프 표시 중 오류가 발생했습니다.\n" + str(error))

    def start_ai_analysis(self):
        """
        AI 분석을 시작하는 함수이다.
        API 요청 중 GUI가 멈추지 않도록 별도 스레드에서 실행한다.
        """

        if len(self.tasks) == 0:
            messagebox.showinfo("AI 분석", "AI가 분석할 공부 계획이 없습니다.")
            return

        self.save_data(show_message=False)

        self.ai_button.config(state="disabled", text="AI 분석 중...")
        self.root.update_idletasks()

        thread = threading.Thread(target=self.run_ai_analysis)
        thread.daemon = True
        thread.start()

    def run_ai_analysis(self):
        """
        실제 OpenAI API 요청을 실행하는 함수이다.
        """

        try:
            result = self.get_ai_feedback()
        except Exception as error:
            result = (
                "AI 분석 중 오류가 발생했습니다.\n\n"
                f"오류 내용: {error}\n\n"
                "확인할 것:\n"
                "1. OPENAI_API_KEY가 설정되어 있는지 확인하세요.\n"
                "2. openai 라이브러리가 설치되어 있는지 확인하세요.\n"
                "3. 인터넷 연결을 확인하세요.\n"
                "4. API 키에 사용 가능한 결제 또는 크레딧이 있는지 확인하세요."
            )

        self.root.after(0, lambda: self.finish_ai_analysis(result))

    def finish_ai_analysis(self, result):
        """
        AI 분석이 끝난 후 버튼 상태를 복구하고 결과창을 띄우는 함수이다.
        """

        self.ai_button.config(state="normal", text="AI 분석 받기")
        self.show_ai_result_window(result)

    def get_ai_feedback(self):
        """
        현재 공부 계획 데이터를 OpenAI API에 보내고 AI 분석 결과를 받아오는 함수이다.
        """

        # .env 파일을 사용할 수 있도록 처리
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(PROGRAM_FOLDER, ".env")
            load_dotenv(env_path)
        except ModuleNotFoundError:
            # python-dotenv가 없어도 환경변수로 API 키가 있으면 작동 가능
            pass

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise Exception(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. "
                "src 폴더에 .env 파일을 만들고 OPENAI_API_KEY를 입력하세요."
            )

        try:
            from openai import OpenAI
        except ModuleNotFoundError:
            raise Exception(
                "openai 라이브러리가 설치되어 있지 않습니다. "
                "명령 프롬프트에서 pip install openai 를 실행하세요."
            )

        client = OpenAI(api_key=api_key)

        # 모델명은 .env에서 바꿀 수 있게 설정
        model_name = os.getenv("OPENAI_MODEL", "gpt-5.5")

        today_text = date.today().strftime("%Y-%m-%d")

        task_data = json.dumps(self.tasks, ensure_ascii=False, indent=2)

        prompt = f"""
너는 대학생을 도와주는 공부 계획 분석 AI 코치이다.

오늘 날짜:
{today_text}

아래는 사용자가 입력한 공부 계획 데이터이다.
각 항목에는 할 일, 과목, 공부 시간, 우선순위, 마감일, 완료 여부가 들어 있다.

공부 계획 데이터:
{task_data}

다음 기준으로 분석해라.

1. 전체 공부 계획이 현실적인지 평가
2. 공부 시간이 한 과목에 너무 치우쳤는지 평가
3. 우선순위가 높은 항목 중 먼저 해야 할 일 추천
4. 마감일이 가까운 항목 또는 위험한 항목 찾기
5. 완료율을 고려해서 현재 진행 상태 평가
6. 오늘부터 실천할 수 있는 공부 순서 추천
7. 너무 과한 계획이면 줄이는 방법 제안
8. 부족한 계획이면 보완할 방법 제안

답변 형식은 아래처럼 작성해라.

[AI 공부 계획 분석 결과]

1. 전체 평가
-

2. 우선적으로 해야 할 일
-

3. 마감일 위험 항목
-

4. 공부 시간 균형 분석
-

5. 오늘의 추천 공부 순서
1)
2)
3)

6. 개선 조언
-

7. 한 줄 요약
-
"""

        response = client.responses.create(
            model=model_name,
            input=[
                {
                    "role": "system",
                    "content": "너는 대학생의 공부 계획을 분석하고 현실적인 학습 조언을 해주는 AI 코치이다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.output_text

    def show_ai_result_window(self, result):
        """
        AI 분석 결과를 새 창으로 보여주는 함수이다.
        """

        result_window = tk.Toplevel(self.root)
        result_window.title("AI 분석 결과")
        result_window.geometry("750x600")

        title_label = tk.Label(
            result_window,
            text="AI 공부 계획 분석 결과",
            font=("맑은 고딕", 15, "bold")
        )
        title_label.pack(pady=10)

        text_area = ScrolledText(
            result_window,
            wrap=tk.WORD,
            font=("맑은 고딕", 10)
        )
        text_area.pack(fill="both", expand=True, padx=15, pady=10)

        text_area.insert(tk.END, result)
        text_area.config(state="disabled")

        close_button = tk.Button(
            result_window,
            text="닫기",
            width=12,
            command=result_window.destroy
        )
        close_button.pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = StudyPlanApp(root)
    root.mainloop()
