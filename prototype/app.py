#!/usr/bin/env python3
"""
Life Simulator — Interactive Financial Planning Game
DIFFICULTY OVERHAUL v2.0:
- Variable market returns with crash events
- Real inflation eroding purchasing power
- Hidden salary/debt ranges (revealed after committing)
- Mid-game decision points: job loss, kids, career pivot, investment choice
- Real failure states: bankruptcy, financial crisis, debt spiral
- Tighter scoring with meaningful failure outcomes
"""

import json
import os
import random
import math
import time
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, template_folder=".", static_folder="static")

GEMINI_API_KEY = "AIzaSyBemhMWACYs1z3pzaxX7r53Gf3E65-yvBQ"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
HIGH_SCORES_FILE = "high_scores.json"

# ─── ECONOMIC CONSTANTS ────────────────────────────────────────────────────────
INFLATION_RATE = 0.032           # 3.2% annual inflation (erodes real purchasing power)
BASE_MARKET_RETURN = 0.07        # Expected real return, but variable
MARKET_CRASH_PROBABILITY = 0.12  # 12% chance of a down year in any given year
MARKET_CRASH_SEVERITY = (-0.35, -0.15)  # Market drops 15–35% in a crash
MARKET_BOOM_PROBABILITY = 0.18   # 18% chance of a great year
MARKET_BOOM_GAIN = (0.18, 0.32)  # Market gains 18–32% in a boom
CREDIT_CARD_APR = 0.2299         # 22.99% — realistic
STUDENT_LOAN_RATE = 0.065        # 6.5% average
TAX_RATE_EFFECTIVE = 0.22        # 22% effective federal + state

def load_high_scores():
    if os.path.exists(HIGH_SCORES_FILE):
        try:
            with open(HIGH_SCORES_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return []

def save_high_scores(scores):
    with open(HIGH_SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def add_high_score(name, score, net_worth, mode):
    scores = load_high_scores()
    scores.append({
        "name": name,
        "score": score,
        "net_worth": net_worth,
        "mode": mode,
        "timestamp": int(time.time())
    })
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:20]
    save_high_scores(scores)
    return scores

def call_gemini(prompt, max_tokens=2000):
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.9}
        }
        resp = requests.post(GEMINI_URL, json=payload, timeout=8)
        data = resp.json()
        if "candidates" in data and data["candidates"]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except Exception as e:
        print(f"Gemini unavailable (using fallback): {type(e).__name__}")
        return None

# ─── GAME DATA ─────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Morgan", "Riley", "Avery", "Quinn", "Skyler",
    "Devon", "Cameron", "Peyton", "Taylor", "Reese", "Blake", "Drew", "Jamie",
    "Parker", "Logan", "Finley", "Rowan", "Emery", "Harper", "Elliot", "Sage"
]

LAST_NAMES = [
    "Rivera", "Chen", "Patel", "Johnson", "Williams", "Kim", "Martinez",
    "Thompson", "Garcia", "Davis", "Wilson", "Anderson", "Taylor", "Harris",
    "Jackson", "White", "Lewis", "Robinson", "Walker", "Hall"
]

HOMETOWNS = [
    "Cedar Falls, Iowa", "Tucson, Arizona", "Raleigh, North Carolina",
    "Spokane, Washington", "Baton Rouge, Louisiana", "Akron, Ohio",
    "El Paso, Texas", "Fresno, California", "Omaha, Nebraska",
    "Richmond, Virginia", "Albuquerque, New Mexico", "Lubbock, Texas",
    "Knoxville, Tennessee", "Boise, Idaho", "Greensboro, North Carolina"
]

FAMILY_BACKGROUNDS = [
    {
        "id": "working_class",
        "label": "Working Class",
        "desc": "Your parents work hard every day. No college savings fund, but you've learned the value of a dollar. First-generation college student if you go.",
        "debt_modifier": 1.3,
        "resilience_bonus": 0.05,
        "starting_savings": 800,
        "credit_score_start": 620
    },
    {
        "id": "middle_class",
        "label": "Middle Class",
        "desc": "Comfortable but not wealthy. Your parents helped a little with applications. Some college savings, but you'll still need loans.",
        "debt_modifier": 1.0,
        "resilience_bonus": 0.0,
        "starting_savings": 2500,
        "credit_score_start": 680
    },
    {
        "id": "upper_middle",
        "label": "Upper-Middle Class",
        "desc": "Your parents are professionals. Good neighborhood, good schools. They can cover some college costs — but expect you to stand on your own eventually.",
        "debt_modifier": 0.6,
        "resilience_bonus": -0.02,
        "starting_savings": 8000,
        "credit_score_start": 720
    },
    {
        "id": "challenging",
        "label": "Challenging Circumstances",
        "desc": "Life hasn't been easy. You've worked since you were 14. You might be supporting family too. But hardship has made you scrappy and resourceful.",
        "debt_modifier": 1.5,
        "resilience_bonus": 0.08,
        "starting_savings": 200,
        "credit_score_start": 580
    }
]

# ── HIDDEN INFO: salary/debt shown as ranges pre-commitment, exact value revealed after ──
POST_HS_CHOICES = [
    {
        "id": "four_year",
        "icon": "🎓",
        "title": "4-Year University",
        "desc": "The traditional path. Take on loans, earn a degree, unlock higher-earning careers. Big investment in your future.",
        "tags": [["credentials", "blue"], ["debt risk", "red"], ["ceiling↑", "green"]],
        # Hidden until committed — player sees only range hint
        "debt_base": 38000,
        "debt_range_hint": "$28K–$52K debt depending on school & aid",
        "years": 4,
        "salary_base": 58000,
        "salary_range_hint": "$48K–$72K starting salary",
        "salary_growth_bonus": 0.03,
        "has_college": True
    },
    {
        "id": "community_then_transfer",
        "icon": "🏫",
        "title": "Community College → Transfer",
        "desc": "Start at community college for 2 years, transfer to state school. A smart, cost-effective path to a 4-year degree.",
        "tags": [["smart savings", "green"], ["longer path", "amber"], ["degree", "blue"]],
        "debt_base": 18000,
        "debt_range_hint": "$12K–$26K debt",
        "years": 4,
        "salary_base": 54000,
        "salary_range_hint": "$44K–$65K starting salary",
        "salary_growth_bonus": 0.025,
        "has_college": True
    },
    {
        "id": "trade_school",
        "icon": "🔧",
        "title": "Trade / Vocational School",
        "desc": "Electrician, plumber, HVAC, welding. 2 years, minimal debt, immediate solid income.",
        "tags": [["low debt", "green"], ["job security", "blue"], ["immediate income", "green"]],
        "debt_base": 8000,
        "debt_range_hint": "$4K–$14K debt",
        "years": 2,
        "salary_base": 52000,
        "salary_range_hint": "$42K–$62K starting salary",
        "salary_growth_bonus": 0.018,
        "has_college": False
    },
    {
        "id": "work_immediately",
        "icon": "💼",
        "title": "Enter the Workforce",
        "desc": "Skip school entirely. Start earning now, avoid debt. Harder path to advancement without credentials.",
        "tags": [["no debt", "green"], ["limited ceiling", "amber"], ["head start", "blue"]],
        "debt_base": 0,
        "debt_range_hint": "No school debt",
        "years": 0,
        "salary_base": 36000,
        "salary_range_hint": "$28K–$42K starting salary",
        "salary_growth_bonus": 0.01,
        "has_college": False
    },
    {
        "id": "military",
        "icon": "🎖️",
        "title": "Military Service",
        "desc": "Serve for 4 years. Free housing, food, training, GI Bill for college after. Demanding — but you'll come out ahead financially.",
        "tags": [["GI Bill", "green"], ["discipline", "blue"], ["risk", "red"]],
        "debt_base": 0,
        "debt_range_hint": "No school debt + housing stipend",
        "years": 4,
        "salary_base": 42000,
        "salary_range_hint": "$38K–$50K starting salary",
        "salary_growth_bonus": 0.022,
        "has_college": True
    }
]

