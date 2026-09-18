#!/bin/bash
# Quick Transfer Script - Low Disk Space Solution
# Copies project to USB without creating archive

echo "════════════════════════════════════════════════════════"
echo "UPI FRAUD STRESS LAB - USB TRANSFER (No Archive Needed)"
echo "════════════════════════════════════════════════════════"
echo ""

# Check if USB path is provided
if [ -z "$1" ]; then
    echo "Usage: ./transfer_to_usb.sh /path/to/usb"
    echo ""
    echo "Example:"
    echo "  ./transfer_to_usb.sh /media/usb"
    echo "  ./transfer_to_usb.sh /mnt/usbdrive"
    echo ""
    echo "First, plug in your USB drive, then find its mount point:"
    echo "  lsblk"
    echo "  df -h | grep media"
    exit 1
fi

USB_PATH="$1"
PROJECT_PATH="/home/yuvakarthik-koduri/upi-fraud-stress-lab"

# Check if USB path exists
if [ ! -d "$USB_PATH" ]; then
    echo "❌ Error: USB path $USB_PATH does not exist"
    echo ""
    echo "Available drives:"
    df -h | grep -E "media|mnt"
    exit 1
fi

# Check free space on USB
FREE_SPACE=$(df -m "$USB_PATH" | awk 'NR==2 {print $4}')
echo "USB drive free space: ${FREE_SPACE}MB"

if [ "$FREE_SPACE" -lt 300 ]; then
    echo "⚠️  Warning: USB has less than 300MB free"
    echo "Need ~200MB to transfer (excluding venv)"
fi

echo ""
echo "Copying project to USB (excluding venv and git)..."
echo "This will take 2-3 minutes for ~200MB..."
echo ""

# Copy with progress, excluding venv and .git
rsync -avh --progress \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "$PROJECT_PATH" \
    "$USB_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Project copied to USB"
    echo ""
    echo "Location: $USB_PATH/upi-fraud-stress-lab"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "NEXT STEPS ON TARGET LAPTOP:"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "1. Plug in this USB drive"
    echo ""
    echo "2. Copy to home directory:"
    echo "   cp -r /media/usb/upi-fraud-stress-lab ~/"
    echo ""
    echo "3. Setup environment:"
    echo "   cd ~/upi-fraud-stress-lab"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "4. Verify transfer:"
    echo "   python3 verify_setup.py"
    echo ""
    echo "5. Train model (5-7 minutes on your 12GB laptop):"
    echo "   python train_lightweight.py"
    echo ""
    echo "6. Run demo:"
    echo "   python demo.py"
    echo ""
    echo "═══════════════════════════════════════════════════════"
else
    echo ""
    echo "❌ Copy failed. Check USB connection and try again."
    exit 1
fi
