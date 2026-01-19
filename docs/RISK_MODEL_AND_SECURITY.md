# Risk Model & Security Specification

> **Technical Deep Dive**  
> This document details the exact algorithms, weights, and parameters used by SafeTravels to calculate risk scores and evaluate safe stops.

---

## 1. Cargo Theft Risk Model (0-10 Scale)

The risk score is calculated using a **15-factor weighted multiplication formula**:

$$
\text{Score} = \text{Base} \times \prod (\text{Weights})
$$

### 1.1 Temporal Factors
Time is a critical risk vector. Most thefts occur when freight is at rest (weekend/night).

| Factor | Value | Weight (Multiplier) | Reasoning |
|--------|-------|---------------------|-----------|
| **Time of Day** | **Night (10 PM - 5 AM)** | **1.5x** | Peak theft window; reduced witnesses/visibility. |
| | Evening (5 PM - 10 PM) | 1.25x | Transition period. |
| | Day (5 AM - 5 PM) | 1.0x | Highest activity levels (safest). |
| **Day of Week** | **Saturday** | **1.2x** | Long dwell times; reduced facility staffing. |
| | Friday | 1.15x | Weekend staging beginning. |
| | Sunday | 1.1x | End of weekend dwell. |
| | Mon-Wed | 1.0x | Standard movement. |
| **Season** | **Black Friday Week** | **1.5x** | Highest value freight volume of the year. |
| | Holiday Peak (Dec) | 1.4x | Gift shipments; chaotic logistics. |
| | Back to School (Aug) | 1.2x | Electronics surge. |

### 1.2 Cargo & Value Factors
Targeted theft focuses on high-resale value goods.

| Factor | Value | Weight | Notes |
|--------|-------|--------|-------|
| **Commodity** | **Electronics** | **1.5x** | Top target: TVs, phones, computers. |
| | Pharmaceuticals | 1.45x | High street value; organized crime. |
| | Alcohol/Tobacco | 1.3x | Easy liquidation. |
| | Auto Parts | 1.25x | Specific demand. |
| | Food/Beverage | 1.0x | Perishable (lower risk). |
| **Cargo Value** | **$1M+ (Ultra High)** | **1.6x** | Triggers targeted surveillance. |
| | $500k - $1M | 1.4x | High value target. |
| | $250k - $500k | 1.25x | Elevated risk. |

### 1.3 Location Factors
Where the truck stops matters most.

| Factor | Value | Weight | Notes |
|--------|-------|--------|-------|
| **Location Type** | **Random Roadside** | **1.6x** | No security; completely vulnerable. |
| | Unsecured Lot | 1.5x | Dark; unmonitored. |
| | Rest Area | 1.3x | Public; minimal oversight. |
| | **Secured Truck Stop** | **0.8x** | Gates, guards, cameras (SAFE). |
| **State Hotspot** | **California (CA)** | **1.35x** | #1 Theft state (Ports/LA). |
| | Texas (TX) | 1.3x | #2 Theft state. |
| | Florida (FL) | 1.25x | #3 Theft state. |

### 1.4 Environmental Factors
Real-time conditions that create vulnerability.

| Factor | Value | Weight | Reasoning |
|--------|-------|--------|-----------|
| **Event** | **Civil Unrest / Riot** | **2.0x** | Chaos enables opportunistic looting. |
| | Major Protest | 1.6x | Police resources diverted. |
| **Traffic** | **Standstill** | **1.5x** | Truck is a sitting duck. |
| | Severe | 1.4x | Extended exposure time. |
| **Weather** | **Severe Storm** | **1.35x** | Low visibility; slow emergency response. |
| | Fog | 1.2x | Cover for theft activity. |

### 1.5 Risk Levels
Final score is clamped between 1.0 and 10.0.

- **CRITICAL (7.0 - 10.0):** Immediate action required. Reroute or secure parking ONLY.
- **HIGH (5.0 - 7.0):** Heightened awareness. No roadside stops.
- **MODERATE (3.0 - 5.0):** Standard precautions.
- **LOW (1.0 - 3.0):** Routine operation.

---

## 2. Safe Stop Security Scoring (0-100 Points)

We rate truck stops on a 100-point scale based on **physical security** and **operational features**.

### 2.1 Scoring Breakdown

#### Tier 1: Physical Security (Max 45 pts)
*Most critical for preventing theft.*
- **Gated Parking:** +18 pts (Controls access)
- **24/7 Security Guards:** +15 pts (Active deterrence)
- **Monitored CCTV:** +8 pts (Video evidence/monitoring)
- **Well-Lit:** +4 pts (Visibility)

#### Tier 2: Location & History (Max 35 pts)
*Contextual safety.*
- **No Theft History:** +18 pts (Proven safety record)
- **Low Risk State:** +8 pts
- **Highway Access:** +6 pts (Rapid exit capability)
- **Nearby Police:** +3 pts (<5 miles)

#### Tier 3: Operational (Max 20 pts)
*Management quality.*
- **Major Brand:** +8 pts (Pilot/Love's/TA have corporate safety policies)
- **Staffed 24/7:** +7 pts (Witnesses always present)
- **High Driver Rating:** +5 pts

#### Penalties (Negative Points)
- **Single Exit:** -8 pts (Entrapment risk)
- **Poor Lighting:** -6 pts
- **Isolated:** -5 pts (No help nearby)
- **High Crime State (CA/TX/FL):** -5 pts

### 2.2 Security Tiers
- **🟢 LEVEL 1 (85-100): Premium Security.** Must have gates, guards, and cameras.
- **🟡 LEVEL 2 (65-84): Secure.** Good lighting, cameras, major brand presence.
- **🟠 LEVEL 3 (45-64): Basic.** Acceptable for short stops; caution overnight.
- **🔴 AVOID (<45): Unsafe.** Do not stop here with high-value cargo.

---

## 3. Route Analysis Logic

### 3.1 Zone Classification
We scan the route every **20 miles**.
- **RED ZONE:** Any segment with Risk Score ≥ 7.0.
    - *Action:* Non-stop transit recommended.
- **YELLOW ZONE:** Any segment with Risk Score ≥ 5.0.
    - *Action:* Stop only at Level 1/2 facilities.

### 3.2 Route Multipliers
Longer routes multiply overall risk due to cumulative exposure.
- **Cross Country (>1500 mi):** 1.4x multiplier
- **Long Haul (1000-1500 mi):** 1.25x multiplier
- **Regional (500-1000 mi):** 1.1x multiplier

---

**Last Updated:** January 2026
**Source Code:** `safetravels/mcp/config.py`