CAREER_CHOICES = [
    {
        "id": "bigtech",
        "icon": "💻",
        "title": "Big Tech Job",
        "desc": "High pressure, long hours, but strong comp and rapid career growth. Comes with layoff risk in downturns.",
        "tags": [["income↑", "green"], ["stress↑", "red"], ["layoff risk", "amber"]],
        "salary": 90000,
        "salary_range_hint": "$78K–$105K total comp",
        "stress": 7,
        "growth": 9,
        "layoff_risk": 0.18,   # 18% chance of layoff in any recession year
        "requires_college": True
    },
    {
        "id": "nonprofit",
        "icon": "🌱",
        "title": "Nonprofit / Public Service",
        "desc": "Meaningful work and PSLF loan forgiveness eligibility after 10 years. Salary growth is limited.",
        "tags": [["fulfillment↑", "green"], ["forgiveness", "blue"], ["income↓", "amber"]],
        "salary": 42000,
        "salary_range_hint": "$36K–$48K",
        "stress": 4,
        "growth": 5,
        "layoff_risk": 0.05,
        "requires_college": False
    },
    {
        "id": "startup",
        "icon": "🚀",
        "title": "Early-Stage Startup",
        "desc": "$65K + equity. 55% chance the company fails within 5 years. If it succeeds, big upside.",
        "tags": [["equity", "green"], ["failure risk", "red"], ["learning↑", "blue"]],
        "salary": 65000,
        "salary_range_hint": "$55K–$75K + equity (could be $0)",
        "stress": 8,
        "growth": 8,
        "layoff_risk": 0.35,   # startup failure chance
        "requires_college": False
    },
    {
        "id": "skilled_trade_career",
        "icon": "🔧",
        "title": "Master Your Trade",
        "desc": "Run your own plumbing/electrical/HVAC business. Physically demanding — injuries are a real risk.",
        "tags": [["own boss", "green"], ["stable", "blue"], ["injury risk", "red"]],
        "salary": 58000,
        "salary_range_hint": "$48K–$72K (variable)",
        "stress": 5,
        "growth": 6,
        "layoff_risk": 0.08,
        "requires_college": False
    },
    {
        "id": "sales",
        "icon": "📊",
        "title": "Sales / Real Estate",
        "desc": "Commission-based. High upside, but income swings wildly. Bad markets can cut your income in half.",
        "tags": [["upside", "green"], ["volatile income", "red"], ["hustle", "blue"]],
        "salary": 62000,
        "salary_range_hint": "$30K–$110K depending on performance",
        "stress": 6,
        "growth": 7,
        "layoff_risk": 0.12,
        "requires_college": False
    },
    {
        "id": "healthcare",
        "icon": "🏥",
        "title": "Healthcare Worker",
        "desc": "Nursing, PA, or allied health. Strong demand, but student debt is often substantial. Burnout is real.",
        "tags": [["job security", "green"], ["burnout risk", "red"], ["debt heavy", "amber"]],
        "salary": 72000,
        "salary_range_hint": "$62K–$85K",
        "stress": 7,
        "growth": 7,
        "layoff_risk": 0.04,
        "requires_college": True
    }
]

HOUSING_CHOICES = [
    {
        "id": "rent_city",
        "icon": "🏙️",
        "title": "Rent in the City",
        "desc": "Close to work and social life. Rent increases ~5% annually — what costs $1,800 now costs $2,300 in 5 years.",
        "tags": [["convenience", "blue"], ["rent inflation", "red"]],
        "rent": 1800,
        "savings_mod": -0.15,
        "equity": 0,
        "rent_growth": 0.05
    },
    {
        "id": "buy_house",
        "icon": "🏠",
        "title": "Buy Starter Home",
        "desc": "Split mortgage with roommate. Builds equity but illiquid. If home values drop, you're underwater.",
        "tags": [["equity", "green"], ["illiquid", "amber"], ["price risk", "red"]],
        "rent": 1100,
        "savings_mod": 0.05,
        "equity": 120000,
        "rent_growth": 0.0,    # fixed mortgage
        "home_crash_risk": 0.15  # 15% chance of 20% home value drop
    },
    {
        "id": "rent_cheap",
        "icon": "🏘️",
        "title": "Cheap Suburban Rental",
        "desc": "$950/mo with roommates. Long commute — that time has real value. Still subject to rent increases.",
        "tags": [["savings↑", "green"], ["commute cost", "red"]],
        "rent": 950,
        "savings_mod": 0.20,
        "equity": 0,
        "rent_growth": 0.04
    },
    {
        "id": "family",
        "icon": "👨‍👩‍👧",
        "title": "Move Back Home",
        "desc": "$300/mo to family. Maximum savings, but limited mobility for job opportunities.",
        "tags": [["max savings", "green"], ["career limits", "amber"]],
        "rent": 300,
        "savings_mod": 0.35,
        "equity": 0,
        "rent_growth": 0.02,
        "career_penalty": 0.05   # 5% lower raises due to location constraints
    }
]

