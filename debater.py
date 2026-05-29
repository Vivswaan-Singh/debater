import re
import subprocess
import sys
import uuid
import argparse
import os

CLAUDE_BIN = os.path.expanduser("~/.local/bin/claude")
CODEX_BIN = os.path.expanduser("~/.nvm/versions/node/v24.13.0/bin/codex")
CAVEMAN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caveman.md")

def validate_sessions(claude_name, codex_id):
    """Validates sessions by sending a silent system ping."""
    ping_prompt = "[system check: reply with exactly OK]"
    
    print("🔍 Checking Claude session...")
    # Use the ping prompt here
    claude_result = call_claude(ping_prompt, session_name=claude_name, is_first_call=False)
    
    if claude_result is None or "OK" not in claude_result.strip().upper():
        print(f"❌ Error: Claude session '{claude_name}' failed validation.")
        return False
    
    print(f"✅ Claude session '{claude_name}' verified.")

    print("🔍 Checking Codex session...")
    codex_result, _ = call_codex(ping_prompt, session_id=codex_id)
    
    if codex_result is None or "OK" not in codex_result.strip().upper():
        print(f"❌ Error: Codex session '{codex_id}' failed validation.")
        return False

    return True

def call_claude(prompt, session_name, is_first_call=False):
    """Calls Claude using named sessions for persistence."""
    cmd = [CLAUDE_BIN, "--print"]
    
    if is_first_call:
        # Create the session with a specific name
        cmd.extend(["-n", session_name])
    else:
        # Resume the session we named earlier
        cmd.extend(["--resume", session_name])
        
    cmd.append(prompt)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = e.stdout if e.stdout else e.stderr
        print(f"\n❌ Claude Error: {error_msg.strip()}")
        return None

def call_codex(prompt, session_id=None):
    """Calls Codex and manages session persistence."""
    cmd = [CODEX_BIN, "exec"]
    if session_id:
        cmd.extend(["resume", session_id])
    cmd.append(prompt)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        # Codex conveniently dumps the session ID in stderr on every run
        if session_id is None:
            match = re.search(r'session id:\s+([a-f0-9-]{36})', result.stderr)
            session_id = match.group(1) if match else None
            
        return output, session_id
    except Exception as e:
        return None, None

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Debater")
    parser.add_argument("--resume", nargs=2, metavar=('CLAUDE_NAME', 'CODEX_ID'), help="Resume previous sessions using Claude name and Codex UUID")
    args = parser.parse_args()

    # --- Initialization Logic ---
    if args.resume:
        claude_session, codex_session_id = args.resume
        print(f"🔍 Validating resume targets...")
        if not validate_sessions(claude_session, codex_session_id):
            sys.exit(1)
        print("✅ Sessions validated. Resuming chat...")
        first_interaction = False # We are resuming, so it's never the "first" call
    else:
        print("✨ Multi-Agent Chatbot: Claude 4.6 + Codex 5.5")
        print("🔄 Initializing FRESH session context...")
        with open(CAVEMAN_PATH, "r") as f:
            caveman_rules = f.read()
        unique_id = str(uuid.uuid4())[:16]
        claude_session = f"debater-{unique_id}"
        first_interaction = True
        call_claude(caveman_rules, session_name=claude_session, is_first_call=first_interaction)
        codex_session_id = None
        _claude_v1, codex_session_id = call_codex(caveman_rules, session_id=codex_session_id)
        first_interaction = False

    try:
        while True:
            user_input = input("❯ ").strip()

            if user_input.lower() in ["/exit", "exit", "quit"]:
                print("Claude session name: ", claude_session)
                print("Codex session id: ", codex_session_id)
                print("👋 Closing AI sessions. Goodbye!")
                break
            if not user_input:
                continue

            # --- ROUND 1: CLAUDE DRAFT ---
            print("⏳ [1/3] Claude is drafting...", end="\r")
            claude_v1 = call_claude(user_input, session_name=claude_session, is_first_call=first_interaction)
            first_interaction = False

            if claude_v1 is None:
                print("\n🚨 Claude failed. Shutting down.")
                sys.exit(1)

            # --- ROUND 2: CODEX REVIEW ---
            print("⏳ [2/3] Codex is reviewing...", end="\r")
            codex_prompt = (
                f"SYSTEM MISSION: Review the following draft for the user request: '{user_input}'\n"
                f"DRAFT TO REVIEW: {claude_v1}\n"
                "Review this. Identify bugs, performance issues, or edge cases. Be technical and brief."
            )
            codex_out, codex_session_id = call_codex(codex_prompt, session_id=codex_session_id)

            # --- ROUND 3: FINAL SYNTHESIS ---
            if codex_out:
                print("⏳ [3/3] Finalizing result...  ", end="\r")
                final_prompt = (
                    f"SYSTEM NOTICE: A peer reviewer (Codex) provided the following critique. "
                    "Incorporate valid technical fixes. Do not comment on the reviewer's identity.\n\n"
                    f"REVIEW: {codex_out}\n\n"
                    "Output ONLY the final production-ready answer for the user."
                )
                final_output = call_claude(final_prompt, session_name=claude_session, is_first_call=first_interaction)
            else:
                final_output = claude_v1

            # Final Display
            print(" " * 50, end="\r")
            print("\n" + "—" * 60)
            print(final_output)
            print("—" * 60 + "\n")
            
            # Uncomment below to verify IDs are successfully grabbed

    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Exit.")
        print("Claude session name: ", claude_session)
        print("Codex session id: ", codex_session_id)
        sys.exit(0)

if __name__ == "__main__":
    main()