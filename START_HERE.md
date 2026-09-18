# 🚀 QUICK START - Read This First!

**You are looking at the UPI Fraud Stress Lab project.**

This is a **75% complete** research prototype for your intermediate review.

---

## ⚡ FASTEST PATH TO WORKING DEMO

### 1️⃣ Verify Transfer (2 min)
```bash
cd upi-fraud-stress-lab
python3 verify_setup.py
```

### 2️⃣ Setup Environment (10 min)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ **CRITICAL: Train Model** (20-30 min)
```bash
python src/detectors/train.py
```
☝️ **This is the ONLY blocking step!**

### 4️⃣ Run Demo (instant)
```bash
python demo.py
```

### 5️⃣ Run Experiments (30 min)
```bash
python run_experiment.py --scenario S4
python run_experiment.py --all
```

---

## 📋 What You Have

✅ **24 Python source files**  
✅ **98 MB fraud dataset** (284,807 transactions)  
✅ **Complete UPI simulator**  
✅ **Adaptive attacker** that responds to detector  
✅ **Campaign-level metrics**  
✅ **S1-S4 experiment framework**  

⚠️ **Missing**: Trained model (do Step 3 above)

---

## 📖 Documentation

- **START HERE**: `TRANSFER_README.md` (complete guide)
- **Quick status**: `STATUS.md`
- **Detailed handoff**: `HANDOFF.md`
- **Dataset info**: `DATASET.md`

---

## 🎯 What The Demo Shows

```
Unknown Fraud Campaign
         ↓
Adaptive Attacker tries ₹50,000
         ↓
Detector: BLOCK
         ↓
Attacker: Reduces to ₹5,000
         ↓
Detector: ALLOW
         ↓
Attacker: Continues adapting...
         ↓
Campaign completes with metrics
```

This demonstrates: **Can detectors handle attackers who adapt to their responses?**

---

## ⏱️ Time Needed

- Setup: 10 min
- **Model training: 20-30 min** ← Most important
- Demo completion: 20 min
- Run experiments: 30 min
- Visualizations: 30-45 min

**Total to 80% prototype: ~2.5 hours**

---

## 🆘 Problems?

### Dataset missing?
```bash
ls -lh data/raw/creditcard.csv  # Should be ~98 MB
```

### Training fails?
- Check you have 4GB+ RAM
- Edit `src/detectors/train.py` to reduce dataset if needed

### Demo fails?
```bash
# Ensure model exists
ls -lh models/baseline_xgboost.pkl
```

---

## 📞 What's Next

After model training:
1. Complete `demo.py` (skeleton ready)
2. Complete `run_experiment.py` (framework ready)
3. Run S1-S4 scenarios
4. Create basic visualizations

**You'll have an 80% working prototype ready for intermediate review!**

---

**Quick reference**: Read `TRANSFER_README.md` for complete instructions.
