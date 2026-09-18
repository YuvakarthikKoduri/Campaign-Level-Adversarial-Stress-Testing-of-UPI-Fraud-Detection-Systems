# 💾 TRANSFER OPTIONS - Low Disk Space

## Your Situation
- **Disk**: 98% full (only 537MB free)
- **Project**: 1.3GB
- **Archive**: 549MB (too big to create)

---

## ✅ BEST OPTIONS (No Archive Needed!)

### Option 1: Direct Copy via USB/External Drive ⭐ RECOMMENDED

```bash
# On current laptop:
# 1. Plug in USB drive (mounted at /media/usb or similar)
# 2. Copy project directly (no compression)

cp -r /home/yuvakarthik-koduri/upi-fraud-stress-lab /media/usb/

# On target laptop:
# 1. Plug in same USB drive
# 2. Copy to home directory

cp -r /media/usb/upi-fraud-stress-lab ~/
cd ~/upi-fraud-stress-lab
python3 verify_setup.py
```

**Advantages:**
- ✅ No archive needed (saves 549MB)
- ✅ No disk space issues
- ✅ Fastest method
- ✅ Works with any USB drive

---

### Option 2: Network Transfer (SCP/RSYNC)

If both laptops are on same network:

```bash
# On target laptop, get IP address:
ip addr show | grep "inet "

# On current laptop, transfer directly:
rsync -avh --progress /home/yuvakarthik-koduri/upi-fraud-stress-lab \
    username@TARGET_IP:~/

# No archive created, direct transfer!
```

**Advantages:**
- ✅ No archive file
- ✅ No disk space needed
- ✅ Can resume if interrupted

---

### Option 3: Cloud Transfer (GitHub/GitLab)

```bash
cd /home/yuvakarthik-koduri/upi-fraud-stress-lab

# Add dataset to .gitignore (already done)
echo "data/raw/creditcard.csv" >> .gitignore

# Commit and push (without dataset)
git add -A
git commit -m "UPI Fraud Stress Lab - code only"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin master

# On target laptop:
git clone YOUR_GITHUB_REPO_URL
cd upi-fraud-stress-lab

# Download dataset separately (98MB)
# See DATASET.md for download instructions
```

**Advantages:**
- ✅ Version controlled
- ✅ Small transfer (<200MB without dataset)
- ✅ Can re-download dataset on other laptop

---

### Option 4: Split Archive (If You Must Use Archive)

```bash
# Create smaller pieces that fit
cd /home/yuvakarthik-koduri

# Exclude dataset temporarily
tar --exclude='upi-fraud-stress-lab/data/raw/creditcard.csv' \
    -czf code-only.tar.gz upi-fraud-stress-lab/

# code-only.tar.gz will be ~150MB (fits in 537MB!)
# Transfer dataset separately later
```

---

## 🎯 MY RECOMMENDATION

**Use Option 1: USB Drive Direct Copy**

Why?
- ✅ Simplest (just plug and copy)
- ✅ No compression time
- ✅ No disk space issues
- ✅ Keeps everything intact
- ✅ Works even if laptops can't connect to network

---

## 📦 What You're Transferring

### Project Structure (1.3GB total):
```
upi-fraud-stress-lab/
├── data/raw/creditcard.csv     98 MB  ← The big file
├── venv/                       1.1 GB ← Don't need to transfer!
├── src/                        ~5 MB  ← Your code
├── documentation/              ~2 MB
└── other files                 ~100 MB
```

---

## 💡 EVEN BETTER: Skip venv Transfer!

You don't need to transfer `venv/` - recreate it on target laptop!

```bash
# On current laptop - copy without venv
rsync -avh --progress --exclude='venv' \
    /home/yuvakarthik-koduri/upi-fraud-stress-lab \
    /media/usb/

# Now only ~200MB to transfer!
# (98MB dataset + code + docs)

# On target laptop - recreate venv
cd ~/upi-fraud-stress-lab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Transfer size: 200MB instead of 1.3GB!**

---

## 🚀 QUICK START - USB Method

### Current Laptop:
```bash
# 1. Plug in USB drive
lsblk  # Find USB drive (e.g., /media/usb)

# 2. Copy project (skip venv to save space)
rsync -avh --progress --exclude='venv' --exclude='.git' \
    /home/yuvakarthik-koduri/upi-fraud-stress-lab \
    /media/usb/

# Takes 2-3 minutes for ~200MB
```

### Target Laptop:
```bash
# 1. Plug in USB drive
# 2. Copy to home
cp -r /media/usb/upi-fraud-stress-lab ~/

# 3. Setup
cd ~/upi-fraud-stress-lab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Verify
python3 verify_setup.py

# 5. Train!
python train_lightweight.py
```

---

## 📊 Transfer Size Comparison

| Method | Size | Time | Disk Space Needed |
|--------|------|------|-------------------|
| Full archive | 549 MB | N/A | ❌ 549 MB (too much!) |
| Skip venv | 200 MB | 2-3 min | ✅ 0 MB |
| Code only (no dataset) | 100 MB | 1 min | ✅ 0 MB |
| USB direct copy | 200 MB | 2-3 min | ✅ 0 MB |

---

## ✅ BEST APPROACH FOR YOU

Since you have **low disk space on current laptop**:

**Use USB drive + skip venv:**
- Transfer: ~200MB
- No archive creation
- No extra disk space needed
- 2-3 minutes
- Recreate venv on target laptop

---

## 🎯 NEXT STEPS

Tell me which method you prefer:
1. USB drive direct copy (recommended)
2. Network transfer (if both laptops on same network)
3. GitHub/GitLab (if you have a repo)
4. Something else?

I'll give you the exact commands for your chosen method!
