"""Local Windows helper for safe Android diagnostics over authorized ADB."""

from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.]+$")
PERMISSION_MARKERS = (
    ("Sobreposição de tela", re.compile(r"SYSTEM_ALERT_WINDOW:\s*granted=true", re.I)),
    ("Solicita instalação de APK", re.compile(r"REQUEST_INSTALL_PACKAGES:\s*granted=true", re.I)),
    ("Acesso a SMS", re.compile(r"(?:READ_SMS|RECEIVE_SMS):\s*granted=true", re.I)),
    ("Serviço de acessibilidade declarado", re.compile(r"BIND_ACCESSIBILITY_SERVICE", re.I)),
    ("Administrador do dispositivo declarado", re.compile(r"BIND_DEVICE_ADMIN|DEVICE_ADMIN_ENABLED", re.I)),
)


def find_adb() -> str | None:
    """Find an existing ADB install without downloading or executing anything else."""
    candidates: list[Path] = [
        APP_DIR / "platform-tools" / "adb.exe",
        APP_DIR.parent / "platform-tools" / "adb.exe",
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe")
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which("adb")


def run_adb(adb_path: str, args: list[str], serial: str | None = None, timeout: int = 20) -> str:
    command = [adb_path]
    if serial:
        command.extend(["-s", serial])
    command.extend(args)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output = completed.stdout.strip()
    if completed.returncode and not output:
        raise RuntimeError(completed.stderr.strip() or f"ADB terminou com código {completed.returncode}.")
    return output


def parse_devices(output: str) -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        columns = line.split()
        if len(columns) >= 2:
            devices.append({"serial": columns[0], "state": columns[1], "details": " ".join(columns[2:])})
    return devices


def parse_user_packages(output: str) -> list[dict[str, str | None]]:
    packages: list[dict[str, str | None]] = []
    for line in output.splitlines():
        match = re.search(r"(?:^|\s)package:([A-Za-z0-9_.]+)(?:\s+installer=(\S+))?", line.strip())
        if match:
            installer = match.group(2)
            if installer in (None, "null", "unknown"):
                installer = None
            packages.append({"package": match.group(1), "installer": installer})
    return packages


def package_blocks(dump: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^\s*Package\s+\[([^\]]+)\]\s+\([^\n]*", dump))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(dump)
        blocks[match.group(1)] = dump[match.start():end]
    return blocks


def analyze_device(adb_path: str, serial: str) -> dict[str, object]:
    device: dict[str, str] = {}
    for key, prop in (
        ("fabricante", "ro.product.manufacturer"),
        ("modelo", "ro.product.model"),
        ("android", "ro.build.version.release"),
    ):
        device[key] = run_adb(adb_path, ["shell", "getprop", prop], serial, timeout=10).strip()

    battery = run_adb(adb_path, ["shell", "dumpsys", "battery"], serial, timeout=15)
    battery_match = re.search(r"(?m)^\s*level:\s*(\d+)", battery)
    device["bateria"] = f"{battery_match.group(1)}%" if battery_match else "não informada"

    package_output = run_adb(adb_path, ["shell", "pm", "list", "packages", "-3", "-i"], serial, timeout=30)
    packages = parse_user_packages(package_output)
    if not packages:
        package_output = run_adb(adb_path, ["shell", "pm", "list", "packages", "-3"], serial, timeout=30)
        packages = parse_user_packages(package_output)

    dump = run_adb(adb_path, ["shell", "dumpsys", "package"], serial, timeout=60)
    blocks = package_blocks(dump)
    for item in packages:
        block = blocks.get(str(item["package"]), "")
        indicators: list[str] = []
        if not item["installer"]:
            indicators.append("origem de instalação não informada")
        for label, pattern in PERMISSION_MARKERS:
            if pattern.search(block):
                indicators.append(label)
        item["indicators"] = indicators

    return {"serial": serial, "device": device, "packages": packages}


class AndroidCleaner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Android — diagnóstico e limpeza assistida")
        self.geometry("1040x700")
        self.minsize(820, 560)
        self.adb_path = find_adb()
        self.devices: dict[str, dict[str, str]] = {}
        self.current_serial: str | None = None
        self.package_by_name: dict[str, dict[str, object]] = {}
        self.last_report = ""
        self.busy = False
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.after(120, self._poll_events)
        self.refresh_devices()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Diagnóstico Android por USB", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Leitura local via ADB autorizado. Os indicadores ajudam a revisar apps; não confirmam malware.",
        ).pack(anchor="w", pady=(2, 12))

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Dispositivo:").pack(side="left")
        self.device_box = ttk.Combobox(controls, state="readonly", width=45)
        self.device_box.pack(side="left", padx=(6, 8))
        self.device_box.bind("<<ComboboxSelected>>", self._device_changed)
        self.refresh_button = ttk.Button(controls, text="Atualizar aparelhos", command=self.refresh_devices)
        self.refresh_button.pack(side="left", padx=(0, 6))
        self.scan_button = ttk.Button(controls, text="Fazer diagnóstico", command=self.scan_device)
        self.scan_button.pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Sem depuração USB?", command=self.show_manual_guide).pack(side="left")
        ttk.Button(controls, text="Obter ADB oficial", command=self.open_platform_tools).pack(side="left", padx=(6, 0))

        self.status = tk.StringVar(value="Procurando ADB e aparelhos…")
        ttk.Label(outer, textvariable=self.status, foreground="#245b8a").pack(anchor="w", pady=(0, 8))

        columns = ("package", "installer", "indicators")
        self.apps = ttk.Treeview(outer, columns=columns, show="headings", height=13, selectmode="browse")
        self.apps.heading("package", text="Pacote do aplicativo")
        self.apps.heading("installer", text="Instalador informado")
        self.apps.heading("indicators", text="Pontos para revisar")
        self.apps.column("package", width=300, minwidth=200)
        self.apps.column("installer", width=240, minwidth=160)
        self.apps.column("indicators", width=430, minwidth=240)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.apps.yview)
        self.apps.configure(yscrollcommand=scrollbar.set)
        self.apps.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(10, 8))
        self.uninstall_button = ttk.Button(
            buttons, text="Desinstalar app selecionado…", command=self.uninstall_selected, state="disabled"
        )
        self.uninstall_button.pack(side="left")
        self.save_button = ttk.Button(buttons, text="Salvar relatório…", command=self.save_report, state="disabled")
        self.save_button.pack(side="left", padx=8)
        ttk.Label(
            buttons,
            text="A desinstalação apaga o app e os dados dele e exige confirmação.",
            foreground="#555555",
        ).pack(side="left", padx=8)

        self.output = tk.Text(outer, height=8, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=False)

    def _set_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def _set_busy(self, value: bool, message: str) -> None:
        self.busy = value
        self.status.set(message)
        state = "disabled" if value else "normal"
        self.refresh_button.configure(state=state)
        self.scan_button.configure(state=state)
        self.device_box.configure(state="disabled" if value else "readonly")
        self.uninstall_button.configure(state="disabled")
        self.save_button.configure(state="disabled" if value or not self.last_report else "normal")

    def _run_async(self, work, event_name: str) -> None:
        if self.busy:
            return
        self._set_busy(True, "Executando diagnóstico local…")

        def worker() -> None:
            try:
                result = work()
            except Exception as exc:
                self.events.put(("error", str(exc)))
            else:
                self.events.put((event_name, result))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                event_name, payload = self.events.get_nowait()
                if event_name == "error":
                    self._set_busy(False, "Não foi possível concluir a operação.")
                    messagebox.showerror("Falha no diagnóstico", str(payload), parent=self)
                elif event_name == "devices":
                    self._apply_devices(payload)
                elif event_name == "scan":
                    self._apply_scan(payload)
                elif event_name == "uninstall":
                    self._apply_uninstall(payload)
        except queue.Empty:
            pass
        self.after(120, self._poll_events)

    def refresh_devices(self) -> None:
        if self.busy:
            return
        self._clear_scan()
        self.adb_path = find_adb()
        if not self.adb_path:
            self.devices.clear()
            self.device_box.configure(values=[])
            self.device_box.set("")
            self.current_serial = None
            self.status.set("ADB não encontrado. Instale as Platform Tools ou coloque adb.exe em windows-cleaner/platform-tools/.")
            self._set_output("Sem ADB, o programa não consegue ler o telefone pelo cabo. Use ‘Sem depuração USB?’ para abrir o roteiro manual.")
            return
        adb_path = self.adb_path
        self._run_async(lambda: parse_devices(run_adb(adb_path, ["devices", "-l"], timeout=20)), "devices")

    def _apply_devices(self, result: object) -> None:
        self._set_busy(False, "ADB encontrado. Verifique o estado do aparelho.")
        devices = result if isinstance(result, list) else []
        self.devices.clear()
        labels: list[str] = []
        for item in devices:
            label = f"{item['serial']}  —  {item['state']}"
            if item.get("details"):
                label += f"  ({item['details']})"
            self.devices[label] = item
            labels.append(label)
        self.device_box.configure(values=labels)
        if labels:
            self.device_box.current(0)
            selected = self.devices[labels[0]]
            self.current_serial = selected["serial"] if selected["state"] == "device" else None
            if selected["state"] == "unauthorized":
                self.status.set("Aparelho conectado, mas falta desbloquear e aceitar a autorização RSA na tela do celular.")
            elif selected["state"] != "device":
                self.status.set(f"Estado ADB: {selected['state']}. Desconecte e reconecte o cabo, depois atualize.")
            else:
                self.status.set("Aparelho autorizado. Você pode iniciar o diagnóstico.")
        else:
            self.current_serial = None
            self.status.set("Nenhum aparelho ADB autorizado. Confira o cabo, o modo USB e a depuração USB.")
            self._set_output("Se o aparelho aparecer apenas como transferência de arquivos (MTP), o Windows pode copiar arquivos, mas não executar a limpeza de apps. Abra o roteiro ‘Sem depuração USB?’.")

    def _selected_device(self) -> dict[str, str] | None:
        item = self.devices.get(self.device_box.get())
        return item if item and item["state"] == "device" else None

    def _clear_scan(self) -> None:
        self.current_serial = None
        self.package_by_name.clear()
        self.last_report = ""
        for child in self.apps.get_children():
            self.apps.delete(child)
        self.save_button.configure(state="disabled")
        self.uninstall_button.configure(state="disabled")

    def _device_changed(self, _event=None) -> None:
        self._clear_scan()
        selected = self._selected_device()
        if selected:
            self.status.set("Aparelho autorizado. Clique em Fazer diagnóstico.")
        else:
            self.status.set("Este aparelho ainda não foi autorizado pelo ADB.")

    def open_platform_tools(self) -> None:
        webbrowser.open("https://developer.android.com/tools/releases/platform-tools")

    def scan_device(self) -> None:
        selected = self._selected_device()
        if not selected or not self.adb_path:
            messagebox.showinfo("ADB necessário", "Desbloqueie o celular e autorize esta conexão ADB para iniciar a leitura.", parent=self)
            return
        serial, adb_path = selected["serial"], self.adb_path
        self._run_async(lambda: analyze_device(adb_path, serial), "scan")

    def _apply_scan(self, result: object) -> None:
        self._set_busy(False, "Diagnóstico concluído. Os resultados são indicadores, não um laudo de malware.")
        if not isinstance(result, dict):
            return
        device = result.get("device", {})
        packages = result.get("packages", [])
        self.package_by_name.clear()
        for child in self.apps.get_children():
            self.apps.delete(child)
        lines = [
            f"Dispositivo: {device.get('fabricante', '')} {device.get('modelo', '')}".strip(),
            f"Android: {device.get('android', 'não informado')}  |  Bateria: {device.get('bateria', 'não informada')}",
            f"Aplicativos de usuário encontrados: {len(packages)}",
            "",
            "Indicadores como origem desconhecida ou permissões especiais pedem revisão; não provam infecção.",
            "A varredura não abre arquivos privados dos apps, não envia dados para a internet e não remove nada automaticamente.",
        ]
        for item in packages:
            package = str(item.get("package", ""))
            if not PACKAGE_RE.fullmatch(package):
                continue
            indicators = list(item.get("indicators", []))
            installer = str(item.get("installer") or "não informado")
            indicator_text = "; ".join(indicators) if indicators else "—"
            self.package_by_name[package] = item
            self.apps.insert("", "end", iid=package, values=(package, installer, indicator_text))
            lines.append(f"• {package} | instalador: {installer} | revisar: {indicator_text}")
        self.last_report = "\n".join(lines) + "\n"
        self.current_serial = str(result.get("serial") or "")
        self._set_output("\n".join(lines[:6]))
        self.save_button.configure(state="normal")
        self.uninstall_button.configure(state="normal" if self.package_by_name and self.current_serial else "disabled")

    def uninstall_selected(self) -> None:
        selection = self.apps.selection()
        if not selection:
            messagebox.showinfo("Selecione um aplicativo", "Selecione primeiro um app de usuário na lista.", parent=self)
            return
        package = selection[0]
        if package not in self.package_by_name or not PACKAGE_RE.fullmatch(package):
            messagebox.showerror("Seleção inválida", "Só é permitido selecionar um pacote listado pelo diagnóstico.", parent=self)
            return
        if not self.current_serial or not self.adb_path:
            messagebox.showerror("ADB indisponível", "Atualize a lista de aparelhos e autorize o ADB novamente.", parent=self)
            return
        confirmed = messagebox.askyesno(
            "Confirmar desinstalação",
            f"Desinstalar {package}?\n\nIsso remove o aplicativo e os dados dele. A ação não pode ser desfeita pelo programa.",
            icon="warning",
            parent=self,
        )
        if not confirmed:
            return
        serial, adb_path = self.current_serial, self.adb_path
        self._run_async(lambda: run_adb(adb_path, ["uninstall", package], serial, timeout=60), "uninstall")

    def _apply_uninstall(self, result: object) -> None:
        output = str(result or "").strip()
        if output == "Success":
            self._set_busy(False, "O app selecionado foi desinstalado.")
            self.package_by_name.clear()
            self.last_report = ""
            self.current_serial = None
            self.save_button.configure(state="disabled")
            self.uninstall_button.configure(state="disabled")
            for child in self.apps.get_children():
                self.apps.delete(child)
            self._set_output("Desinstalação concluída. Execute outro diagnóstico para atualizar a lista.")
            messagebox.showinfo("Desinstalação concluída", "O pacote selecionado foi removido.", parent=self)
        else:
            self._set_busy(False, "O Android não confirmou a desinstalação.")
            self._set_output(f"Resposta do ADB:\n{output or 'sem resposta'}")

    def save_report(self) -> None:
        if not self.last_report:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar relatório local",
            defaultextension=".txt",
            filetypes=(("Relatório de texto", "*.txt"),),
            initialfile=f"android-diagnostico-{datetime.now():%Y%m%d-%H%M%S}.txt",
        )
        if path:
            Path(path).write_text(self.last_report, encoding="utf-8")
            messagebox.showinfo("Relatório salvo", "O relatório foi salvo somente no computador, no caminho escolhido.", parent=self)

    def show_manual_guide(self) -> None:
        guide = tk.Toplevel(self)
        guide.title("Limpeza manual sem depuração USB")
        guide.geometry("720x560")
        guide.transient(self)
        frame = ttk.Frame(guide, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Sem depuração USB: roteiro manual", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        text = tk.Text(frame, wrap="word")
        text.pack(fill="both", expand=True, pady=10)
        text.insert(
            "1.0",
            "O modo MTP/Transferência de arquivos só libera cópia de arquivos. Ele não permite ao PC ler dados privados de outros apps, inspecionar permissões ou desinstalá-los.\n\n"
            "1. Desbloqueie o aparelho e conecte um cabo USB de dados. Se quiser apenas copiar arquivos, escolha ‘Transferência de arquivos’ na notificação USB.\n\n"
            "2. No celular, abra Configurações > Aplicativos. Revise apps instalados recentemente ou que você não reconhece. Abra a página do app e use Desinstalar se tiver certeza. Os nomes dos menus variam por fabricante.\n\n"
            "3. Se Desinstalar estiver bloqueado, revise Acessibilidade e Apps de administrador do dispositivo. Desative somente serviços que você reconheça como indesejados; não desative componentes do sistema.\n\n"
            "4. Revise notificações recentes e remova notificações de sites desconhecidos no navegador.\n\n"
            "5. Abra a Play Store > perfil > Play Protect > Verificar. Atualize o Android e os apps pela loja oficial.\n\n"
            "6. Se anúncios continuarem, inicialize em modo seguro seguindo o procedimento do fabricante e repita a revisão de apps. Se houver sinais persistentes, faça backup de fotos/documentos e considere uma restauração de fábrica.\n\n"
            "Para diagnóstico pelo PC, o dono precisa ativar Opções do desenvolvedor > Depuração USB, desbloquear a tela e aceitar a chave RSA deste computador. O programa não contorna essa confirmação.\n\n"
            "Não instale um ‘limpador’ desconhecido transferido por cabo. Um APK instalado manualmente ainda exige confirmação do usuário e, como app comum, não pode limpar os dados privados ou desinstalar silenciosamente outros apps."
        )
        text.configure(state="disabled")
        ttk.Button(frame, text="Fechar", command=guide.destroy).pack(anchor="e")


if __name__ == "__main__":
    AndroidCleaner().mainloop()