DEBT_CHOICES = [
    {
        "id": "minimum",
        "icon": "🐢",
        "title": "Minimum Payments",
        "desc": "Pay the minimum (~$380/mo). Interest compounds at 6.5%. After 10 years you'll have paid nearly double the principal.",
        "tags": [["cash flow", "green"], ["total cost↑↑", "red"]],
        "debt_payment": 380,
        "debt_years": 10,
        "invest_mod": 1.0,
        "total_interest_multiplier": 1.45
    },
    {
        "id": "aggressive",
        "icon": "💪",
        "title": "Aggressive Payoff",
        "desc": "Pay $1,200/mo. Debt-free in ~3 years. Very cash-poor in the meantime — no buffer for emergencies.",
        "tags": [["debt-free fast", "green"], ["cash-poor", "red"], ["no safety net", "red"]],
        "debt_payment": 1200,
        "debt_years": 3,
        "invest_mod": 0.3,   # almost nothing invested during payoff
        "total_interest_multiplier": 1.08
    },
    {
        "id": "refinance",
        "icon": "🔄",
        "title": "Refinance to Private Loan",
        "desc": "Lower rate (4.5%) but you lose federal protections — income-driven repayment, deferment, forgiveness. A bet things stay stable.",
        "tags": [["lower rate", "green"], ["lose protections", "red"], ["balanced", "blue"]],
        "debt_payment": 600,
        "debt_years": 7,
        "invest_mod": 0.7,
        "total_interest_multiplier": 1.18,
        "no_forgiveness": True   # forfeit PSLF
    },
    {
        "id": "forgiveness",
        "icon": "🎁",
        "title": "Income-Driven + PSLF Track",
        "desc": "~$180/mo. Only works if you stay at a nonprofit 10 years. If you leave for better pay, you're back to full debt.",
        "tags": [["low payments", "green"], ["career lock-in", "red"], ["risky long game", "amber"]],
        "debt_payment": 180,
        "debt_years": 20,
        "invest_mod": 1.2,
        "total_interest_multiplier": 1.9,  # if forgiveness fails, massive interest accrued
        "forgiveness_dependent": True
    }
]

LIFESTYLE_CHOICES = [
    {
        "id": "lifestyle_up",
        "icon": "✈️",
        "title": "Upgrade Your Lifestyle",
        "desc": "New car, travel, nicer apartment. Lifestyle inflation is permanent — it's very hard to cut back later.",
        "tags": [["enjoyment", "green"], ["lifestyle lock-in", "red"]],
        "lifestyle_cost": 1500,
        "savings_rate_boost": -0.05,
        "side_income": 0,
        "lifestyle_inflation_lock": True
    },
    {
        "id": "invest_first",
        "icon": "📈",
        "title": "Invest Most of the Raise",
        "desc": "Keep lifestyle flat, max 401k, funnel into index funds. Boring now, powerful later — if the market cooperates.",
        "tags": [["wealth↑", "green"], ["discipline", "blue"]],
        "lifestyle_cost": 300,
        "savings_rate_boost": 0.12,
        "side_income": 0
    },
    {
        "id": "balanced_life",
        "icon": "⚖️",
        "title": "Balance It Out",
        "desc": "Half the raise to lifestyle, half to savings. The middle path — neither great at wealth-building nor miserable.",
        "tags": [["balance", "blue"], ["steady", "green"]],
        "lifestyle_cost": 700,
        "savings_rate_boost": 0.06,
        "side_income": 0
    },
    {
        "id": "side_hustle",
        "icon": "💡",
        "title": "Start a Side Hustle",
        "desc": "Extra income potential, but ~15 hrs/week. High chance of burnout. Most side hustles fail within 2 years.",
        "tags": [["income+", "green"], ["burnout risk", "red"], ["time↓", "amber"]],
        "lifestyle_cost": 400,
        "savings_rate_boost": 0.10,
        "side_income": 15000,
        "burnout_risk": 0.40,    # 40% chance side hustle collapses by year 3
        "burnout_penalty": 8000  # medical/stress costs if burnout hits
    }
]

EMERGENCY_CHOICES = [
    {
        "id": "prepared",
        "icon": "🛡️",
        "title": "Use Emergency Fund",
        "desc": "You have 6 months saved. Bridge the gap without touching investments or taking on debt.",
        "tags": [["resilient", "green"], ["prepared", "blue"]],
        "emergency_cost": 0,
        "stress_event": False,
        "requires_savings": 15000   # must have this much saved or this option is unavailable
    },
    {
        "id": "credit",
        "icon": "💳",
        "title": "Put It on Credit Cards",
        "desc": "Charge $9,500 at 22.99% APR. Minimum payments drag this out 3+ years. Total payback: ~$14,000.",
        "tags": [["quick fix", "amber"], ["debt spiral risk", "red"]],
        "emergency_cost": 9500,
        "total_repayment": 14000,
        "stress_event": True,
        "credit_score_hit": -45
    },
    {
        "id": "withdraw_401k",
        "icon": "📉",
        "title": "Withdraw from 401k",
        "desc": "Pull $14K early. 10% penalty + income tax = you net ~$9K but lose $14K of compound growth forever.",
        "tags": [["available now", "amber"], ["10% penalty", "red"], ["compounding lost", "red"]],
        "emergency_cost": 14000,
        "net_received": 9000,
        "compound_loss_multiplier": 3.5,  # what that $14K would have grown to
        "stress_event": True
    },
    {
        "id": "family_loan",
        "icon": "🤝",
        "title": "Borrow from Family",
        "desc": "Interest-free but with strings attached. Paid back over 2 years, $500/mo. Relationship strain is real.",
        "tags": [["low cost", "green"], ["relationship risk", "amber"]],
        "emergency_cost": 2000,
        "monthly_repayment": 500,
        "repayment_months": 24,
        "stress_event": False
    }
]

# ─── MID-GAME DECISION POINTS (new for difficulty overhaul) ────────────────────

JOB_LOSS_CHOICES = [
    {
        "id": "pivot_industry",
        "icon": "🔄",
        "title": "Pivot to a New Industry",
        "desc": "Take a 20% pay cut to enter a growing field. Takes 12–18 months to ramp back up.",
        "tags": [["new start", "blue"], ["pay cut", "red"], ["long term upside", "green"]],
        "income_impact": -0.20,
        "duration_months": 15,
        "upside_probability": 0.55
    },
    {
        "id": "freelance_gap",
        "icon": "💼",
        "title": "Go Freelance While Searching",
        "desc": "Cobble together contracts. Unpredictable income, no benefits. Average 8 months before full-time.",
        "tags": [["flexible", "blue"], ["volatile", "amber"], ["no benefits", "red"]],
        "income_impact": -0.35,
        "duration_months": 8,
        "health_insurance_gap": True
    },
    {
        "id": "take_first_offer",
        "icon": "🚨",
        "title": "Take the First Offer",
        "desc": "Any job is better than no job. Significant pay cut, likely underemployed. Easier to find work while working.",
        "tags": [["immediate income", "green"], ["underemployment", "red"]],
        "income_impact": -0.30,
        "duration_months": 4,
        "career_setback": True
    },
    {
        "id": "upskill_unemployed",
        "icon": "📚",
        "title": "Go Back to School / Upskill",
        "desc": "6 months of intensive upskilling. Zero income, burn savings. Higher salary ceiling if it works out.",
        "tags": [["salary ceiling↑", "green"], ["savings burn", "red"], ["risky", "amber"]],
        "income_impact": -1.0,
        "duration_months": 6,
        "upskill_bonus": 0.15
    }
]

