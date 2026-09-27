from datetime import date
from app.extensions import db
from app.models import Medicine, PHC, PatientFootfall, Forecast

def calculate_medicine_forecast(medicine: Medicine, phc: PHC = None, demand_multiplier: float = 1.0):
    """
    Calculate demand forecast, stockout timeline, and explainable risk for a medicine.
    Algorithm:
      Predicted Daily Demand = Baseline Daily Usage * Trend Factor * Footfall Factor * Seasonal Factor * demand_multiplier
    """
    baseline_usage = float(medicine.daily_usage) if medicine.daily_usage > 0 else 10.0

    # Trend factor based on category
    trend_factors = {
        'Analgesic': 1.23,      # Paracetamol surge
        'Antibiotic': 1.17,     # Antibiotics surge
        'Rehydration': 1.31,    # ORS surge
        'Vaccine': 1.12,        # Vaccine surge
        'Antidiabetic': 1.04,
        'Respiratory': 1.18,
        'IV Fluid': 1.09,
        'Antihistamine': 1.06,
        'Antimalarial': 1.15
    }
    cat_trend = trend_factors.get(medicine.category, 1.08)

    # Footfall factor (if PHC specified or network average)
    footfall_factor = 1.05
    if phc:
        if phc.patients_today > 250:
            footfall_factor = 1.20
        elif phc.patients_today > 180:
            footfall_factor = 1.10
        elif phc.patients_today < 140:
            footfall_factor = 0.95

    # Seasonal adjustment factor (demo factor: monsoon/post-monsoon respiratory & vector uptick)
    seasonal_factor = 1.06

    predicted_daily_rate = baseline_usage * cat_trend * footfall_factor * seasonal_factor * demand_multiplier
    predicted_7d = int(round(predicted_daily_rate * 7))
    predicted_30d = int(round(predicted_daily_rate * 30))

    current_stock = float(medicine.current_stock)
    if predicted_daily_rate > 0:
        stockout_days = round(current_stock / predicted_daily_rate, 1)
    else:
        stockout_days = 99.0

    # Severity Risk
    if stockout_days < 2.0 or current_stock < (medicine.minimum_stock * 0.4):
        risk_level = 'CRITICAL'
    elif stockout_days < 4.0 or current_stock < medicine.minimum_stock:
        risk_level = 'HIGH'
    elif stockout_days < 7.0 or current_stock < (medicine.minimum_stock * 1.5):
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'

    # Confidence calculation (between 88% and 96%)
    confidence = min(96, max(88, int(92 + (3 if stockout_days < 3 else -2))))

    # Explainable AI Reason (Innovation 9)
    reasons = []
    if current_stock < medicine.minimum_stock:
        reasons.append(f"Current stock ({int(current_stock)} {medicine.unit}) is below minimum safety threshold ({medicine.minimum_stock} {medicine.unit}).")
    else:
        reasons.append(f"Current buffer is {int(current_stock)} {medicine.unit}.")

    pct_change = int(round((cat_trend - 1.0) * 100))
    if pct_change > 0:
        reasons.append(f"Category demand trend shows a +{pct_change}% upward shift.")

    if demand_multiplier > 1.0:
        sim_pct = int(round((demand_multiplier - 1.0) * 100))
        reasons.append(f"What-If stress test active: +{sim_pct}% external demand surge applied.")

    reasons.append(f"Projected depletion rate is ~{int(round(predicted_daily_rate))} {medicine.unit}/day, giving {stockout_days} days of remaining runway.")

    if risk_level in ['CRITICAL', 'HIGH']:
        reasons.append("Cross-district resource redistribution review strongly recommended.")

    return {
        'medicine_id': medicine.id,
        'medicine_name': medicine.name,
        'category': medicine.category,
        'unit': medicine.unit,
        'current_stock': medicine.current_stock,
        'minimum_stock': medicine.minimum_stock,
        'daily_usage': medicine.daily_usage,
        'predicted_daily_rate': round(predicted_daily_rate, 1),
        'predicted_7d': predicted_7d,
        'predicted_30d': predicted_30d,
        'stockout_days': stockout_days,
        'risk_level': risk_level,
        'confidence': confidence,
        'reason': " ".join(reasons),
        'reasons_list': reasons
    }


def run_what_if_simulation(demand_increase_pct: float = 0.0):
    """
    Simulate what happens if demand increases by 0%, 10%, 20%, 30%, 50%.
    Does NOT modify actual database values.
    Returns:
      - simulated metrics
      - affected medicines
      - bed pressure changes
      - new alert count estimate
      - required transfers
    """
    multiplier = 1.0 + (float(demand_increase_pct) / 100.0)
    medicines = Medicine.query.all()
    phcs = PHC.query.all()

    simulated_results = []
    critical_count = 0
    high_count = 0
    total_shortage_units = 0

    for med in medicines:
        sim_data = calculate_medicine_forecast(med, demand_multiplier=multiplier)
        simulated_results.append(sim_data)
        if sim_data['risk_level'] == 'CRITICAL':
            critical_count += 1
        elif sim_data['risk_level'] == 'HIGH':
            high_count += 1
        
        # Calculate shortage deficit if stockout is under 7 days
        if sim_data['stockout_days'] < 7.0:
            needed = max(0, sim_data['predicted_7d'] - med.current_stock)
            total_shortage_units += needed

    # Bed pressure simulation
    # Baseline beds occupied: ~84.2%
    base_occupancy = 84.2
    simulated_bed_occupancy = min(98.5, round(base_occupancy + (demand_increase_pct * 0.28), 1))
    
    # Alert count estimate
    base_alerts = 126
    simulated_alert_count = int(round(base_alerts + (demand_increase_pct * 1.8)))

    # Critical PHCs estimate
    base_crit_phcs = 34
    simulated_crit_phcs = int(round(base_crit_phcs + (demand_increase_pct * 0.45)))

    # Key highlight medicines
    key_med_names = ["Paracetamol 500mg", "Amoxicillin 500mg", "ORS Sachets 20.5g", "Covishield Vaccine"]
    key_highlights = [s for s in simulated_results if s['medicine_name'] in key_med_names]

    return {
        'demand_increase_pct': demand_increase_pct,
        'multiplier': multiplier,
        'simulated_bed_occupancy': simulated_bed_occupancy,
        'simulated_alert_count': simulated_alert_count,
        'simulated_crit_phcs': simulated_crit_phcs,
        'critical_medicines_count': critical_count,
        'high_risk_medicines_count': high_count,
        'total_shortage_units': total_shortage_units,
        'key_highlights': key_highlights,
        'all_medicines': simulated_results
    }
