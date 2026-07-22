import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from pixel_bot.core.executor import execute_action
from pixel_bot.core.planner import Plan, Planner
from pixel_bot.core.safety import Action
from pixel_bot.vision.screen_capture import capture_screen
from pixel_bot.update_readiness import format_summary, run_update_readiness_check


class ControlCenter(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Pixel Bot Control Center")
        self.geometry("900x700")
        self.minsize(760, 580)

        self.planner = Planner()
        self.current_plan: Plan | None = None

        self.stop_event = threading.Event()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        self.status_variable = tk.StringVar(value="Pronto")

        self._build_interface()
        self.after(100, self._process_events)

    def _build_interface(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x")

        title = ttk.Label(
            header,
            text="PIXEL BOT CONTROL CENTER",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(side="left")

        self.status_label = ttk.Label(
            header,
            textvariable=self.status_variable,
            font=("Segoe UI", 11, "bold"),
        )
        self.status_label.pack(side="right")

        ttk.Separator(root).pack(fill="x", pady=12)

        objective_frame = ttk.LabelFrame(
            root,
            text="Obiettivo",
            padding=12,
        )
        objective_frame.pack(fill="x")

        self.goal_entry = ttk.Entry(
            objective_frame,
            font=("Segoe UI", 11),
        )
        self.goal_entry.pack(fill="x")
        self.goal_entry.bind("<Return>", lambda event: self.analyze_goal())

        buttons = ttk.Frame(objective_frame)
        buttons.pack(fill="x", pady=(12, 0))

        self.analyze_button = ttk.Button(
            buttons,
            text="Analizza",
            command=self.analyze_goal,
        )
        self.analyze_button.pack(side="left", padx=(0, 8))

        self.execute_button = ttk.Button(
            buttons,
            text="Esegui",
            command=self.execute_plan,
            state="disabled",
        )
        self.execute_button.pack(side="left", padx=(0, 8))

        self.stop_button = ttk.Button(
            buttons,
            text="Stop",
            command=self.stop_execution,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(0, 8))

        self.screenshot_button = ttk.Button(
            buttons,
            text="Screenshot",
            command=self.take_screenshot,
        )
        self.screenshot_button.pack(side="left", padx=(0, 8))

        # PB-028 UPDATE READINESS
        self.readiness_button = ttk.Button(
            buttons,
            text="Verifica prontezza aggiornamento",
            command=self.check_update_readiness,
        )
        self.readiness_button.pack(side="left")

        plan_frame = ttk.LabelFrame(
            root,
            text="Piano",
            padding=12,
        )
        plan_frame.pack(fill="both", expand=True, pady=12)

        columns = ("id", "status", "action", "parameters")

        self.plan_tree = ttk.Treeview(
            plan_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        self.plan_tree.heading("id", text="#")
        self.plan_tree.heading("status", text="Stato")
        self.plan_tree.heading("action", text="Azione")
        self.plan_tree.heading("parameters", text="Parametri")

        self.plan_tree.column("id", width=45, anchor="center")
        self.plan_tree.column("status", width=100, anchor="center")
        self.plan_tree.column("action", width=150)
        self.plan_tree.column("parameters", width=500)

        scrollbar = ttk.Scrollbar(
            plan_frame,
            orient="vertical",
            command=self.plan_tree.yview,
        )
        self.plan_tree.configure(yscrollcommand=scrollbar.set)

        self.plan_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        log_frame = ttk.LabelFrame(
            root,
            text="Log",
            padding=12,
        )
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=10,
            state="disabled",
            wrap="word",
            font=("Consolas", 10),
        )
        self.log_text.pack(fill="both", expand=True)

        self._log("Control Center avviato.")

    def analyze_goal(self) -> None:
        goal = self.goal_entry.get().strip()

        if not goal:
            messagebox.showwarning(
                "Obiettivo mancante",
                "Scrivi un obiettivo da analizzare.",
            )
            return

        try:
            self.status_variable.set("Analisi in corso")
            self.current_plan = self.planner.create_plan(goal)
            self._render_plan()

            self.execute_button.configure(state="normal")
            self.status_variable.set("Piano pronto")

            self._log(
                f"Piano generato con "
                f"{len(self.current_plan.steps)} azioni."
            )

        except Exception as error:
            self.current_plan = None
            self.execute_button.configure(state="disabled")
            self.status_variable.set("Errore")
            self._log(f"Errore di analisi: {error}")

            messagebox.showerror(
                "Errore di analisi",
                str(error),
            )

    def _render_plan(self) -> None:
        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)

        if self.current_plan is None:
            return

        for step in self.current_plan.steps:
            self.plan_tree.insert(
                "",
                "end",
                iid=str(step.id),
                values=(
                    step.id,
                    step.status,
                    step.action,
                    str(step.parameters),
                ),
            )

    def execute_plan(self) -> None:
        if self.current_plan is None:
            messagebox.showwarning(
                "Piano mancante",
                "Analizza prima un obiettivo.",
            )
            return

        confirmed = messagebox.askyesno(
            "Conferma esecuzione",
            "Vuoi eseguire il piano visualizzato?",
        )

        if not confirmed:
            self._log("Esecuzione annullata dall'utente.")
            return

        self.stop_event.clear()
        self.current_plan.status = "running"

        self.analyze_button.configure(state="disabled")
        self.execute_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.screenshot_button.configure(state="disabled")

        self.status_variable.set("In esecuzione")
        self._log("Esecuzione del piano avviata.")

        worker = threading.Thread(
            target=self._execution_worker,
            daemon=True,
        )
        worker.start()

    def _execution_worker(self) -> None:
        if self.current_plan is None:
            return

        try:
            for step in self.current_plan.steps:
                if self.stop_event.is_set():
                    step.status = "stopped"

                    self.events.put(
                        ("step", (step.id, step.status))
                    )
                    self.events.put(("stopped", None))
                    return

                step.status = "running"
                self.events.put(
                    ("step", (step.id, step.status))
                )
                self.events.put(
                    (
                        "log",
                        f"Esecuzione: {step.action} "
                        f"{step.parameters}",
                    )
                )

                action = Action(
                    name=step.action,
                    parameters=step.parameters.copy(),
                )

                result = execute_action(action)

                step.status = "completed"
                self.events.put(
                    ("step", (step.id, step.status))
                )

                if result is not None:
                    self.events.put(
                        ("log", f"Risultato: {result}")
                    )

            self.current_plan.status = "completed"
            self.events.put(("completed", None))

        except Exception as error:
            self.current_plan.status = "failed"
            self.events.put(("error", str(error)))

    def stop_execution(self) -> None:
        self.stop_event.set()
        self.status_variable.set("Arresto richiesto")
        self._log(
            "Richiesto arresto: il bot si fermerà "
            "prima della prossima azione."
        )

    def take_screenshot(self) -> None:
        try:
            path = capture_screen()
            self._log(f"Screenshot salvato: {path}")

            messagebox.showinfo(
                "Screenshot completato",
                f"File salvato in:\n{path}",
            )

        except Exception as error:
            self._log(f"Errore screenshot: {error}")
            messagebox.showerror(
                "Errore screenshot",
                str(error),
            )

    def check_update_readiness(self) -> None:
        self.readiness_button.configure(state="disabled")
        self.status_variable.set("Controlli aggiornamento")
        self._log("Avvio verifica di prontezza aggiornamento.")

        worker = threading.Thread(
            target=self._readiness_worker,
            daemon=True,
        )
        worker.start()

    def _readiness_worker(self) -> None:
        try:
            report = run_update_readiness_check()
            self.events.put(("readiness", report))
        except Exception as error:
            self.events.put(("readiness_error", str(error)))

    def _process_events(self) -> None:
        while True:
            try:
                event_name, payload = self.events.get_nowait()
            except queue.Empty:
                break

            if event_name == "log":
                self._log(str(payload))

            elif event_name == "step":
                step_id, status = payload

                if self.plan_tree.exists(str(step_id)):
                    self.plan_tree.set(
                        str(step_id),
                        "status",
                        status,
                    )

            elif event_name == "completed":
                self.status_variable.set("Completato")
                self._log("Piano completato correttamente.")
                self._reset_buttons()

            elif event_name == "stopped":
                if self.current_plan is not None:
                    self.current_plan.status = "stopped"

                self.status_variable.set("Interrotto")
                self._log("Esecuzione interrotta.")
                self._reset_buttons()

            elif event_name == "readiness":
                report = payload
                labels = {
                    "green": "VERDE - pronto",
                    "orange": "ARANCIONE - intervento richiesto",
                    "red": "ROSSO - aggiornamento bloccato",
                }
                self.status_variable.set(labels[report.status])
                self._log(format_summary(report))
                self.readiness_button.configure(state="normal")

                title = "Prontezza aggiornamento"
                if report.status == "green":
                    messagebox.showinfo(title, "Pixel Bot e pronto per il prossimo aggiornamento.\n\n" + format_summary(report))
                elif report.status == "orange":
                    messagebox.showwarning(title, "Sono presenti elementi da sistemare o autorizzare.\n\n" + format_summary(report))
                else:
                    messagebox.showerror(title, "Aggiornamento bloccato da errori gravi.\n\n" + format_summary(report))

            elif event_name == "readiness_error":
                self.status_variable.set("Errore verifica")
                self._log(f"Errore verifica aggiornamento: {payload}")
                self.readiness_button.configure(state="normal")
                messagebox.showerror("Prontezza aggiornamento", str(payload))

            elif event_name == "error":
                self.status_variable.set("Errore")
                self._log(f"Errore durante l'esecuzione: {payload}")
                self._reset_buttons()

                messagebox.showerror(
                    "Errore di esecuzione",
                    str(payload),
                )

        self.after(100, self._process_events)

    def _reset_buttons(self) -> None:
        self.analyze_button.configure(state="normal")
        self.execute_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.screenshot_button.configure(state="normal")
        self.readiness_button.configure(state="normal")

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_text.configure(state="normal")
        self.log_text.insert(
            "end",
            f"{timestamp} | {message}\n",
        )
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def main() -> None:
    app = ControlCenter()
    app.mainloop()


if __name__ == "__main__":
    main()