KIDS_CHOICES = [
    {
        "id": "have_kids_now",
        "icon": "👶",
        "title": "Start a Family",
        "desc": "Kids cost ~$15–17K/year per child through age 17. Childcare alone runs $1,200–$2,400/mo. One partner may reduce hours.",
        "tags": [["meaningful", "green"], ["expensive", "red"], ["career impact", "amber"]],
        "annual_cost": 16000,
        "years": 17,
        "career_impact": -0.08,
        "savings_rate_hit": -0.10
    },
    {
        "id": "wait_kids",
        "icon": "⏳",
        "title": "Wait — Focus on Career First",
        "desc": "Delay family until finances are stronger. More time to build wealth, but some opportunities narrow with age.",
        "tags": [["wealth first", "blue"], ["delayed", "amber"]],
        "annual_cost": 0,
        "career_impact": 0.03,
        "savings_rate_hit": 0
    },
    {
        "id": "no_kids",
        "icon": "🚫",
        "title": "Choose Not to Have Kids",
        "desc": "The DINK path. Significantly more financial flexibility and career mobility.",
        "tags": [["max flexibility", "green"], ["personal choice", "blue"]],
        "annual_cost": 0,
        "career_impact": 0.05,
        "savings_rate_hit": 0.05
    }
]

INVESTMENT_CHOICES = [
    {
        "id": "index_funds",
        "icon": "📊",
        "title": "Stick to Index Funds",
        "desc": "Boring, diversified, low-cost. Average ~7% real returns but you ride every crash too. No shortcuts.",
        "tags": [["low cost", "green"], ["market risk", "amber"], ["proven", "blue"]],
        "expected_return": 0.07,
        "risk_level": "medium",
        "crash_exposure": 1.0
    },
    {
        "id": "crypto_bet",
        "icon": "₿",
        "title": "Go Heavy on Crypto",
        "desc": "40% of portfolio into crypto. Could 10x. Could lose 80%. Not a plan — a bet.",
        "tags": [["massive upside", "green"], ["80% loss risk", "red"], ["volatile", "red"]],
        "expected_return": 0.12,
        "risk_level": "extreme",
        "crash_exposure": 2.5,
        "ruin_probability": 0.35
    },
    {
        "id": "real_estate_invest",
        "icon": "🏘️",
        "title": "Buy a Rental Property",
        "desc": "Leverage into a rental. Cash flow positive only if vacancy is low. One bad tenant + repairs = year erased.",
        "tags": [["leveraged", "amber"], ["cash flow", "green"], ["landlord risk", "red"]],
        "expected_return": 0.09,
        "risk_level": "medium-high",
        "crash_exposure": 1.3,
        "vacancy_risk": 0.20
    },
    {
        "id": "cash_conservative",
        "icon": "🏦",
        "title": "Keep It in High-Yield Savings",
        "desc": "Play it safe: 4.5–5% in HYSA. No market risk. But inflation slowly erodes real value over 15 years.",
        "tags": [["safe", "green"], ["inflation drag", "red"]],
        "expected_return": 0.045,
        "risk_level": "low",
        "crash_exposure": 0.0
    }
]

# ─── FAILURE STATES ────────────────────────────────────────────────────────────

FAILURE_STATES = {
    "bankruptcy": {
        "threshold": -30000,
        "title": "Financial Bankruptcy",
        "desc": "Debt spiral became unmanageable. You file Chapter 7. Credit score drops to 520 and stays there for 7 years. You'll rebuild — but you're starting over.",
        "score_cap": 22,
        "recovery_years": 7
    },
    "debt_spiral": {
        "threshold": -15000,
        "title": "Debt Spiral",
        "desc": "Credit card debt compounding at 23% has taken on a life of its own. Minimum payments barely cover interest. You're treading water.",
        "score_cap": 35,
        "monthly_drag": 800
    },
    "financial_crisis": {
        "threshold": 0,     # net worth is zero with no assets
        "title": "Financial Crisis",
        "desc": "No savings, no investments, living paycheck to paycheck. One emergency away from serious trouble.",
        "score_cap": 45
    }
}

# ─── GEMINI GENERATION ─────────────────────────────────────────────────────────

def generate_all_scenarios(char_name, char_bg, post_hs_path, career_choice):
    context = f"""
Character: {char_name}
Background: {char_bg['label']} - {char_bg['desc']}
Post-high school path: {post_hs_path['title']} - {post_hs_path['desc']}
Career: {career_choice['title']} - {career_choice['desc']}
"""
    prompt = f"""You are writing for an interactive financial planning game called "Life Simulator". 
The player's character is:
{context}

Generate 15 annual life events (ages 18-37) that create emotional storytelling AND financial impact.
Some should be positive, some negative, some neutral but thought-provoking.

IMPORTANT: 
- At least 3 events should be financially severe (job loss, major medical event, car totaled, recession layoff, market crash hitting investments)
- Make them feel like a real person's life — personal, specific, emotional
- Include consequences of earlier decisions

Respond with ONLY a JSON array, no markdown, no explanation:
[
  {{
    "age": 19,
    "title": "Short punchy title",
    "story": "2-3 vivid, personal sentences.",
    "financial_impact": 1500,
    "impact_type": "one_time_gain",
    "emoji": "🎉",
    "severity": "minor"
  }}
]

impact_type options: "one_time_gain", "one_time_loss", "monthly_income_boost", "monthly_expense", "savings_rate_change", "investment_multiplier"
severity options: "minor", "moderate", "major"
financial_impact: positive number (dollar amount or percentage*100 for rates/multipliers)

Ages should span 18-37."""

    result = call_gemini(prompt, max_tokens=3000)
    scenarios = []
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean[clean.find("["):clean.rfind("]")+1]
            scenarios = json.loads(clean)
        except Exception as e:
            print(f"JSON parse error: {e}")
    
    if not scenarios:
        scenarios = get_fallback_scenarios(char_name)
    
    return scenarios[:15]


