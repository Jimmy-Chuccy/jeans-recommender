# Guide: Installing Dependencies (Step 2)

## Where to Run pip install

Run the `pip install` command in **Terminal**, in your project directory.

## Step-by-Step Instructions

### 1. Open Terminal

- Press `Cmd + Space` to open Spotlight
- Type "Terminal" and press Enter
- Or go to: Applications → Utilities → Terminal

### 2. Navigate to Your Project Directory

Type this command and press Enter:

```bash
cd /Users/jimmychu/Desktop/N\&F_SideProject
```

**Verify you're in the right place:**
```bash
pwd
```

You should see: `/Users/jimmychu/Desktop/N&F_SideProject`

**Also verify you can see the requirements.txt file:**
```bash
ls requirements.txt
```

You should see: `requirements.txt` listed

### 3. Install Dependencies

You have two options:

#### Option A: Install Just Flask and Twilio (Faster)

```bash
pip install flask twilio
```

#### Option B: Install All Dependencies (Recommended)

```bash
pip install -r requirements.txt
```

This installs Flask, Twilio, and all other project dependencies.

### 4. Verify Installation

Check that Flask and Twilio are installed:

```bash
python -c "import flask; import twilio; print('✅ Flask and Twilio installed successfully!')"
```

If you see the success message, you're good to go!

## What You'll See

When you run `pip install`, you'll see output like:

```
Collecting flask
  Downloading flask-3.0.0-py3-none-any.whl (101 kB)
Collecting twilio
  Downloading twilio-8.10.0-py3-none-any.whl (1.2 MB)
...
Installing collected packages: ...
Successfully installed flask-3.0.0 twilio-8.10.0 ...
```

This is normal! It's downloading and installing the packages.

## Troubleshooting

### Issue: "command not found: pip"

Try:
```bash
pip3 install flask twilio
```

Or:
```bash
python3 -m pip install flask twilio
```

### Issue: "Permission denied"

If you see permission errors, you might need to use:
```bash
pip install --user flask twilio
```

Or if you're using a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Then install
pip install flask twilio
```

### Issue: "No module named pip"

Install pip first:
```bash
python3 -m ensurepip --upgrade
```

Then try installing again.

## Quick Reference: Complete Command Sequence

Copy and paste these commands one by one:

```bash
# 1. Navigate to project
cd /Users/jimmychu/Desktop/N\&F_SideProject

# 2. Verify you're in the right place
pwd
ls requirements.txt

# 3. Install dependencies
pip install flask twilio

# 4. Verify installation
python -c "import flask; import twilio; print('✅ Success!')"
```

## Using a Virtual Environment (Optional but Recommended)

If you want to keep dependencies isolated:

```bash
# 1. Navigate to project
cd /Users/jimmychu/Desktop/N\&F_SideProject

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install dependencies
pip install flask twilio

# 5. When done, you can deactivate with:
# deactivate
```

**Note:** If you use a virtual environment, you'll need to activate it (`source venv/bin/activate`) every time you want to run the server.

## Next Steps

After installing:
1. ✅ Dependencies installed
2. ✅ Create `.env` file (Step 1)
3. ✅ Join WhatsApp Sandbox (Step 3)
4. ✅ Set up ngrok (Step 4)
5. ✅ Configure webhook (Step 5)
6. ✅ Test and run (Steps 6-7)

