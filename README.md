<div align="center">

<img src="./assets/VoxOS%20logo.jpeg" alt="Vox OS Logo" width="600"/>

<br><br>

# 🤖 Vox OS

### Your Computer. Your Voice. Your AI.

**An AI-powered voice-controlled desktop assistant for interacting with and automating your Windows computer using natural language.**

<br>

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-Package%20Manager-DE5FE9?style=for-the-badge)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Under%20Development-orange?style=for-the-badge)

<br>

</div>

---

## 🧠 About The Project

**Vox OS** is an AI-powered desktop assistant designed to allow users to control their computer using natural voice commands. Instead of navigating through applications manually, users can interact with their computer conversationally.

### How It Works

```text
                 🎙️ USER
                  │
                  ▼
          ┌──────────────────┐
          │  Audio Capture   │
          │   sounddevice    │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Voice Activity   │
          │    Detection     │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Speech-to-Text  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │    AI / Intent   │
          │      Engine      │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Command Router   │
          └────────┬─────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      🖥️ System   📱 Apps    🌐 Web
        │          │          │
        └──────────┼──────────┘
                   ▼
              💻 WINDOWS
```

## 🎯 Core Goals

Vox OS is being built around these principles:
- 🎙️ Natural voice interaction

- 🧠 AI-powered intent understanding

- ⚡ Fast command processing (Zero-latency architecture)

- 🖥️ Windows automation

- 🧩 Modular architecture

- 🔌 Extensible tool system

- 🔐 Safe system-level execution

- 🚀 Dynamic application control

## 🎙️ Voice Processing Pipeline

The Vox OS voice engine is designed as a modular pipeline that converts human speech into a command that can be understood and executed by the system.

```text
🎤 Microphone
      │
      ▼
┌─────────────────┐
│   sounddevice   │
│  Audio Capture  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audio Stream   │
│  Real-time Data │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Voice Activity  │
│    Detection    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Speech-to-Text  │
│      (STT)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Text Command   │
│                 │
│ "Open Chrome"   │
└─────────────────┘
```

### Why sounddevice?

sounddevice provides Python access to the computer's audio devices through PortAudio. It is responsible for microphone input, audio output, and real-time audio callbacks. It does not perform speech recognition. Speech recognition and AI processing happen asynchronously in later layers.

## 🧠 AI Intent Engine

The **AI Intent Engine** is the reasoning layer of Vox OS. Its primary responsibility is to transform natural-language input into a **structured**, **machine-readable intent** that the **Command Layer** can safely process. The AI decides what the user wants, while the execution layer decides how to perform it.

```text
Natural Language
       │
       ▼
┌────────────────────┐
│   AI Intent Engine │
│                    │
│ Understand request │
│ + identify target  │
└─────────┬──────────┘
          │
          ▼
   Structured Intent
```

## 🧩 Dynamic Application Control

Vox OS is designed to understand what the user wants to do separately from how the action is executed. This allows the system to support applications dynamically instead of requiring a hardcoded Python script for every application.

Instead of writing chrome.py, spotify.py, or vscode.py, Vox OS is designed around a generic application resolver:

```text
User Command ➔ Intent Detection ➔ Application Resolver ➔ Windows Execution
```

# 🏗️ Architecture

The backend is built using a strict modular monolith architecture communicating via an asynchronous event bus:

``` text
Vox OS
│
├── Voice Layer
│   ├── Audio Capture
│   ├── Voice Activity Detection
│   ├── Speech-to-Text
│   └── Text-to-Speech
│
├── Intelligence Layer
│   ├── Intent Recognition
│   ├── Context Management
│   ├── Planning
│   └── Tool Selection
│
├── Command Layer
│   ├── Command Registry
│   ├── Command Router
│   └── Validation
│
└── Automation Layer
    ├── System Control
    ├── Application Control
    ├── File Operations
    └── Browser Automation

```

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 **Python** | Backend, AI integration & automation |
| ⚡ **uv** | Blazing-fast Python package & environment management |
| 🎤 **sounddevice** | Zero-latency audio input/output |
| 🔢 **NumPy** | Audio & numerical processing |
| 🧠 **Local LLMs** | Intent understanding |
| 🗣️ **faster-whisper** | Real-time Speech-to-Text |
| 🪟 **Windows APIs** | Deep system automation |

## 🚀 Getting Started

Prerequisites
- Windows 10 / 11

- Python 3.14

- Git

- PowerShell

- uv Package Manager

1. Clone & Setup

```
git clone https://github.com/SynapseCore-Labs/VoxOS
cd VoxOS/backend
```

2. Install uv (If you don't have it)

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Setup Environment
```
uv python pin 3.14
uv venv
```

Activate the environment:
```
.venv\Scripts\Activate.ps1
```

4. Install Dependencies
```
uv sync
```

5. Run Vox OS
```
uv run main.py
```

## 🔐 Security First

Vox OS is designed to interact directly with the user's computer. The AI will never blindly execute arbitrary commands. Potentially sensitive operations (Deleting files, transferring money, formatting) require explicit voice or keyboard confirmation.

```text
AI Decision
                      │
                      ▼
                 Safety Check
                      │
             ┌────────┴────────┐
             │                 │
           Safe            Sensitive
             │                 │
             ▼                 ▼
          Execute           Ask User
```

## 🗺️ Roadmap

- [x] Phase 1 — Foundation: Python backend, uv setup, threaded mic capture.

- [x] Phase 2 — Voice Engine: Wake-word detection (openwakeword), VAD, Speech-to-Text.

- [ ] Phase 3 — AI Brain: Intent recognition, tool routing, local memory.

- [ ] Phase 4 — Computer Control: Window management, browser Playwright automation.

- [ ] Phase 5 — Advanced Agent: Multi-step reasoning, shopping agents, OTP handling.

# 🤝 Contributing
Contributions, suggestions, and ideas are welcome!

1. Fork the repository

2. Create a feature branch: git checkout -b feature/your-feature

3. Commit your changes: git commit -m "feat: add your feature"

4. Push to the branch: git push origin feature/your-feature

5. Open a Pull Request 🚀

## 👨‍💻 Authors

### Built by **Sudhanshu Tiwari** & **Piyush Tiwari**

*AI · Automation · Software Engineering · Computer Systems*

**Piyush Tiwari**
[GitHub](https://github.com/Piyushtiwari919) · [LinkedIn](https://www.linkedin.com/in/piyush-tiwari919/)

**Sudhanshu Tiwari**
[GitHub](https://github.com/stiwari0223-ux) · [LinkedIn](https://www.linkedin.com/in/sudhanshu-tiwari-25337834b/)