def generate_gemini_choices(char_profile, all_choices):
    prompt = f"""You are playing a financial planning game as an AI advisor.
Character profile: {json.dumps(char_profile, indent=2)}

This game has been OVERHAULED for difficulty. Key rules:
- Market returns are VARIABLE — crashes happen. Index funds are safer long-term.
- Debt compounds at 6.5%; credit cards at 22.99%. Debt is dangerous.
- Having kids costs $16K/yr for 17 years — factor this in.
- Job loss events happen. Always maintain an emergency fund.
- Lifestyle inflation is PERMANENT — it's a trap.

Make ALL the following decisions to maximize net worth at age 37.

POST HIGH SCHOOL: {json.dumps([{"id":c["id"],"title":c["title"],"debt_range_hint":c["debt_range_hint"],"salary_range_hint":c["salary_range_hint"]} for c in POST_HS_CHOICES])}
CAREER: {json.dumps([{"id":c["id"],"title":c["title"],"salary":c["salary"],"layoff_risk":c["layoff_risk"]} for c in CAREER_CHOICES])}
HOUSING: {json.dumps([{"id":c["id"],"title":c["title"],"rent":c["rent"],"savings_mod":c["savings_mod"]} for c in HOUSING_CHOICES])}
DEBT: {json.dumps([{"id":c["id"],"title":c["title"],"debt_payment":c["debt_payment"],"invest_mod":c["invest_mod"]} for c in DEBT_CHOICES])}
LIFESTYLE: {json.dumps([{"id":c["id"],"title":c["title"],"savings_rate_boost":c["savings_rate_boost"]} for c in LIFESTYLE_CHOICES])}
EMERGENCY: {json.dumps([{"id":c["id"],"title":c["title"],"emergency_cost":c["emergency_cost"]} for c in EMERGENCY_CHOICES])}
JOB LOSS (if it occurs): {json.dumps([{"id":c["id"],"title":c["title"],"income_impact":c["income_impact"]} for c in JOB_LOSS_CHOICES])}
KIDS: {json.dumps([{"id":c["id"],"title":c["title"]} for c in KIDS_CHOICES])}
INVESTMENTS: {json.dumps([{"id":c["id"],"title":c["title"],"expected_return":c["expected_return"],"risk_level":c["risk_level"]} for c in INVESTMENT_CHOICES])}

Respond ONLY with JSON:
{{
  "post_hs": "choice_id",
  "career": "choice_id",
  "housing": "choice_id",
  "debt": "choice_id",
  "lifestyle": "choice_id",
  "emergency": "choice_id",
  "job_loss": "choice_id",
  "kids": "choice_id",
  "investment": "choice_id",
  "reasoning": "3 sentences explaining your strategy"
}}"""

    result = call_gemini(prompt, max_tokens=800)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                start = clean.find("{")
                end = clean.rfind("}") + 1
                clean = clean[start:end]
            return json.loads(clean)
        except Exception as e:
            print(f"Gemini choices parse error: {e}")
    
    return {
        "post_hs": "community_then_transfer",
        "career": "bigtech",
        "housing": "rent_cheap",
        "debt": "aggressive",
        "lifestyle": "invest_first",
        "emergency": "prepared",
        "job_loss": "upskill_unemployed",
        "kids": "wait_kids",
        "investment": "index_funds",
        "reasoning": "Minimize debt costs, live lean, invest aggressively in diversified index funds. Emergency fund is non-negotiable. Delay kids until net worth exceeds $100K."
    }


BACKSTORY_FALLBACKS = {
    "working_class": "You grew up watching your parents stretch every dollar. You learned early that nothing comes free — you've been hustling since you were old enough to mow lawns. School was something you fit in between shifts. Now at 18, you're the first in your family who gets to choose what comes next.",
    "middle_class": "You grew up in a comfortable house in a decent neighborhood — not rich, but never really worried about rent either. Your parents worked hard and expected you to do the same. You've had opportunities, and now it's on you to actually use them.",
    "upper_middle": "Your parents are professionals who gave you every advantage — good schools, SAT prep, family vacations. You've never had to think much about money. That might be your biggest blind spot. Now the training wheels come off.",
    "challenging": "Life has thrown everything at you and you're still standing. You've been working since 14, sometimes to help your family make rent. Hardship has made you scrappy in ways your peers can't understand. You're starting behind — but you're also starting hungry.",
}

def generate_character_backstory(name, hometown, background):
    prompt = f"""Write a SHORT (3-4 sentences) personal backstory for {name} from {hometown} 
with a {background['label']} background: "{background['desc']}"

Make it feel real and emotionally resonant. Mention one specific memory or detail.
Write in second person ("You grew up..."). Under 80 words. No lists."""
    
    result = call_gemini(prompt, max_tokens=200)
    if result:
        return result.strip()
    return BACKSTORY_FALLBACKS.get(background["id"],
        f"You grew up in {hometown}, shaped by your {background['label'].lower()} upbringing. Every dollar has taught you something. Now at 18, the whole future is open.")


def get_fallback_scenarios(char_name):
    return [
        {"age": 19, "title": "Unexpected Medical Bill", "story": f"{char_name} got a nasty infection that required urgent care. No insurance meant paying out of pocket.", "financial_impact": 2200, "impact_type": "one_time_loss", "emoji": "🏥", "severity": "moderate"},
        {"age": 20, "title": "Summer Job Bonus", "story": "The manager loved your work ethic and slipped you a cash bonus.", "financial_impact": 800, "impact_type": "one_time_gain", "emoji": "💵", "severity": "minor"},
        {"age": 21, "title": "Car Totaled", "story": "A driver ran a red light and totaled your car. Insurance covered less than you expected.", "financial_impact": 4500, "impact_type": "one_time_loss", "emoji": "🚗", "severity": "major"},
        {"age": 22, "title": "Freelance Gig", "story": "A friend connected you with a project that became recurring monthly income.", "financial_impact": 500, "impact_type": "monthly_income_boost", "emoji": "💻", "severity": "minor"},
        {"age": 23, "title": "Market Crash (-28%)", "story": "The market dropped sharply. Your portfolio fell with it. You held firm, but it hurt to watch.", "financial_impact": 72, "impact_type": "investment_multiplier", "emoji": "📉", "severity": "major"},
        {"age": 24, "title": "Promotion!", "story": "Your hard work paid off. Your boss offered a significant raise and more responsibility.", "financial_impact": 9000, "impact_type": "one_time_gain", "emoji": "🎉", "severity": "moderate"},
        {"age": 25, "title": "Rent Spiked Again", "story": "Your landlord raised rent $400/month at renewal. You had to absorb it or move.", "financial_impact": 400, "impact_type": "monthly_expense", "emoji": "🏠", "severity": "moderate"},
        {"age": 26, "title": "Family Emergency", "story": "A family member needed financial help. You stepped up — because that's who you are.", "financial_impact": 5500, "impact_type": "one_time_loss", "emoji": "❤️", "severity": "moderate"},
        {"age": 27, "title": "Strong Market Year", "story": "A disciplined year of investing paid off as the market rebounded. Your portfolio surged.", "financial_impact": 118, "impact_type": "investment_multiplier", "emoji": "📈", "severity": "minor"},
        {"age": 28, "title": "Identity Theft", "story": "Someone stole your financial identity. Months of calls, frozen accounts, and stress to clean it up.", "financial_impact": 3800, "impact_type": "one_time_loss", "emoji": "🕵️", "severity": "major"},
        {"age": 29, "title": "Tax Surprise", "story": "A side project meant you owed more taxes than expected. The IRS is unforgiving.", "financial_impact": 2800, "impact_type": "one_time_loss", "emoji": "📋", "severity": "moderate"},
        {"age": 30, "title": "Side Hustle Revenue", "story": "That project you've been building quietly started generating real consistent revenue.", "financial_impact": 1200, "impact_type": "monthly_income_boost", "emoji": "🚀", "severity": "minor"},
        {"age": 31, "title": "Recession Hits", "story": "The economy contracted. Hiring froze. You kept your job but raises disappeared for two years.", "financial_impact": -0.02, "impact_type": "savings_rate_change", "emoji": "📊", "severity": "major"},
        {"age": 32, "title": "Apartment Flooding", "story": "A burst pipe damaged your belongings. Renters insurance covered some, but not all.", "financial_impact": 2200, "impact_type": "one_time_loss", "emoji": "🌊", "severity": "moderate"},
        {"age": 33, "title": "Industry Recognition", "story": "You were featured in an industry publication. New clients found you. Income jumped.", "financial_impact": 14000, "impact_type": "one_time_gain", "emoji": "⭐", "severity": "moderate"},
    ]


