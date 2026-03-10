# Quick Start Guide

Get your first autonomous coding session running in 5 minutes.

## Prerequisites

Before starting, ensure you have:

- Python 3.11 or higher
- Node.js 18 or higher
- ANTHROPIC_API_KEY environment variable set

```bash
# Check Python version
python --version  # Should be 3.11+

# Check Node.js version
node --version    # Should be 18+

# Verify API key
echo $ANTHROPIC_API_KEY  # Should show your key
```

## Step 1: Install Autonomous CLI

```bash
# Install from PyPI (recommended)
pip install autonomous-cli

# Or install from source
git clone https://github.com/claude-code-skills-factory/autonomous-cli
cd autonomous-cli
pip install -e .

# Verify installation
acli --version
```

## Step 2: Initialize Your First Project

```bash
# Create a new project
acli init my_todo_app

# Navigate into project directory
cd my_todo_app
```

This creates:
- `my_todo_app/` directory
- `app_spec.txt` file (you'll edit this next)

## Step 3: Write Your Specification

Edit `app_spec.txt` with your application requirements:

```text
Build a todo application with the following features:

Features:
- Add new tasks with title and description
- Mark tasks as complete with checkbox
- Delete tasks with confirmation dialog
- Filter tasks: All, Active, Completed
- Persistent storage using localStorage
- Task count display

Technical Requirements:
- React 18 with TypeScript
- Tailwind CSS for styling
- No external state management libraries
- Mobile-responsive design
- Accessibility (ARIA labels)

UI Design:
- Clean, minimal interface
- Input field at top for new tasks
- Task list below with checkboxes
- Filter buttons at bottom
- Color: Blue for active, Gray for completed
```

**Tips for Writing Good Specs:**

✅ **DO**:
- Be specific about features
- Mention technical stack
- Include UI/UX requirements
- Specify data storage

❌ **DON'T**:
- Be vague ("make it nice")
- Omit technical details
- Skip UI descriptions

## Step 4: Run the Autonomous Agent

```bash
# Start autonomous coding
acli run
```

**What happens now:**

1. **Session 1 (Initializer)** - ~5-10 minutes:
   - Reads your `app_spec.txt`
   - Generates `feature_list.json` with ~200 test cases
   - Creates project structure (React + TypeScript)
   - Generates `init.sh` setup script
   - Runs `npm install`

2. **Sessions 2+** - Variable duration:
   - Each session implements ONE feature
   - Tests feature with browser automation
   - Marks feature as passing in `feature_list.json`
   - Commits changes to git
   - Continues until all features complete

## Step 5: Monitor Progress

The cyberpunk Agent Monitor TUI shows real-time progress with full agent visibility:

```
┌──────────────────────────────────────────────────────────────┐
│  ⟁ ACLI AGENT MONITOR │ ● RUNNING │ S#2 [coding] │ 05:30  │
├────────────────────┬─────────────────────────────────────────┤
│  AGENT HIERARCHY   │ LOGS │ F1:All F2:Tools F3:Errors F4:Text│
│  ◆ ORCHESTRATOR    │ 14:32:15 TXT Creating structure...      │
│  ├─ ✓ S#1 [init]  │ 14:32:16 TOL ▶ Bash npm init -y         │
│  ╰─ ◆ S#2 [code]  │ 14:32:17 TOL ✓ Bash 150ms OK            │
│    ⚡ Write        │ 14:32:18 TOL ▶ Write src/App.jsx         │
│────────────────────├─────────────────────────────────────────┤
│  ◆ CODING          │ PROGRESS ████████░░░░░░ 10/200 5.0%    │
│  Status: running   │ Sessions: 2 │ Tools: 15 │ Errors: 0    │
│  Duration: 5m30s   │ RECENT TOOLS                             │
│  Tools: 15         │   ✓ Write 88ms │ → Read 23ms...         │
├────────────────────┴─────────────────────────────────────────┤
│ q Quit  p Pause/Resume  s Stop  ↑↓ Navigate  Enter Detail   │
└──────────────────────────────────────────────────────────────┘
```

Use j/k keys to navigate agents, Enter to drill into details, F1-F4 to filter logs.

**Or launch the dedicated monitor in a separate terminal:**

```bash
acli monitor
```

**Or check status manually:**

```bash
# In another terminal
cd my_todo_app
acli status

# Output:
# Progress: 15/200 (7.5%)
# Completed: 15 features
# Remaining: 185 features
```

## Step 6: View Your Application

Once a few features are implemented:

```bash
# Start the development server
npm run dev

# Open in browser
# Default: http://localhost:3000
```

You can view progress as features are implemented in real-time!

## Common Workflows

### Resume After Interruption

The agent saves progress automatically. Just run again:

```bash
acli run
# Continues from where it left off
```

### Speed Up Development

Reduce feature count for faster iteration:

```bash
# Edit app_spec.txt to be more concise
# Or modify prompts/templates/initializer.md
# Change "~200 features" to "~50 features"
```

### Watch Detailed Logs

Enable verbose logging:

```bash
acli run --verbose
```

### Run Without Dashboard

For CI/CD or background execution:

```bash
acli run --no-dashboard --headless
```

### Limit Sessions

Test with limited iterations:

```bash
acli run --max-iterations 3
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Or add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

### "npm: command not found"

Install Node.js:

```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Verify
node --version
```

### Agent Stuck or Making Mistakes

1. Check `feature_list.json` for current progress
2. Review recent commits: `git log --oneline`
3. Stop with Ctrl+C and restart
4. Edit `app_spec.txt` to be more specific

### Browser Tests Failing

Install MCP server:

```bash
# Puppeteer (recommended)
npm install -g puppeteer-mcp-server

# Or Playwright
npm install -g @executeautomation/playwright-mcp-server
```

### Permission Errors

The agent only has access to:
- Project directory
- 16 allowed commands
- Development processes

If you see "Command blocked", it's working as designed for security.

## Next Steps

### Learn More

- [Architecture](ARCHITECTURE.md) - System design
- [API Reference](API.md) - Python API
- [Configuration](../README.md#configuration) - Customize behavior

### Example Projects

Try these sample specs:

**Blog Platform:**
```text
Build a blog platform with:
- Create, edit, delete posts
- Markdown support
- Categories and tags
- Search functionality
- Responsive design
Stack: React + TypeScript + Tailwind
```

**Weather Dashboard:**
```text
Build a weather dashboard with:
- Current weather display
- 5-day forecast
- Location search
- Temperature unit toggle (C/F)
- Weather icons
Stack: React + TypeScript + OpenWeather API
```

### Configuration

Customize default behavior:

```bash
# Set default model
acli config model claude-opus-4

# Set max iterations
acli config max_iterations 10

# Use Playwright instead of Puppeteer
acli config browser_provider playwright

# List all settings
acli config --list
```

## Best Practices

### Writing Specs

1. **Start Simple**: Begin with core features
2. **Be Specific**: Include UI details and interactions
3. **Tech Stack**: Always specify frameworks and libraries
4. **Test Cases**: Mention important edge cases

### Monitoring Progress

1. **Check Regularly**: Use `acli status`
2. **Review Commits**: `git log` shows what was implemented
3. **Test Locally**: `npm run dev` to verify features

### Debugging

1. **Feature List**: Check `feature_list.json` for current state
2. **Logs**: Enable `--verbose` for details
3. **Browser**: Watch browser automation with `--no-headless`

## Tips for Success

**DO**:
- ✅ Write detailed specifications
- ✅ Specify exact tech stack
- ✅ Include UI/UX requirements
- ✅ Monitor progress regularly
- ✅ Let agent complete features fully

**DON'T**:
- ❌ Interrupt mid-session frequently
- ❌ Edit files the agent is working on
- ❌ Change spec while running
- ❌ Expect perfection in first iteration

## Getting Help

- **Issues**: https://github.com/claude-code-skills-factory/autonomous-cli/issues
- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder (coming soon)

## What's Next?

After completing your first project:

1. Try a more complex application
2. Experiment with different tech stacks
3. Contribute improvements (see CONTRIBUTING.md)
4. Share your results!

Happy autonomous coding! 🚀
