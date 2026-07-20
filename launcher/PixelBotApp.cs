using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

public class PixelBotForm : Form
{
    private readonly Button startButton = new Button();
    private readonly Button openFolderButton = new Button();
    private readonly Button clearButton = new Button();
    private readonly Button sendButton = new Button();
    private readonly TextBox commandBox = new TextBox();
    private readonly TextBox logBox = new TextBox();
    private readonly Label statusLabel = new Label();
    private readonly string repo;
    private readonly string launcherDir;
    private readonly string runner;
    private readonly List<string> history = new List<string>();
    private string lastCommand = "";
    private bool developerMode = false;
    private bool safeMode = true;

    public PixelBotForm()
    {
        repo = FindRepository();
        launcherDir = Path.Combine(repo, "launcher");
        runner = Path.Combine(launcherDir, "RUN_AUTO_005_2.ps1");

        Text = "Pixel Bot - MAGI Brain v3";
        Width = 860;
        Height = 690;
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(720, 540);
        BackColor = Color.FromArgb(18, 24, 38);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10F);

        try
        {
            string iconPath = Path.Combine(launcherDir, "PixelBot.ico");
            if (File.Exists(iconPath)) Icon = new Icon(iconPath);
        }
        catch { }

        Label title = new Label { Text = "PIXEL BOT", Font = new Font("Segoe UI Semibold", 24F, FontStyle.Bold), AutoSize = true, Left = 24, Top = 18 };
        Label subtitle = new Label { Text = "Cervello MAGI + OpenAI - ogni richiesta passa dal consiglio", AutoSize = true, Left = 28, Top = 62, ForeColor = Color.LightGray };