# ─── SIMULATION ENGINE (OVERHAULED) ───────────────────────────────────────────

def get_market_return(year, seed_offset=0):
    """Variable market returns: crashes, booms, and normal years."""
    rng = random.Random(year * 1337 + seed_offset)
    r = rng.random()
    if r < MARKET_CRASH_PROBABILITY:
        crash = rng.uniform(*MARKET_CRASH_SEVERITY)
        return crash, "crash"
    elif r < MARKET_CRASH_PROBABILITY + MARKET_BOOM_PROBABILITY:
        boom = rng.uniform(*MARKET_BOOM_GAIN)
        return boom, "boom"
    else:
        # Normal year: base return +/- variance
        variance = rng.gauss(0, 0.06)
        return BASE_MARKET_RETURN + variance, "normal"


def apply_investment_strategy(investment_choice_id, base_return, return_type, rng):
    """Modify returns based on investment choice."""
    inv = next((c for c in INVESTMENT_CHOICES if c["id"] == investment_choice_id), INVESTMENT_CHOICES[0])
    
    if investment_choice_id == "crypto_bet":
        # Crypto: amplified swings + ruin risk
        if rng.random() < inv["ruin_probability"] / 20:  # spread over years
            return -0.50, "crypto_crash"
        return base_return * inv["crash_exposure"] + rng.gauss(0.05, 0.20), return_type
    
    elif investment_choice_id == "cash_conservative":
        # HYSA: no market exposure, steady but inflation-lagging
        return inv["expected_return"] - INFLATION_RATE * 0.5, "stable"
    
    elif investment_choice_id == "real_estate_invest":
        # Real estate: vacancy risk dampens some good years
        if return_type == "boom":
            base_return *= 0.7  # doesn't fully participate in market booms
        if rng.random() < inv["vacancy_risk"]:
            return base_return - 0.08, "vacancy_hit"  # bad tenant year
        return base_return * 1.1, return_type
    
    else:  # index_funds (default)
        return base_return, return_type


