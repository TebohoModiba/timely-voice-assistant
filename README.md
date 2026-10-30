# Timely: a voice assistant for time management

Timely is a voice AI assistant you can talk to. It sets reminders, tracks
the habits you mention, and keeps a daily log of what you did, all by voice.

Built with the Kiro IDE, Strands Bidi Agents and Amazon Nova Sonic on
Amazon Bedrock, as a follow-up to the AWS Community Day Johannesburg voice
agent tutorial.

## What it does

| You say | What happens |
|---|---|
| "Remind me to call the bank tomorrow at 9" | Saves a reminder |
| "What reminders do I have?" | Reads your pending reminders |
| "I finished the bank call" | Marks the reminder done |
| "I did a 20 minute walk today" | Logs the habit |
| "How are my habits this week?" | Summarises habit frequency |
| "Log that I finished my assignment draft" | Adds an entry to today's log |
| "What did I do today?" | Reads back today's log |

When a reminder comes due, it is printed in the terminal and the agent is
prompted to announce it.

## How it works

- **Amazon Nova Sonic** (via Amazon Bedrock) is the speech-to-speech model.
- **Strands Bidi Agents** handles the two-way audio stream and calls Python
  functions ("tools") when you ask for something.
- Eight small tools read and write a local `tracker_data.json` file.
- A background task checks every 20 seconds for reminders that are due.

## Prerequisites

- Python **3.12** (3.11 also works; 3.14 does not, because PyAudio has no
  prebuilt package for it yet)
- An AWS account with an IAM user that can call Amazon Bedrock
- Amazon Nova Sonic available in your region (this project uses
  `eu-north-1`, Stockholm)
- A microphone and speakers; headphones give the best results

## Setup

1. Clone the repo and enter the folder:

   ```powershell
   git clone https://github.com/TebohoModiba/timely-voice-assistant.git
   cd timely-voice-assistant
   ```

2. Create and activate a virtual environment (Windows PowerShell):

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS or Linux: `python3 -m venv .venv` then
   `source .venv/bin/activate`.

3. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Add your AWS credentials in `~/.aws/credentials`
   (`C:\Users\YOU\.aws\credentials` on Windows):

   ```
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY_ID
   aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
   ```

   and `~/.aws/config`:

   ```
   [default]
   region = eu-north-1
   output = json
   ```

   Never commit these files.

## Run it

```powershell
python voice_agent.py
```

Wait for "Timely is listening", then start talking. Press **Ctrl+C** to end
the session.

## Make it your own

- **Rename the agent:** change `AGENT_NAME` at the top of `voice_agent.py`.
- **Change the voice:** edit the `voice=` argument (for example `tiffany` or
  `matthew`).
- **Change the personality:** edit `SYSTEM_PROMPT`.
- **Change the region:** edit `region=` and make sure Nova Sonic is
  available there.

## Known limitations

- Reminders only fire while the program is running.
- Nova Sonic does not support South African languages such as isiZulu or
  Afrikaans, so use English.
- Data is stored in a local JSON file, not a database.

## Credits

Based on the AWS Community Day Johannesburg voice agent tutorial by
[veliswaan](https://github.com/veliswaan/awscommunitydayjozi-voice-agent-tutorial).