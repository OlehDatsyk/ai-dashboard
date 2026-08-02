# Getting Started with AI Dashboard - Complete Beginner's Guide

This guide assumes you have **never used Python, Git, Visual Studio Code, a terminal, virtual environments, FastAPI/Flask, or any API before.** Every step is spelled out. Follow them in order and you'll have the app running.

If you get stuck at any point, jump to the [Troubleshooting](#troubleshooting) or [FAQ](#faq) section - most beginner problems are already answered there.

---

## Table of contents

1. [What this app is](#1-what-this-app-is)
2. [Install Python](#2-install-python)
3. [Install Git](#3-install-git)
4. [Install Visual Studio Code](#4-install-visual-studio-code)
5. [Install the recommended VS Code extensions](#5-install-the-recommended-vs-code-extensions)
6. [Open the project in VS Code](#6-open-the-project-in-vs-code)
7. [What a terminal is (and how to open one)](#7-what-a-terminal-is-and-how-to-open-one)
8. [Create a virtual environment](#8-create-a-virtual-environment)
9. [Activate the virtual environment](#9-activate-the-virtual-environment)
10. [Install the project's dependencies](#10-install-the-projects-dependencies)
11. [Create your `.env` file](#11-create-your-env-file)
12. [Get and configure an OpenAI API key](#12-get-and-configure-an-openai-api-key)
13. [Run the application](#13-run-the-application)
14. [Test that everything works](#14-test-that-everything-works)
15. [Using every feature](#15-using-every-feature)
16. [Troubleshooting](#troubleshooting)
17. [FAQ](#faq)
18. [Common mistakes](#common-mistakes)
19. [Security recommendations](#security-recommendations)
20. [Next learning steps](#next-learning-steps)

---

## 1. What this app is

AI Dashboard is a small web application that runs on **your own computer**. Once it's running, you open it in your web browser (like Chrome or Safari) at an address like `http://127.0.0.1:5000`, and you'll see an admin-style dashboard with charts, an AI chat assistant, and a "Prompt Playground" for testing prompts against OpenAI's models.

It's written in **Python** (a programming language) using a small web framework called **Flask**. You don't need to know Python to run it - you just need to follow the setup steps below once.

---

## 2. Install Python

Python is the programming language this app is written in. Your computer almost certainly doesn't have the right version installed yet, so let's install it.

1. Go to **https://www.python.org/downloads/** in your web browser.
2. Click the big yellow/blue **Download Python** button (it auto-detects Windows or Mac). You need **Python 3.12 or newer**.
3. Run the downloaded installer.
   - **Windows:** On the very first install screen, **check the box that says "Add python.exe to PATH"** before clicking Install. This step is easy to miss and causes most beginner problems - don't skip it.
   - **Mac:** Run the `.pkg` installer and click through the default prompts.
4. When installation finishes, verify it worked. (See [Section 7](#7-what-a-terminal-is-and-how-to-open-one) if you don't know how to open a terminal yet, then come back here.)

   In your terminal, type:
   ```bash
   python3 --version
   ```
   On Windows you may need `python --version` instead. You should see something like:
   ```
   Python 3.12.4
   ```
   If you see a version number, Python is installed correctly.

---

## 3. Install Git

Git is a tool for downloading and managing code projects. You may not strictly need it if you already have the project folder (e.g. downloaded as a `.zip`), but it's used throughout this guide and is worth having.

1. Go to **https://git-scm.com/downloads**.
2. Download the installer for your operating system.
3. Run it and click "Next" through the default options (the defaults are fine for beginners).
4. Verify it worked by opening a terminal and typing:
   ```bash
   git --version
   ```
   You should see something like `git version 2.45.0`.

> If you already have the `ai-dashboard` project folder on your computer (for example, unzipped from a download), you can skip cloning with Git and just open that folder directly in VS Code in Section 6.

---

## 4. Install Visual Studio Code

Visual Studio Code (VS Code) is a free code editor - think of it like a much more powerful version of Notepad or TextEdit, built for writing and running code.

1. Go to **https://code.visualstudio.com/**.
2. Click **Download**.
3. Run the installer and accept the default options.
4. Open VS Code once to confirm it launches.

---

## 5. Install the recommended VS Code extensions

Extensions add extra functionality to VS Code. Install these two:

1. Open VS Code.
2. Click the **Extensions** icon in the left-hand sidebar (it looks like four small squares, one detached).
3. In the search box, type **Python** and install the official one published by **Microsoft** (`ms-python.python`).
4. Search for **Pylance** and install the official one published by **Microsoft** (`ms-python.vscode-pylance`). This gives you autocomplete and error-checking as you view the code.

You don't need to configure anything else yet - just having them installed is enough.

---

## 6. Open the project in VS Code

1. Make sure you have the `ai-dashboard` project folder somewhere on your computer (e.g. your Desktop or Documents folder), unzipped if it came as a `.zip` file.
2. Open VS Code.
3. Go to **File -> Open Folder...** (on Mac: **File -> Open...**).
4. Select the `ai-dashboard` folder (the one containing `app.py`, `README.md`, etc.) and click **Open** / **Select Folder**.
5. You should now see the file list (`app.py`, `config.py`, `templates/`, `static/`, etc.) in the sidebar on the left.

---

## 7. What a terminal is (and how to open one)

A **terminal** (also called a "console" or "command prompt") is a text-based way to type commands to your computer, instead of clicking icons. We'll use it to run setup commands and start the app.

**Easiest way - inside VS Code:**
1. With the project open in VS Code, go to the top menu and click **Terminal -> New Terminal**.
2. A panel opens at the bottom of the window with a blinking cursor. This is your terminal, and it's already pointed at your project folder - you're ready to type commands.

You'll use this same terminal panel for the rest of this guide.

---

## 8. Create a virtual environment

A **virtual environment** ("venv") is an isolated folder that keeps this project's Python packages separate from everything else on your computer, so installing dependencies here can't break other Python projects (or vice versa).

In the VS Code terminal, type:

```bash
python3 -m venv venv
```

(On Windows, if `python3` isn't recognized, use `python -m venv venv` instead.)

Nothing dramatic will appear to happen - but a new folder named `venv` will show up in your file list on the left. That folder now contains a private copy of Python just for this project.

---

## 9. Activate the virtual environment

"Activating" the virtual environment tells your terminal "use the Python inside `venv/`, not the one installed system-wide." You need to do this **every time** you open a new terminal to work on this project.

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows (PowerShell - the default VS Code terminal):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt / cmd.exe):**
  ```cmd
  venv\Scripts\activate.bat
  ```

When it worked, you'll see `(venv)` appear at the start of the line in your terminal, like:
```
(venv) C:\Users\you\ai-dashboard>
```

> **VS Code tip:** Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on Mac), type "Python: Select Interpreter", and choose the one located inside your `venv` folder. This makes VS Code's autocomplete and error-checking use the right packages too.

---

## 10. Install the project's dependencies

"Dependencies" are the external packages (Flask, the OpenAI library, etc.) this project needs to run. They're listed in `requirements.txt`. With your virtual environment **activated** (you should see `(venv)` in the terminal), run:

```bash
pip install -r requirements.txt
```

You'll see a bunch of text scroll by as each package downloads and installs. This is normal. When it finishes and you're back at a plain prompt, the install succeeded.

---

## 11. Create your `.env` file

The `.env` file holds settings and secrets (like your API key) that shouldn't be shared publicly. The project ships a template called `.env.example` - you copy it to a new file named `.env` and fill in your own values.

- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```
- **Windows:**
  ```cmd
  copy .env.example .env
  ```

Now open the new `.env` file in VS Code (click it in the file list on the left) so you can edit it in the next step.

> **Important:** `.env` is deliberately excluded from Git (see `.gitignore`) so you never accidentally publish your API key. Never remove `.env` from `.gitignore`, and never paste your real key into `.env.example`.

---

## 12. Get and configure an OpenAI API key

The AI Chat and Prompt Playground features need an OpenAI API key to work. (The rest of the dashboard - charts, settings, notifications - works fine without one; AI features are simply disabled until you add a key.)

1. Go to **https://platform.openai.com/api-keys** and sign in (or create an account).
2. Click **Create new secret key**, give it a name, and click Create.
3. **Copy the key immediately** - OpenAI only shows it once. It will look like `sk-...` followed by a long string of letters/numbers.
4. In VS Code, open your `.env` file and find this line:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```
5. Replace the placeholder with your real key, so it looks like:
   ```
   OPENAI_API_KEY=sk-abc123...yourrealkeyhere
   ```
6. Save the file (`Ctrl+S` / `Cmd+S`).

You can leave every other line in `.env` at its default value for now.

> Using the OpenAI API costs money based on usage (typically fractions of a cent per request for small tests). Check current pricing at platform.openai.com before heavy use, and consider setting a spending limit in your OpenAI account settings.

---

## 13. Run the application

With your virtual environment still activated (`(venv)` visible in the terminal), run:

```bash
python app.py
```

You should see log output ending with something like:
```
2026-07-10 09:00:00 [INFO] ai_dashboard: Starting AI Dashboard on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

Now open your web browser and go to:
```
http://127.0.0.1:5000
```

You should see the AI Dashboard home page. 🎉

To stop the app, click back into the terminal and press `Ctrl+C`.

---

## 14. Test that everything works

Run through this quick checklist:

- [ ] The dashboard page loads at `http://127.0.0.1:5000` and shows stat cards and charts (they may show zero values the first time - that's expected, there's no usage history yet).
- [ ] Click **Settings** in the sidebar - the page loads without errors.
- [ ] Click **AI Chat & Prompt Playground** (`/chat`) - the page loads.
- [ ] If you configured an API key: type a message in the chat and send it. You should get a response from the AI within a few seconds.
- [ ] If you did **not** configure an API key yet: you should see a clear on-screen notice that AI features are disabled, rather than a crash. That's the expected, graceful behavior.

If any of these fail, see [Troubleshooting](#troubleshooting) below.

---

## 15. Using every feature

**Dashboard (`/`)**
The home page. Shows requests/tokens/cost stat cards for today/week/month, five charts (requests over time, token usage, cost, prompt categories, response time), a recent activity feed, and your most-used prompts.

**AI Chat widget (floating button, available on every page except `/chat`)**
Click the floating chat icon to open a quick chat panel without leaving your current page. Good for quick one-off questions.

**AI Chat & Prompt Playground (`/chat`)**
This page has two tabs:
- **Chat tab** - a full multi-turn conversation, streamed token-by-token as the AI responds. Toggle "Stream responses" off if you'd rather wait for the full reply at once.
- **Playground tab** - for single-shot prompt experiments. You can:
  - Choose a model and temperature (higher temperature = more random/creative output).
  - Edit the system prompt (instructions that steer the AI's behavior).
  - Toggle "Request structured JSON output" to force the AI to respond with valid JSON.
  - View the result as **Rendered** (formatted Markdown), **JSON** (pretty-printed), or **Raw** text.

**Saved & favorite prompts**
In the Playground, save any prompt with a title and category so you can reuse it later. Click the star icon to mark a prompt as a favorite; filter the list to favorites only.

**Settings (`/settings`)**
Update your display name/email/role (shown in the UI only - not used for authentication), switch between light and dark theme, and set your default AI model/temperature/system prompt.

**Notifications**
Click the bell icon in the top bar to see notifications, mark individual ones as read, or mark all as read.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'flask'`**
Your virtual environment isn't activated, or dependencies weren't installed. Run the activation command from [Section 9](#9-activate-the-virtual-environment) again (you should see `(venv)` in the terminal), then re-run `pip install -r requirements.txt`.

**`'python3' is not recognized as an internal or external command` (Windows)**
Python either isn't installed or wasn't added to PATH. Reinstall Python from [Section 2](#2-install-python) and make sure you check "Add python.exe to PATH" on the first install screen. Try `python` instead of `python3` as well.

**AI features show "not configured" / chat returns an error**
Your `.env` file is missing a real `OPENAI_API_KEY`, or it's still the placeholder value. Re-check [Section 12](#12-get-and-configure-an-openai-api-key), save `.env`, then stop the app (`Ctrl+C`) and run `python app.py` again - `.env` is only read when the app starts.

**Charts don't render / browser console shows a Chart.js error**
The dashboard loads Chart.js and marked.js from an internet CDN. Make sure you're connected to the internet.

**"Port already in use" / the app won't start**
Something else on your computer is already using port 5000 (common on Macs due to the AirPlay Receiver feature). Run the app on a different port instead:
```bash
PORT=5050 python app.py
```
Then visit `http://127.0.0.1:5050` instead.

**Changes to `.env` don't seem to apply**
The app only reads `.env` once, when it starts. Stop it with `Ctrl+C` and run `python app.py` again after any `.env` edit.

**My data (prompts, notifications, settings) disappeared**
All of that is stored in `.json` files inside the `data/` folder, which is deliberately excluded from Git backups. If you deleted the `data/` folder or moved the project without it, that history is gone - the app will simply recreate empty defaults on next run.

**I closed the terminal / restarted my computer - how do I run the app again?**
Open the project in VS Code, open a new terminal, activate your virtual environment again ([Section 9](#9-activate-the-virtual-environment)), then run `python app.py`. Or use the double-click startup scripts described in the README (`Start App.bat` for Windows, `Start App (Mac).command` for macOS) - see below.

---

## FAQ

**Do I need to repeat all these steps every time I want to use the app?**
No. Steps 2-6 (installing software) are one-time. Steps 8 and 10 (creating the venv and installing dependencies) are also one-time - you already have them once done. Each time you come back, you only need to: open the folder in VS Code, open a terminal, activate the virtual environment (Section 9), and run `python app.py`. Or simply double-click the provided startup script.

**Do I have to use VS Code?**
No, any text editor and terminal works. VS Code is recommended because of its built-in terminal and Python support, which makes this guide's steps line up exactly.

**Is my OpenAI API key safe?**
It stays in your local `.env` file, which is excluded from Git by `.gitignore` and never sent anywhere except directly to OpenAI's API when you use the AI features. Never share your `.env` file or paste your key into a public chat, forum, or repository.

**Does the app cost money to run?**
Running the Flask app itself is free. Only the AI Chat/Playground features cost money, and only when you actually send a request - billed by OpenAI based on your account's usage.

**Can I use this without an OpenAI account?**
Yes - the dashboard, settings, and general UI all work without a key. Only the AI-specific features are disabled.

**What is `localhost` / `127.0.0.1`?**
It's a special address that always means "this computer." When the app says it's running on `http://127.0.0.1:5000`, that means it's only reachable from your own machine, not the internet - that's why running it doesn't expose it to anyone else by default.

---

## Common mistakes

1. **Forgetting to activate the virtual environment** before running `pip install` or `python app.py`. If you don't see `(venv)` in your terminal prompt, activate it again.
2. **Not checking "Add to PATH" during Python install on Windows**, causing `python`/`python3` commands to not be recognized. Fix by reinstalling Python and checking that box.
3. **Editing `.env.example` instead of `.env`.** Always copy it to `.env` first (Section 11) and edit the copy - `.env.example` should stay as a template with placeholder values only.
4. **Leaving the placeholder API key in `.env`** (`sk-your-openai-api-key-here`) and wondering why AI features don't work.
5. **Forgetting to restart the app after editing `.env`.** Config is only loaded at startup.
6. **Committing `.env` to Git.** It's git-ignored by default - don't force-add it or remove it from `.gitignore`.
7. **Running `python app.py` from the wrong folder.** Make sure your terminal's current folder is the `ai-dashboard` project folder (VS Code's integrated terminal handles this automatically if you opened the folder correctly in Section 6).

---

## Security recommendations

- **Never commit your `.env` file or your real API key** to Git, a public repository, a chat message, or a screenshot.
- **Set a spending limit** on your OpenAI account so a bug or unexpected usage spike can't run up a large bill.
- **Change `SECRET_KEY` in `.env`** away from the default `change-this-to-a-random-secret-value` before any deployment beyond your own machine (any random long string works).
- **Set `FLASK_DEBUG=False`** in `.env` before running this anywhere other than your own local machine - debug mode can expose an interactive code console to anyone who can reach the app.
- **Keep this app on `127.0.0.1` (localhost)** unless you specifically intend to expose it on your network - changing `HOST` to `0.0.0.0` makes it reachable by other devices on your network/internet.
- **Rotate your API key** (delete the old one, create a new one on platform.openai.com) if you ever suspect it was exposed.

---

## Next learning steps

If this is your first time doing something like this, here's a sensible path forward:

1. **Learn basic terminal commands** - `cd`, `ls`/`dir`, `mkdir`. Many free tutorials exist (search "command line basics for beginners").
2. **Learn Python fundamentals** - official tutorial at https://docs.python.org/3/tutorial/, or an interactive course like https://www.codecademy.com/learn/learn-python-3.
3. **Learn Git basics** - `git init`, `git add`, `git commit`, `git push`. Try https://learngitbranching.js.org/ for a visual, interactive way to learn.
4. **Learn Flask** - since this project uses it, the official Flask quickstart (https://flask.palletsprojects.com/) is a great next step to understand `app.py`.
5. **Read through this project's own `README.md`** - it documents the architecture, API endpoints, and deployment options in more depth once you're comfortable with the basics above.
6. **Try making a small change** - e.g. edit the sidebar text in `templates/base.html`, save, and refresh your browser to see it update. Small experiments like this are the fastest way to build confidence.