def compute_results(selections, scenarios=None):
    """Full overhauled simulation with crashes, inflation, hidden reveals, failure states."""
    
    rng = random.Random(42 + hash(json.dumps(selections, sort_keys=True)) % 10000)

    post_hs = next(c for c in POST_HS_CHOICES if c["id"] == selections["post_hs"])
    career = next(c for c in CAREER_CHOICES if c["id"] == selections["career"])
    housing = next(c for c in HOUSING_CHOICES if c["id"] == selections["housing"])
    debt = next(c for c in DEBT_CHOICES if c["id"] == selections["debt"])
    lifestyle = next(c for c in LIFESTYLE_CHOICES if c["id"] == selections["lifestyle"])
    emergency = next(c for c in EMERGENCY_CHOICES if c["id"] == selections["emergency"])
    bg = next(b for b in FAMILY_BACKGROUNDS if b["id"] == selections.get("background", "middle_class"))
    
    # Mid-game choices
    job_loss_id = selections.get("job_loss", "take_first_offer")
    kids_id = selections.get("kids", "wait_kids")
    investment_id = selections.get("investment", "index_funds")
    
    job_loss_choice = next(c for c in JOB_LOSS_CHOICES if c["id"] == job_loss_id)
    kids_choice = next(c for c in KIDS_CHOICES if c["id"] == kids_id)
    
    # ── HIDDEN REVEAL: actual salary/debt rolled with variance ──
    # Player only saw ranges; now the dice are cast
    debt_variance = rng.uniform(0.80, 1.25)
    salary_variance = rng.uniform(0.88, 1.18)
    
    student_debt = post_hs["debt_base"] * bg["debt_modifier"] * debt_variance
    
    # PSLF forgiveness — only works if nonprofit + forgiveness plan + no refinance
    if (selections.get("debt") == "forgiveness" and 
        selections.get("career") == "nonprofit" and
        not debt.get("no_forgiveness")):
        forgiveness_succeeds = rng.random() > 0.25  # 75% PSLF success rate (realistic)
        if forgiveness_succeeds:
            student_debt = 0
        else:
            # Failed forgiveness: full debt + 19 years of accrued interest
            student_debt *= debt.get("total_interest_multiplier", 1.9)
    
    base_age = 18 + post_hs["years"]
    base_salary = career["salary"] * salary_variance
    
    # Career penalty for living at home
    if housing.get("career_penalty"):
        base_salary *= (1 - housing["career_penalty"])
    
    salary_growth = career["growth"] * 0.01 + 0.015  # slightly reduced baseline
    
    # Kids impact
    kids_annual_cost = kids_choice.get("annual_cost", 0)
    kids_career_impact = kids_choice.get("career_impact", 0)
    salary_growth += kids_career_impact
    
    # Lifestyle upswing is a TRAP — hard to undo
    lifestyle_lock = lifestyle.get("lifestyle_inflation_lock", False)
    savings_boost = lifestyle["savings_rate_boost"]
    if lifestyle_lock:
        savings_boost -= 0.02  # gets slightly worse each year (lifestyle inflation creep)
    
    savings_mod = housing.get("savings_mod", 0) + bg["resilience_bonus"]
    emergency_cost = emergency.get("emergency_cost", 0)
    
    # Side hustle burnout
    side_income = lifestyle.get("side_income", 0)
    if side_income and rng.random() < lifestyle.get("burnout_risk", 0):
        side_income = 0  # burnout kills it
        emergency_cost += lifestyle.get("burnout_penalty", 0)
    
    house_equity = housing.get("equity", 0)
    # Home value crash risk
    home_crashed = False
    if house_equity and rng.random() < housing.get("home_crash_risk", 0):
        house_equity *= 0.78   # 22% drop
        home_crashed = True
    
    savings_rate = max(0.01, min(0.45, 0.10 + savings_boost + savings_mod))
    
    # Job loss event (triggered probabilistically or guaranteed in hard mode)
    job_loss_triggered = rng.random() < career.get("layoff_risk", 0.10)
    job_loss_age = base_age + rng.randint(3, 9)  # happens 3-9 years into career
    
    # Build scenario impact map
    scenario_impacts = {}
    if scenarios:
        for s in scenarios:
            if "age" in s and "financial_impact" in s:
                scenario_impacts[s["age"]] = s

    # ── SIMULATION LOOP ──
    net_worth_by_year = []
    investments = float(bg["starting_savings"])
    remaining_debt = float(student_debt)
    credit_card_debt = 0.0
    current_salary = float(base_salary) * 0.55  # lower during school
    failure_state = None
    market_history = []

    # Pre-career years
    for age in range(18, base_age + 1):
        nw = investments - remaining_debt
        net_worth_by_year.append({"age": age, "nw": round(nw)})

    current_salary = float(base_salary)

    for yr in range(1, 38 - base_age + 1):
        age = base_age + yr
        if age > 37:
            break

        # ── Inflation: salary in nominal terms grows, but purchasing power erodes
        current_salary *= (1 + salary_growth + INFLATION_RATE * 0.4)

        # ── Job loss event
        income_multiplier = 1.0
        if job_loss_triggered and age == job_loss_age:
            income_multiplier = 1.0 + job_loss_choice["income_impact"]
            if job_loss_choice.get("upskill_bonus"):
                salary_growth += job_loss_choice["upskill_bonus"] / 10

        annual_income = current_salary * income_multiplier + side_income

        # ── Taxes
        after_tax_income = annual_income * (1 - TAX_RATE_EFFECTIVE)

        # ── Kids cost
        if kids_choice["id"] == "have_kids_now" and age >= base_age + 3:
            after_tax_income = max(0, after_tax_income - kids_annual_cost)

        # ── Housing (inflation-adjusted rent)
        rent_multiplier = (1 + housing.get("rent_growth", 0.03)) ** yr
        effective_rent = housing["rent"] * rent_multiplier
        annual_rent = effective_rent * 12

        # ── Debt payments
        debt_years_remaining = max(0, debt.get("debt_years", 10) - yr)
        annual_debt_pay = debt.get("debt_payment", 0) * 12 if remaining_debt > 0 and debt_years_remaining > 0 else 0
        remaining_debt = max(0.0, remaining_debt * (1 + STUDENT_LOAN_RATE * 0.1) - annual_debt_pay)

        # ── Credit card debt spirals
        if credit_card_debt > 0:
            credit_card_debt = credit_card_debt * (1 + CREDIT_CARD_APR) - 500 * 12
            credit_card_debt = max(0, credit_card_debt)

        # ── Savings & investing
        spendable = after_tax_income - annual_rent - annual_debt_pay - credit_card_debt * 0.1
        annual_savings = max(0, spendable * savings_rate)

        # ── Market returns (variable!)
        base_return, return_type = get_market_return(age, seed_offset=hash(str(selections)) % 100)
        effective_return, effective_type = apply_investment_strategy(investment_id, base_return, return_type, rng)
        market_history.append({"age": age, "return": round(effective_return * 100, 1), "type": effective_type})

        investments = max(0, (investments + annual_savings) * (1 + effective_return))

        # ── Scenario impacts
        if age in scenario_impacts:
            sc = scenario_impacts[age]
            impact = sc["financial_impact"]
            itype = sc.get("impact_type", "one_time_loss")
            if itype == "one_time_gain":
                investments += impact
            elif itype == "one_time_loss":
                investments = max(0, investments - impact)
            elif itype == "monthly_income_boost":
                investments += impact * 12 * 0.5
            elif itype == "monthly_expense":
                investments = max(0, investments - impact * 12)
            elif itype == "investment_multiplier":
                investments *= (impact / 100)
            elif itype == "savings_rate_change":
                savings_rate = max(0.01, min(0.45, savings_rate + impact))

        # ── Emergency event (age 27–30 window)
        if age == 28:
            if emergency["id"] == "credit":
                credit_card_debt += emergency["emergency_cost"]
            elif emergency["id"] == "withdraw_401k":
                investments = max(0, investments - emergency["emergency_cost"])
            elif emergency["id"] == "prepared":
                if investments < emergency.get("requires_savings", 15000):
                    # Didn't actually have the savings — forced onto credit
                    credit_card_debt += 9500
            else:
                investments = max(0, investments - emergency.get("emergency_cost", 0))

        # ── Home equity appreciation (or crash)
        equity_value = 0
        if house_equity:
            if home_crashed and yr < 5:
                equity_value = house_equity * (0.78 + 0.04 * yr) - house_equity
            else:
                equity_value = house_equity * (1 + 0.035 * yr) - house_equity

        # ── Net worth & failure check
        nw = investments - remaining_debt - credit_card_debt + equity_value
        net_worth_by_year.append({"age": age, "nw": round(nw)})

        # Failure state detection — only after career starts (3+ years in)
        # Being in debt during/just after school is normal and expected
        if age >= base_age + 3:
            if nw < FAILURE_STATES["bankruptcy"]["threshold"] and not failure_state:
                failure_state = "bankruptcy"
            elif nw < FAILURE_STATES["debt_spiral"]["threshold"] and not failure_state:
                failure_state = "debt_spiral"
            elif nw <= 0 and investments < 500 and age >= 30 and not failure_state:
                failure_state = "financial_crisis"

    final_nw = net_worth_by_year[-1]["nw"] if net_worth_by_year else 0
    final_salary = round(current_salary + side_income)
    debt_free_age = base_age + debt.get("debt_years", 10) if student_debt > 0 else base_age

    # ── SCORING (tighter — 99 is nearly impossible, 70 is solid, <40 is a bad run) ──
    # Base score starts at 40 (not 50) — you have to earn it
    score = 40

    # Net worth brackets — harder to hit top tiers
    if final_nw > 800000: score += 35
    elif final_nw > 500000: score += 25
    elif final_nw > 300000: score += 16
    elif final_nw > 150000: score += 8
    elif final_nw > 50000: score += 2
    elif final_nw > 0: score -= 2
    elif final_nw < -50000: score -= 35
    elif final_nw < -15000: score -= 25
    elif final_nw < 0: score -= 15

    # Savings discipline — harder thresholds
    if savings_rate > 0.25: score += 10
    elif savings_rate > 0.18: score += 5
    elif savings_rate < 0.06: score -= 12

    # Remaining debt penalties
    if remaining_debt > 20000: score -= 8
    if credit_card_debt > 5000: score -= 18
    elif credit_card_debt > 0: score -= 8

    # Event-driven bonuses/penalties
    if emergency.get("stress_event"): score -= 8
    if job_loss_triggered: score -= 5  # job loss always stings even if handled well
    if home_crashed: score -= 8
    if housing["id"] == "buy_house" and not home_crashed: score += 4
    if side_income > 0: score += 4

    # Background challenge bonus — overcoming adversity
    if bg["id"] == "working_class" and final_nw > 150000: score += 8
    if bg["id"] == "challenging" and final_nw > 75000: score += 12
    if bg["id"] == "challenging" and final_nw > 200000: score += 6  # extra

    # Investment strategy alignment
    if investment_id == "crypto_bet":
        score += 8 if final_nw > 500000 else -12
    if investment_id == "cash_conservative" and final_nw < 150000:
        score -= 10  # inflation killed real value

    # Lifestyle trap penalty
    if lifestyle.get("lifestyle_inflation_lock") and final_nw < 200000:
        score -= 6

    # Apply failure state hard caps
    if failure_state:
        fs = FAILURE_STATES[failure_state]
        score = min(score, fs["score_cap"])

    score = max(5, min(99, score))

    # ── TIMELINE EVENTS ──
    events = [
        {"age": 18, "icon": "🎓", "text": f"High school graduation. Chose: {post_hs['title']}."},
    ]
    if post_hs["has_college"]:
        events.append({"age": base_age, "icon": "🎓", "text": f"Completed education. Actual starting salary: ${round(base_salary/1000)}K (variance applied). Beginning career as: {career['title']}."})
    else:
        events.append({"age": base_age, "icon": "💼", "text": f"Entered workforce: {career['title']}. Starting at ${round(base_salary/1000)}K/yr."})

    if student_debt > 0:
        events.append({"age": base_age, "icon": "💸", "text": f"Actual student debt: ${round(student_debt/1000)}K (variance from aid/tuition). Strategy: {debt['title']}."})
    
    events.append({"age": base_age + 1, "icon": "🏠", "text": f"Housing: {housing['title']}."})
    
    if job_loss_triggered:
        events.append({"age": job_loss_age, "icon": "⚡", "text": f"Job loss event at age {job_loss_age}! Response: {job_loss_choice['title']}."})
    
    if kids_choice["id"] == "have_kids_now":
        events.append({"age": base_age + 3, "icon": "👶", "text": f"Started a family. ~${kids_annual_cost//1000}K/yr in child-rearing costs begin."})
    
    events.append({"age": 28, "icon": "⚠️" if emergency.get("stress_event") else "✅",
                   "text": f"Emergency hit. Response: {emergency['title']}."})
    
    if credit_card_debt > 0:
        events.append({"age": 30, "icon": "💳", "text": f"Credit card debt still outstanding: ${round(credit_card_debt/1000)}K at 22.99% APR."})
    
    if home_crashed:
        events.append({"age": base_age + 4, "icon": "🏚️", "text": "Housing market dropped ~22%. Home now worth less than purchase price."})
    
    if lifestyle.get("burnout_risk") and side_income == 0:
        events.append({"age": base_age + 5, "icon": "🔥", "text": "Side hustle burnout. Had to step away. Recovery costs hit."})
    
    if failure_state:
        fs = FAILURE_STATES[failure_state]
        events.append({"age": 33, "icon": "🚨", "text": f"FAILURE STATE: {fs['title']} — {fs['desc']}"})
    
    if debt_free_age <= 37 and student_debt > 0 and not failure_state:
        events.append({"age": debt_free_age, "icon": "🎉", "text": "Student loans fully paid off!"})
    
    events.append({"age": 37, "icon": "📊",
                   "text": f"Final net worth: ${round(final_nw/1000)}K at age 37. Score: {score}/99."})

    if scenarios:
        for s in scenarios[:4]:
            if s.get("age") and s["age"] not in [e["age"] for e in events]:
                events.append({"age": s["age"], "icon": s.get("emoji", "📌"), "text": s["title"]})

    events.sort(key=lambda x: x["age"])

    return {
        "net_worth_by_year": net_worth_by_year,
        "final_nw": final_nw,
        "final_salary": final_salary,
        "score": score,
        "events": events,
        "savings_rate": savings_rate,
        "debt_free_age": debt_free_age,
        "base_age": base_age,
        "student_debt": round(student_debt),
        "actual_starting_salary": round(base_salary),
        "failure_state": failure_state,
        "failure_details": FAILURE_STATES.get(failure_state) if failure_state else None,
        "market_history": market_history,
        "job_loss_triggered": job_loss_triggered,
        "home_crashed": home_crashed,
        "credit_card_debt": round(credit_card_debt),
        "crash_years": [m["age"] for m in market_history if m["type"] == "crash"]
    }


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/api/character-data")
def get_character_data():
    return jsonify({
        "first_names": FIRST_NAMES,
        "last_names": LAST_NAMES,
        "hometowns": HOMETOWNS,
        "backgrounds": FAMILY_BACKGROUNDS,
        "post_hs_choices": POST_HS_CHOICES,
        "career_choices": CAREER_CHOICES,
        "housing_choices": HOUSING_CHOICES,
        "debt_choices": DEBT_CHOICES,
        "lifestyle_choices": LIFESTYLE_CHOICES,
        "emergency_choices": EMERGENCY_CHOICES,
        # New mid-game choices exposed to frontend
        "job_loss_choices": JOB_LOSS_CHOICES,
        "kids_choices": KIDS_CHOICES,
        "investment_choices": INVESTMENT_CHOICES,
        "failure_states": FAILURE_STATES
    })

