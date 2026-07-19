using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

public class PixelBotForm : Form
{
    private readonly Button startButton = new Button();
    private readonly Button openFolderButton = new Button();
    private readonly Button clearButton = new Button();
    private readonly TextBox logBox = new TextBox();
    private readonly Label statusLabel = new Label();
    private readonly string repo;
    private readonly string launcherDir;
    private readonly string runner;

    public PixelBotForm()
    {
        repo = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            "OneDrive", "Dokumenty", "GitHub", "Pixel-Bot");
        launcherDir = Path.Combine(repo, "launcher");
        runner = Path.Combine(launcherDir, "RUN_AUTO_005_2.ps1");

        Text = "Pixel Bot";
        Width = 760;
        Height = 540;
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(650, 430);
        BackColor = Color.FromArgb(18, 24, 38);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10F);

        try
        {
            var iconPath = Path.Combine(launcherDir, "PixelBot.ico");
            if (File.Exists(iconPath)) Icon = new Icon(iconPath);
        }
        catch { }

        var title = new Label
        {
            Text = "PIXEL BOT",
            Font = new Font("Segoe UI Semibold", 24F, FontStyle.Bold),
            AutoSize = true,
            Left = 24,
            Top = 18
        };

        var subtitle = new Label
        {
            Text = "Centro di controllo locale",
            AutoSize = true,
            Left = 28,
            Top = 62,
            ForeColor = Color.LightGray
        };

        startButton.Text = "▶  Avvia Pixel Bot";
        startButton.SetBounds(26, 100, 210, 48);
        startButton.Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold);
        startButton.Click += async (s, e) => await RunPixelBotAsync();

        openFolderButton.Text = "Apri cartella progetto";
        openFolderButton.SetBounds(250, 100, 190, 48);
        openFolderButton.Click += (s, e) => OpenFolder();

        clearButton.Text = "Pulisci log";
        clearButton.SetBounds(454, 100, 120, 48);
        clearButton.Click += (s, e) => logBox.Clear();

        statusLabel.Text = "Pronto";
        statusLabel.AutoSize = true;
        statusLabel.Left = 28;
        statusLabel.Top = 164;
        statusLabel.ForeColor = Color.LightGreen;

        logBox.Multiline = true;
        logBox.ReadOnly = true;
        logBox.ScrollBars = ScrollBars.Both;
        logBox.WordWrap = false;
        logBox.BackColor = Color.FromArgb(9, 13, 22);
        logBox.ForeColor = Color.Gainsboro;
        logBox.Font = new Font("Consolas", 9.5F);
        logBox.SetBounds(26, 192, 690, 292);
        logBox.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;

        Controls.Add(title);
        Controls.Add(subtitle);
        Controls.Add(startButton);
        Controls.Add(openFolderButton);
        Controls.Add(clearButton);
        Controls.Add(statusLabel);
        Controls.Add(logBox);

        Shown += (s, e) =>
        {
            AppendLog("Pixel Bot pronto.");
            AppendLog("Repository: " + repo);
            if (!File.Exists(runner))
                AppendLog("ATTENZIONE: script non trovato: " + runner);
        };
    }

    private void OpenFolder()
    {
        try
        {
            Directory.CreateDirectory(repo);
            Process.Start(new ProcessStartInfo("explorer.exe", "\"" + repo + "\"") { UseShellExecute = true });
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Pixel Bot", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private async Task RunPixelBotAsync()
    {
        if (!Directory.Exists(repo))
        {
            MessageBox.Show("Repository non trovato:\n" + repo, "Pixel Bot", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        if (!File.Exists(runner))
        {
            MessageBox.Show("Script di avvio non trovato:\n" + runner, "Pixel Bot", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        startButton.Enabled = false;
        statusLabel.Text = "In esecuzione...";
        statusLabel.ForeColor = Color.Khaki;
        AppendLog("");
        AppendLog("=== AVVIO PIXEL BOT ===");

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows),
                    "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
                Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + runner + "\" -Repo \"" + repo + "\"",
                WorkingDirectory = repo,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            using (var process = new Process { StartInfo = psi, EnableRaisingEvents = true })
            {
                process.OutputDataReceived += (s, e) => { if (e.Data != null) AppendLog(e.Data); };
                process.ErrorDataReceived += (s, e) => { if (e.Data != null) AppendLog("ERRORE: " + e.Data); };
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                await Task.Run(() => process.WaitForExit());

                AppendLog("=== FINE, codice uscita: " + process.ExitCode + " ===");
                statusLabel.Text = process.ExitCode == 0 ? "Completato" : "Terminato con errori";
                statusLabel.ForeColor = process.ExitCode == 0 ? Color.LightGreen : Color.Salmon;
            }
        }
        catch (Exception ex)
        {
            AppendLog("ERRORE FATALE: " + ex);
            statusLabel.Text = "Errore";
            statusLabel.ForeColor = Color.Salmon;
        }
        finally
        {
            startButton.Enabled = true;
        }
    }

    private void AppendLog(string text)
    {
        if (InvokeRequired)
        {
            BeginInvoke(new Action<string>(AppendLog), text);
            return;
        }
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