        startButton.Text = "▶  Avvia Pixel Bot";
        startButton.SetBounds(26, 100, 210, 48);
        startButton.Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold);
        startButton.Click += async delegate { await RunPixelBotAsync(); };

        openFolderButton.Text = "Apri cartella progetto";
        openFolderButton.SetBounds(250, 100, 190, 48);
        openFolderButton.Click += delegate { OpenPath(repo); };

        clearButton.Text = "Pulisci log";
        clearButton.SetBounds(454, 100, 120, 48);
        clearButton.Click += delegate { logBox.Clear(); };

        statusLabel.Text = "Pronto | Sicura: ON";
        statusLabel.AutoSize = true;
        statusLabel.Left = 28;
        statusLabel.Top = 164;
        statusLabel.ForeColor = Color.LightGreen;

        Label commandLabel = new Label { Text = "Scrivi un comando naturale", AutoSize = true, Left = 28, Top = 196, ForeColor = Color.LightGray };

        commandBox.SetBounds(26, 220, 690, 34);
        commandBox.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        commandBox.BackColor = Color.FromArgb(9, 13, 22);
        commandBox.ForeColor = Color.White;
        commandBox.BorderStyle = BorderStyle.FixedSingle;
        commandBox.Font = new Font("Segoe UI", 11F);
        commandBox.KeyDown += async delegate(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                e.SuppressKeyPress = true;
                await ExecuteCommandAsync(commandBox.Text, true);
            }
        };

        sendButton.Text = "Invia";
        sendButton.SetBounds(728, 220, 90, 34);
        sendButton.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        sendButton.Click += async delegate { await ExecuteCommandAsync(commandBox.Text, true); };

        logBox.Multiline = true;
        logBox.ReadOnly = true;
        logBox.ScrollBars = ScrollBars.Both;
        logBox.WordWrap = false;
        logBox.BackColor = Color.FromArgb(9, 13, 22);
        logBox.ForeColor = Color.Gainsboro;
        logBox.Font = new Font("Consolas", 9.5F);
        logBox.SetBounds(26, 270, 792, 365);
        logBox.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;

        Controls.AddRange(new Control[] { title, subtitle, startButton, openFolderButton, clearButton, statusLabel, commandLabel, commandBox, sendButton, logBox });

        Shown += delegate
        {
            AppendLog("Pixel Bot MAGI Brain v3 pronto.");
            AppendLog("Repository: " + repo);
            AppendLog("Ogni messaggio viene valutato da MAGI e inviato al cervello OpenAI.");
            commandBox.Focus();
        };
    }

    private string FindRepository()
    {
        string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        string[] candidates = new string[]
        {
            Path.Combine(home, "OneDrive", "Dokumenty", "GitHub", "Pixel-Bot"),
            Path.Combine(home, "OneDrive", "Documents", "GitHub", "Pixel-Bot"),
            Path.Combine(home, "Documents", "GitHub", "Pixel-Bot"),
            Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, ".."))
        };
        foreach (string candidate in candidates)
            if (Directory.Exists(candidate)) return candidate;
        return candidates[0];
    }

    private async Task ExecuteCommandAsync(string rawCommand, bool remember)
    {
        string command = (rawCommand ?? "").Trim();
        if (command.Length == 0) return;
        commandBox.Clear();
        AppendLog("");
        AppendLog("Tu: " + command);

        if (remember && !IsRepeatCommand(command))
        {
            lastCommand = command;
            history.Add(DateTime.Now.ToString("HH:mm:ss") + "  " + command);
            if (history.Count > 100) history.RemoveAt(0);
        }

        SetWorking("Consultazione MAGI e OpenAI...");
        try
        {
            BrainResult brain = await AskBrainAsync(command);
            AppendLog("--- CERVELLO MAGI ---");
            if (!String.IsNullOrWhiteSpace(brain.MagiSummary)) AppendLog(brain.MagiSummary);
            if (!String.IsNullOrWhiteSpace(brain.Answer)) AppendLog("Pixel Bot: " + brain.Answer);
            if (!String.IsNullOrWhiteSpace(brain.Error)) AppendLog("Cervello: " + brain.Error);
            AppendLog("--- AZIONE LOCALE ---");

            string n = Normalize(command);

            if (Matches(n, "aiuto", "help", "cosa puoi fare", "comandi", "mostra comandi"))
                ShowHelp();
            else if (Matches(n, "ripeti ultimo comando", "ripeti", "di nuovo"))
                await RepeatLastCommandAsync();
            else if (Matches(n, "mostra cronologia", "cronologia", "storico comandi"))
                ShowHistory();
            else if (Matches(n, "pulisci cronologia", "cancella cronologia"))
            {
                history.Clear();
                AppendLog("Pixel Bot: cronologia cancellata.");
            }
            else if (Matches(n, "modalita sicura", "attiva modalita sicura"))
            {
                safeMode = true;
                AppendLog("Pixel Bot: modalità sicura attivata.");
            }
            else if (Matches(n, "disattiva modalita sicura"))
            {
                if (Confirm("Disattivare la modalità sicura? Le azioni sensibili richiederanno comunque conferma."))
                {
                    safeMode = false;
                    AppendLog("Pixel Bot: modalità sicura disattivata.");
                }
            }
            else if (Matches(n, "modalita sviluppatore", "attiva modalita sviluppatore"))
            {
                developerMode = true;
                AppendLog("Pixel Bot: modalità sviluppatore attivata.");
            }
            else if (Matches(n, "disattiva modalita sviluppatore"))
            {
                developerMode = false;
                AppendLog("Pixel Bot: modalità sviluppatore disattivata.");
            }
            else if (ContainsAny(n, "apri chrome", "avvia chrome", "lancia chrome", "apri browser", "lancia il browser", "aprimi google chrome"))
                StartShell("chrome.exe", "Chrome aperto.");
            else if (ContainsAny(n, "apri esplora file", "apri esplora risorse", "apri file explorer"))
                StartShell("explorer.exe", "Esplora file aperto.");
            else if (ContainsAny(n, "apri powershell", "avvia powershell", "lancia powershell"))
                StartShell("powershell.exe", "PowerShell aperto.");
            else if (ContainsAny(n, "apri impostazioni", "impostazioni windows"))
                StartShell("ms-settings:", "Impostazioni aperte.");
            else if (ContainsAny(n, "apri vscode", "apri visual studio code", "avvia vscode"))
                StartShellWithArgs("code", "\"" + repo + "\"", "Visual Studio Code aperto sul progetto.");
            else if (ContainsAny(n, "apri cartella progetto", "apri progetto", "mostra progetto"))
            {
                OpenPath(repo);
                AppendLog("Pixel Bot: cartella progetto aperta.");
            }
            else if (ContainsAny(n, "mostra download", "apri download"))
                OpenPath(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Downloads");
            else if (ContainsAny(n, "mostra desktop", "apri desktop"))
                OpenPath(Environment.GetFolderPath(Environment.SpecialFolder.Desktop));
            else if (ContainsAny(n, "stato git", "git status", "controlla git"))
                await RunProcessAsync("git.exe", "status --short --branch", repo, "STATO GIT");
            else if (ContainsAny(n, "git diff", "mostra differenze git", "differenze git"))
                await RunProcessAsync("git.exe", "diff --stat && git diff", repo, "GIT DIFF");
            else if (ContainsAny(n, "ultimi commit", "log git", "git log"))
                await RunProcessAsync("git.exe", "log -10 --oneline --decorate", repo, "ULTIMI COMMIT");
            else if (ContainsAny(n, "avvia test veloci", "test veloci"))
                await RunTestsAsync("-m pytest -q --maxfail=1");
            else if (ContainsAny(n, "avvia test", "esegui test", "pytest") || n == "test")
                await RunTestsAsync("-m pytest -q");
            else if (ContainsAny(n, "apri log", "mostra log"))
                OpenFirstExisting(new string[] { Path.Combine(repo, "logs"), Path.Combine(repo, "log"), launcherDir });
            else if (ContainsAny(n, "crea backup progetto", "backup progetto", "fai backup"))
                await CreateBackupAsync();
            else if (ContainsAny(n, "fai screenshot", "screenshot", "cattura schermo"))
                await TakeScreenshotAsync();
            else if (ContainsAny(n, "apri screenshot", "mostra screenshot"))
                OpenPath(Path.Combine(repo, "screenshots"));
            else if (ContainsAny(n, "elenca finestre aperte", "finestre aperte"))
                await ListWindowsAsync();
            else if (ContainsAny(n, "porta chrome in primo piano", "mostra chrome"))
                await BringChromeToFrontAsync();
            else if (ContainsAny(n, "avvia pixel bot", "avvia bot") || n == "avvia")
                await RunPixelBotAsync();
            else if (n.StartsWith("cerca file "))
                SearchFiles(command.Substring(command.ToLowerInvariant().IndexOf("cerca file ") + 11).Trim());
            else if (n.StartsWith("apri file "))
                OpenFileByName(command.Substring(command.ToLowerInvariant().IndexOf("apri file ") + 10).Trim());
            else if (n.StartsWith("crea cartella "))
                CreateFolder(command.Substring(command.ToLowerInvariant().IndexOf("crea cartella ") + 13).Trim());
            else if (ContainsAny(n, "blocca pc", "blocca computer"))
                RunConfirmed("Bloccare adesso il PC?", "rundll32.exe", "user32.dll,LockWorkStation", "PC bloccato.");
            else if (ContainsAny(n, "spegni pc", "spegni computer"))
                RunConfirmed("Spegnere il PC adesso?", "shutdown.exe", "/s /t 0", "Spegnimento avviato.");
            else if (ContainsAny(n, "riavvia pc", "riavvia computer"))
                RunConfirmed("Riavviare il PC adesso?", "shutdown.exe", "/r /t 0", "Riavvio avviato.");
            else if (ContainsAny(n, "annulla ultima azione", "annulla"))
                AppendLog("Pixel Bot: non posso annullare automaticamente un'azione già completata. Le operazioni sensibili richiedono conferma prima dell'esecuzione.");
            else
                AppendLog("Pixel Bot: risposta completata dal cervello. Nessuna azione locale automatica associata.");
        }
        catch (Exception ex)
        {
            AppendLog("Pixel Bot: ERRORE: " + ex.Message);
        }
        finally
        {
            statusLabel.Text = "Pronto | Sicura: " + (safeMode ? "ON" : "OFF") + " | Dev: " + (developerMode ? "ON" : "OFF");
            statusLabel.ForeColor = Color.LightGreen;
            commandBox.Focus();
        }
    }

    private void ShowHelp()
    {
        AppendLog("Pixel Bot: ogni richiesta passa sempre da MAGI + OpenAI. I comandi seguenti possono anche attivare strumenti locali:");
        AppendLog("SISTEMA: apri Chrome | Esplora file | PowerShell | Impostazioni | VS Code");
        AppendLog("PROGETTO: apri progetto | stato git | git diff | ultimi commit | avvia test | test veloci | apri log | crea backup progetto");
        AppendLog("SCHERMO: fai screenshot | apri screenshot | elenca finestre aperte | porta Chrome in primo piano");
        AppendLog("FILE: cerca file NOME | apri file NOME | crea cartella NOME | mostra Download | mostra Desktop");
        AppendLog("MEMORIA: ripeti ultimo comando | mostra cronologia | pulisci cronologia");
        AppendLog("MODALITÀ: modalità sicura | disattiva modalità sicura | modalità sviluppatore");
        AppendLog("SENSIBILI: blocca PC | spegni PC | riavvia PC (sempre con conferma)");
    }

    private sealed class BrainResult
    {
        public string Answer = "";
        public string MagiSummary = "";
        public string Error = "";
    }

    private async Task<BrainResult> AskBrainAsync(string command)
    {
        BrainResult result = new BrainResult();
        string bridge = Path.Combine(launcherDir, "pixelbot_brain_bridge.py");
        if (!File.Exists(bridge))
        {
            result.Error = "bridge del cervello non trovato: " + bridge;
            return result;
        }

        string python = Path.Combine(repo, ".venv", "Scripts", "python.exe");
        if (!File.Exists(python)) python = "python.exe";
        string requestDir = Path.Combine(repo, "workspace", "brain-requests");
        Directory.CreateDirectory(requestDir);
        string requestFile = Path.Combine(requestDir, "request-" + DateTime.Now.ToString("yyyyMMdd-HHmmss-fff") + ".txt");
        File.WriteAllText(requestFile, command, new UTF8Encoding(false));

        string output = await RunCaptureAsync(python, "\"" + bridge + "\" --repo \"" + repo + "\" --request-file \"" + requestFile + "\"", repo);
        foreach (string line in output.Replace("\r", "").Split('\n'))
        {
            if (line.StartsWith("PIXELBOT_ANSWER_B64=")) result.Answer = DecodeB64(line.Substring(20));
            else if (line.StartsWith("PIXELBOT_MAGI_B64=")) result.MagiSummary = DecodeB64(line.Substring(18));
            else if (line.StartsWith("PIXELBOT_ERROR_B64=")) result.Error = DecodeB64(line.Substring(19));
        }
        if (String.IsNullOrWhiteSpace(result.Answer) && String.IsNullOrWhiteSpace(result.Error))
            result.Error = "il cervello non ha restituito una risposta valida.";
        return result;
    }

    private async Task<string> RunCaptureAsync(string fileName, string arguments, string workingDirectory)
    {
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = fileName,
            Arguments = arguments,
            WorkingDirectory = workingDirectory,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };
        using (Process process = new Process())
        {
            process.StartInfo = psi;
            process.Start();
            Task<string> stdout = process.StandardOutput.ReadToEndAsync();
            Task<string> stderr = process.StandardError.ReadToEndAsync();
            await Task.Run(delegate { process.WaitForExit(); });
            string outText = await stdout;
            string errText = await stderr;
            if (process.ExitCode != 0 && !String.IsNullOrWhiteSpace(errText))
                return outText + Environment.NewLine + "PIXELBOT_ERROR_B64=" + Convert.ToBase64String(Encoding.UTF8.GetBytes(errText.Trim()));
            return outText;
        }
    }

    private string DecodeB64(string value)
    {
        try { return Encoding.UTF8.GetString(Convert.FromBase64String(value.Trim())); }
        catch { return value; }
    }

    private async Task RepeatLastCommandAsync()
    {
        if (String.IsNullOrWhiteSpace(lastCommand))
        {
            AppendLog("Pixel Bot: non c'è ancora un comando da ripetere.");
            return;
        }
        AppendLog("Pixel Bot: ripeto: " + lastCommand);
        await ExecuteCommandAsync(lastCommand, false);
    }

    private void ShowHistory()
    {
        if (history.Count == 0) { AppendLog("Pixel Bot: cronologia vuota."); return; }
        AppendLog("Pixel Bot: ultimi comandi:");
        int start = Math.Max(0, history.Count - 20);
        for (int i = start; i < history.Count; i++) AppendLog((i + 1) + ". " + history[i]);
    }

    private async Task RunTestsAsync(string args)
    {
        string python = Path.Combine(repo, ".venv", "Scripts", "python.exe");
        if (!File.Exists(python)) python = "python.exe";
        await RunProcessAsync(python, args, repo, "TEST");
    }

    private async Task CreateBackupAsync()
    {
        string backupDir = Path.Combine(repo, "backups");
        Directory.CreateDirectory(backupDir);
        string zip = Path.Combine(backupDir, "Pixel-Bot-backup-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".zip");
        string ps = "$src='" + EscapePs(repo) + "';$dst='" + EscapePs(zip) + "';Get-ChildItem $src -Force | Where-Object {$_.Name -notin @('.git','.venv','backups')} | Compress-Archive -DestinationPath $dst -Force";
        await RunProcessAsync("powershell.exe", "-NoProfile -Command \"" + ps.Replace("\"", "\\\"") + "\"", repo, "BACKUP PROGETTO");
        if (File.Exists(zip)) AppendLog("Pixel Bot: backup creato: " + zip);
    }

    private async Task TakeScreenshotAsync()
    {
        string screenshots = Path.Combine(repo, "screenshots");
        Directory.CreateDirectory(screenshots);
        string output = Path.Combine(screenshots, "screenshot-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".png");
        string ps = "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;$i=New-Object Drawing.Bitmap $b.Width,$b.Height;$g=[Drawing.Graphics]::FromImage($i);$g.CopyFromScreen($b.Location,[Drawing.Point]::Empty,$b.Size);$i.Save('" + EscapePs(output) + "',[Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$i.Dispose()";
        await RunProcessAsync("powershell.exe", "-NoProfile -STA -Command \"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; " + ps.Replace("\"", "\\\"") + "\"", repo, "SCREENSHOT");
        if (File.Exists(output)) AppendLog("Pixel Bot: screenshot salvato in " + output);
    }

    private async Task ListWindowsAsync()
    {
        string ps = "Get-Process | Where-Object {$_.MainWindowTitle} | Sort-Object ProcessName | Select-Object ProcessName,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 220";
        await RunProcessAsync("powershell.exe", "-NoProfile -Command \"" + ps + "\"", repo, "FINESTRE APERTE");
    }

    private async Task BringChromeToFrontAsync()
    {
        string ps = "$p=Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1;if(!$p){Write-Error 'Chrome non trovato';exit 1};Add-Type '[DllImport(\"user32.dll\")]public static extern bool SetForegroundWindow(IntPtr hWnd);' -Name Win32 -Namespace Native;[Native.Win32]::SetForegroundWindow($p.MainWindowHandle) | Out-Null";
        await RunProcessAsync("powershell.exe", "-NoProfile -Command \"" + ps.Replace("\"", "\\\"") + "\"", repo, "CHROME IN PRIMO PIANO");
    }

    private void SearchFiles(string term)
    {
        if (String.IsNullOrWhiteSpace(term)) { AppendLog("Pixel Bot: specifica il nome da cercare."); return; }
        AppendLog("Pixel Bot: cerco file contenenti '" + term + "'...");
        int count = 0;
        try
        {
            foreach (string file in Directory.EnumerateFiles(repo, "*", SearchOption.AllDirectories))
            {
                if (file.IndexOf("\\.git\\", StringComparison.OrdinalIgnoreCase) >= 0 || file.IndexOf("\\.venv\\", StringComparison.OrdinalIgnoreCase) >= 0) continue;
                if (Path.GetFileName(file).IndexOf(term, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    AppendLog(file);
                    count++;
                    if (count >= 30) { AppendLog("Pixel Bot: risultati limitati ai primi 30."); break; }
                }
            }
        }
        catch (Exception ex) { AppendLog("Pixel Bot: ricerca interrotta: " + ex.Message); }
        if (count == 0) AppendLog("Pixel Bot: nessun file trovato.");
    }

    private void OpenFileByName(string term)
    {
        if (String.IsNullOrWhiteSpace(term)) { AppendLog("Pixel Bot: specifica il file da aprire."); return; }
        string found = null;
        try
        {
            foreach (string file in Directory.EnumerateFiles(repo, "*", SearchOption.AllDirectories))
            {
                if (file.IndexOf("\\.git\\", StringComparison.OrdinalIgnoreCase) >= 0 || file.IndexOf("\\.venv\\", StringComparison.OrdinalIgnoreCase) >= 0) continue;
                if (Path.GetFileName(file).IndexOf(term, StringComparison.OrdinalIgnoreCase) >= 0) { found = file; break; }
            }
        }
        catch { }
        if (found == null) { AppendLog("Pixel Bot: file non trovato."); return; }
        StartShell(found, "File aperto: " + found);
    }

    private void CreateFolder(string name)
    {
        name = (name ?? "").Trim().Trim('"');
        if (name.Length == 0 || name.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0) { AppendLog("Pixel Bot: nome cartella non valido."); return; }
        string path = Path.Combine(repo, name);
        Directory.CreateDirectory(path);
        AppendLog("Pixel Bot: cartella creata: " + path);
    }

    private void OpenFirstExisting(string[] paths)
    {
        foreach (string path in paths)
        {
            if (Directory.Exists(path) || File.Exists(path)) { OpenPath(path); AppendLog("Pixel Bot: aperto " + path); return; }
        }
        AppendLog("Pixel Bot: nessun percorso log trovato.");
    }

    private void OpenPath(string path)
    {
        if (path.EndsWith("screenshots", StringComparison.OrdinalIgnoreCase)) Directory.CreateDirectory(path);
        Process.Start(new ProcessStartInfo("explorer.exe", "\"" + path + "\"") { UseShellExecute = true });
    }

    private void StartShell(string target, string success)
    {
        Process.Start(new ProcessStartInfo(target) { UseShellExecute = true });
        AppendLog("Pixel Bot: " + success);
    }

    private void StartShellWithArgs(string target, string args, string success)
    {
        Process.Start(new ProcessStartInfo(target, args) { UseShellExecute = true });
        AppendLog("Pixel Bot: " + success);
    }

    private void RunConfirmed(string question, string file, string args, string success)
    {
        if (!Confirm(question)) { AppendLog("Pixel Bot: operazione annullata."); return; }
        Process.Start(new ProcessStartInfo(file, args) { UseShellExecute = true });
        AppendLog("Pixel Bot: " + success);
    }

    private bool Confirm(string question)
    {
        return MessageBox.Show(question, "Conferma Pixel Bot", MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) == DialogResult.Yes;
    }

    private async Task RunPixelBotAsync()
    {
        if (!File.Exists(runner))
        {
            AppendLog("Pixel Bot: script non trovato: " + runner);
            return;
        }
        await RunProcessAsync("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File \"" + runner + "\" -Repo \"" + repo + "\"", repo, "AVVIO PIXEL BOT");
    }

    private async Task RunProcessAsync(string fileName, string arguments, string workingDirectory, string title)
    {
        startButton.Enabled = false;
        sendButton.Enabled = false;
        SetWorking("In esecuzione...");
        AppendLog("=== " + title + " ===");

        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = fileName,
            Arguments = arguments,
            WorkingDirectory = workingDirectory,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        using (Process process = new Process())
        {
            process.StartInfo = psi;
            process.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendLog(e.Data); };
            process.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) AppendLog("ERRORE: " + e.Data); };
            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            await Task.Run(delegate { process.WaitForExit(); });
            AppendLog("=== FINE, codice uscita: " + process.ExitCode + " ===");
            statusLabel.Text = process.ExitCode == 0 ? "Completato" : "Terminato con errori";
            statusLabel.ForeColor = process.ExitCode == 0 ? Color.LightGreen : Color.Salmon;
        }

        startButton.Enabled = true;
        sendButton.Enabled = true;
    }

    private void SetWorking(string text)
    {
        statusLabel.Text = text;
        statusLabel.ForeColor = Color.Khaki;
    }

    private string Normalize(string value)
    {
        string s = value.ToLowerInvariant().Trim();
        s = s.Replace("à", "a").Replace("è", "e").Replace("é", "e").Replace("ì", "i").Replace("ò", "o").Replace("ù", "u");
        while (s.Contains("  ")) s = s.Replace("  ", " ");
        return s;
    }

    private bool Matches(string value, params string[] options)
    {
        foreach (string option in options) if (value == Normalize(option)) return true;
        return false;
    }

    private bool ContainsAny(string value, params string[] options)
    {
        foreach (string option in options) if (value.Contains(Normalize(option))) return true;
        return false;
    }

    private bool IsRepeatCommand(string value)
    {
        string n = Normalize(value);
        return Matches(n, "ripeti ultimo comando", "ripeti", "di nuovo");
    }

    private string EscapePs(string value) { return value.Replace("'", "''"); }

    private void AppendLog(string text)
    {
        if (InvokeRequired) { BeginInvoke(new Action<string>(AppendLog), text); return; }
        logBox.AppendText(text + Environment.NewLine);
    }

    [STAThread]
    public static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new PixelBotForm());
    }
}