@app.route("/api/generate-character", methods=["POST"])
def generate_character():
    data = request.json or {}
    name = random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)
    hometown = random.choice(HOMETOWNS)
    background = random.choice(FAMILY_BACKGROUNDS)
    backstory = generate_character_backstory(name, hometown, background)
    return jsonify({
        "name": name,
        "hometown": hometown,
        "background": background,
        "backstory": backstory
    })

@app.route("/api/generate-backstory", methods=["POST"])
def gen_backstory():
    data = request.json
    name = data.get("name", "Alex")
    hometown = data.get("hometown", "Anytown")
    background = next((b for b in FAMILY_BACKGROUNDS if b["id"] == data.get("background_id", "middle_class")), FAMILY_BACKGROUNDS[1])
    backstory = generate_character_backstory(name, hometown, background)
    return jsonify({"backstory": backstory})

@app.route("/api/generate-scenarios", methods=["POST"])
def generate_scenarios():
    data = request.json
    char_name = data.get("name", "Alex")
    bg_id = data.get("background_id", "middle_class")
    post_hs_id = data.get("post_hs_id", "four_year")
    career_id = data.get("career_id", "bigtech")
    
    bg = next((b for b in FAMILY_BACKGROUNDS if b["id"] == bg_id), FAMILY_BACKGROUNDS[1])
    post_hs = next((c for c in POST_HS_CHOICES if c["id"] == post_hs_id), POST_HS_CHOICES[0])
    career = next((c for c in CAREER_CHOICES if c["id"] == career_id), CAREER_CHOICES[0])
    
    scenarios = generate_all_scenarios(char_name, bg, post_hs, career)
    return jsonify({"scenarios": scenarios})

@app.route("/api/generate-gemini-choices", methods=["POST"])
def gen_gemini_choices():
    data = request.json
    char_profile = data.get("char_profile", {})
    gemini_choices = generate_gemini_choices(char_profile, {})
    return jsonify(gemini_choices)

@app.route("/api/compute-results", methods=["POST"])
def compute():
    data = request.json
    selections = data.get("selections", {})
    scenarios = data.get("scenarios", [])
    result = compute_results(selections, scenarios)
    return jsonify(result)

@app.route("/api/high-scores", methods=["GET"])
def get_high_scores():
    return jsonify(load_high_scores())

@app.route("/api/high-scores", methods=["POST"])
def post_high_score():
    data = request.json
    scores = add_high_score(
        data.get("name", "Anonymous"),
        data.get("score", 0),
        data.get("net_worth", 0),
        data.get("mode", "standard")
    )
    return jsonify({"scores": scores, "success": True})

if __name__ == "__main__":
    print("🎓 Life Simulator v2.0 — DIFFICULTY OVERHAUL — starting on http://localhost:5000")
    app.run(debug=True, port=5000)