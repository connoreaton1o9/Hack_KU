#!/usr/bin/env python3
"""
Life Simulator — Interactive Financial Planning Game
Starting at high school graduation, with college optional.
Modes: Standard, Random, Beat Gemini
"""

import json
import os
import random
import math
import time
import requests
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, template_folder=".", static_folder="static")

GEMINI_API_KEY_FILE = open('prototype/gemini-api-key', 'r')
for key in GEMINI_API_KEY_FILE:
    GEMINI_API_KEY = key.strip('\n')
GEMINI_API_KEY_FILE.close()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
HIGH_SCORES_FILE = "high_scores.json"

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

def add_high_score(name, score, net_worth, mode, game_length=""):
    scores = load_high_scores()
    scores.append({
        "name": name,
        "score": score,
        "net_worth": net_worth,
        "mode": mode,
        "game_length": game_length,
        "timestamp": int(time.time())
    })
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:20]  # top 20
    save_high_scores(scores)
    return scores

def call_gemini(prompt, max_tokens=2000):
    """Call Gemini API with a short timeout; returns None immediately on failure."""
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
        "starting_savings": 800
    },
    {
        "id": "middle_class",
        "label": "Middle Class",
        "desc": "Comfortable but not wealthy. Your parents helped a little with applications. Some college savings, but you'll still need loans.",
        "debt_modifier": 1.0,
        "resilience_bonus": 0.0,
        "starting_savings": 2500
    },
    {
        "id": "upper_middle",
        "label": "Upper-Middle Class",
        "desc": "Your parents are professionals. Good neighborhood, good schools. They can cover some college costs — but expect you to stand on your own eventually.",
        "debt_modifier": 0.6,
        "resilience_bonus": -0.02,
        "starting_savings": 8000
    },
    {
        "id": "challenging",
        "label": "Challenging Circumstances",
        "desc": "Life hasn't been easy. You've worked since you were 14. You might be supporting family too. But hardship has made you scrappy and resourceful.",
        "debt_modifier": 1.5,
        "resilience_bonus": 0.08,
        "starting_savings": 200
    }
]

POST_HS_CHOICES = [
    {
        "id": "four_year",
        "icon": "🎓",
        "title": "4-Year University",
        "desc": "The traditional path. Take on loans, earn a degree, unlock higher-earning careers. Big investment in your future.",
        "tags": [["credentials", "blue"], ["debt risk", "red"], ["ceiling↑", "green"]],
        "debt_base": 38000,
        "years": 4,
        "salary_base": 58000,
        "salary_growth_bonus": 0.03,
        "has_college": True
    },
    {
        "id": "community_then_transfer",
        "icon": "🏫",
        "title": "Community College → Transfer",
        "desc": "Start at community college for 2 years ($8K), transfer to state school. A smart, cost-effective path to a 4-year degree.",
        "tags": [["smart savings", "green"], ["longer path", "amber"], ["degree", "blue"]],
        "debt_base": 18000,
        "years": 4,
        "salary_base": 54000,
        "salary_growth_bonus": 0.025,
        "has_college": True
    },
    {
        "id": "trade_school",
        "icon": "🔧",
        "title": "Trade / Vocational School",
        "desc": "Electrician, plumber, HVAC, welding. 2 years, minimal debt, immediate solid income. More stable than people think.",
        "tags": [["low debt", "green"], ["job security", "blue"], ["immediate income", "green"]],
        "debt_base": 8000,
        "years": 2,
        "salary_base": 52000,
        "salary_growth_bonus": 0.018,
        "has_college": False
    },
    {
        "id": "work_immediately",
        "icon": "💼",
        "title": "Enter the Workforce",
        "desc": "Skip school entirely. Start earning now, avoid debt. Harder path to advancement without credentials, but you'll have a head start on savings.",
        "tags": [["no debt", "green"], ["limited ceiling", "amber"], ["head start", "blue"]],
        "debt_base": 0,
        "years": 0,
        "salary_base": 36000,
        "salary_growth_bonus": 0.01,
        "has_college": False
    },
    {
        "id": "military",
        "icon": "🎖️",
        "title": "Military Service",
        "desc": "Serve your country for 4 years. Free housing, food, training, GI Bill for college after. Demanding — but you'll come out ahead financially.",
        "tags": [["GI Bill", "green"], ["discipline", "blue"], ["risk", "red"]],
        "debt_base": 0,
        "years": 4,
        "salary_base": 42000,
        "salary_growth_bonus": 0.022,
        "has_college": True  # GI Bill = college after
    }
]

CAREER_CHOICES = [
    {
        "id": "bigtech",
        "icon": "💻",
        "title": "Big Tech Job",
        "desc": "$85–95K salary at a large tech company. High pressure, long hours, but strong comp and rapid career growth.",
        "tags": [["income↑", "green"], ["stress↑", "red"], ["growth↑", "blue"]],
        "salary": 90000,
        "stress": 7,
        "stress_start": 7,
        "growth": 9,
        "requires_college": True,
        "trait_bonus": "income_ceiling",
        "trait_desc": "Strong stock comp and rapid promotions can 2-3x your salary within 5 years."
    },
    {
        "id": "nonprofit",
        "icon": "🌱",
        "title": "Nonprofit / Public Service",
        "desc": "$42K at a mission-driven org. Meaningful work and PSLF loan forgiveness eligibility after 10 years.",
        "tags": [["fulfillment↑", "green"], ["forgiveness", "blue"], ["income↓", "amber"]],
        "salary": 42000,
        "stress": 4,
        "stress_start": 4,
        "growth": 5,
        "requires_college": False,
        "trait_bonus": "social_impact",
        "trait_desc": "PSLF eligibility can erase tens of thousands in student debt after 10 years of payments."
    },
    {
        "id": "startup",
        "icon": "🚀",
        "title": "Early-Stage Startup",
        "desc": "$65K + equity. Risky but with real upside potential. 60% chance the company succeeds.",
        "tags": [["equity", "green"], ["risk↑", "red"], ["learning↑", "blue"]],
        "salary": 65000,
        "stress": 8,
        "stress_start": 8,
        "growth": 8,
        "requires_college": False,
        "trait_bonus": "networking",
        "trait_desc": "Startup alumni networks open doors that résumés alone never could."
    },
    {
        "id": "skilled_trade_career",
        "icon": "🔧",
        "title": "Master Your Trade",
        "desc": "Run your own plumbing/electrical/HVAC business after years of experience. Great income ceiling for non-college paths.",
        "tags": [["own boss", "green"], ["stable", "blue"], ["physical", "amber"]],
        "salary": 58000,
        "stress": 5,
        "stress_start": 5,
        "growth": 6,
        "requires_college": False,
        "trait_bonus": "autonomy",
        "trait_desc": "Business ownership means no income ceiling — your hustle sets your pay."
    },
    {
        "id": "sales",
        "icon": "📊",
        "title": "Sales / Real Estate",
        "desc": "Commission-based. Base $45K + unlimited upside. High variance — great years and rough years.",
        "tags": [["upside", "green"], ["variable income", "amber"], ["hustle", "blue"]],
        "salary": 62000,
        "stress": 6,
        "stress_start": 6,
        "growth": 7,
        "requires_college": False,
        "trait_bonus": "flexibility",
        "trait_desc": "Set your own hours — top performers can earn $150K+ with the right market."
    },
    {
        "id": "healthcare",
        "icon": "🏥",
        "title": "Healthcare Worker",
        "desc": "Nursing, PA, or allied health. Strong demand, good pay, meaningful work. Requires specific schooling.",
        "tags": [["job security", "green"], ["meaningful", "blue"], ["demanding", "red"]],
        "salary": 72000,
        "stress": 7,
        "stress_start": 7,
        "growth": 7,
        "requires_college": True,
        "trait_bonus": "stability",
        "trait_desc": "Healthcare demand is recession-proof — layoffs are nearly unheard of."
    }
]

HOUSING_CHOICES = [
    {
        "id": "rent_city",
        "icon": "🏙️",
        "title": "Rent in the City",
        "desc": "$1,800/mo for a 1BR. Close to work and social life, but expensive.",
        "tags": [["convenience", "blue"], ["high cost", "red"]],
        "rent": 1800,
        "savings_mod": -0.15,
        "equity": 0
    },
    {
        "id": "buy_house",
        "icon": "🏠",
        "title": "Buy with Roommate",
        "desc": "Split a starter home. $2,200/mo mortgage total ($1,100 each). Builds equity but illiquid.",
        "tags": [["equity", "green"], ["illiquid", "amber"], ["risk", "red"]],
        "rent": 1100,
        "savings_mod": 0.05,
        "equity": 120000
    },
    {
        "id": "rent_cheap",
        "icon": "🏘️",
        "title": "Cheap Suburban Rental",
        "desc": "$950/mo with roommates. Long commute, but frees up significant monthly cash.",
        "tags": [["savings↑", "green"], ["commute", "red"]],
        "rent": 950,
        "savings_mod": 0.20,
        "equity": 0
    },
    {
        "id": "family",
        "icon": "👨‍👩‍👧",
        "title": "Move Back Home",
        "desc": "$300/mo to family. Maximum savings potential with some social tradeoffs.",
        "tags": [["max savings", "green"], ["social↓", "amber"]],
        "rent": 300,
        "savings_mod": 0.35,
        "equity": 0
    }
]

DEBT_CHOICES = [
    {
        "id": "minimum",
        "icon": "🐢",
        "title": "Minimum Payments",
        "desc": "Pay the minimum (~$380/mo). Keep cash free for investing and life. Loans paid off in ~10 years.",
        "tags": [["cash flow", "green"], ["interest↑", "red"]],
        "debt_payment": 380,
        "debt_years": 10,
        "invest_mod": 1.0
    },
    {
        "id": "aggressive",
        "icon": "💪",
        "title": "Aggressive Payoff",
        "desc": "Pay $1,200/mo. Debt-free in ~3 years, then redirect everything to investing.",
        "tags": [["debt-free", "green"], ["cash-poor", "red"]],
        "debt_payment": 1200,
        "debt_years": 3,
        "invest_mod": 0.4
    },
    {
        "id": "refinance",
        "icon": "🔄",
        "title": "Refinance + Balance",
        "desc": "Refinance to 4.5% rate, pay $600/mo. A middle path between speed and flexibility.",
        "tags": [["lower rate", "green"], ["balanced", "blue"]],
        "debt_payment": 600,
        "debt_years": 7,
        "invest_mod": 0.7
    },
    {
        "id": "forgiveness",
        "icon": "🎁",
        "title": "Pursue Forgiveness",
        "desc": "Income-driven plan (~$180/mo). Aim for PSLF if at nonprofit. Long game — potentially powerful.",
        "tags": [["low payments", "green"], ["risky", "amber"], ["long term", "blue"]],
        "debt_payment": 180,
        "debt_years": 20,
        "invest_mod": 1.2
    }
]

LIFESTYLE_CHOICES = [
    {
        "id": "lifestyle_up",
        "icon": "✈️",
        "title": "Upgrade Your Lifestyle",
        "desc": "New car, nicer apartment, travel twice a year. Enjoy the fruits of your hard work now.",
        "tags": [["enjoyment", "green"], ["savings↓", "red"]],
        "lifestyle_cost": 1500,
        "savings_rate_boost": -0.03,
        "side_income": 0
    },
    {
        "id": "invest_first",
        "icon": "📈",
        "title": "Invest Most of the Raise",
        "desc": "Keep lifestyle flat, funnel 80% of raise into index funds and max out 401k contributions.",
        "tags": [["wealth↑", "green"], ["discipline", "blue"]],
        "lifestyle_cost": 300,
        "savings_rate_boost": 0.12,
        "side_income": 0
    },
    {
        "id": "balanced_life",
        "icon": "⚖️",
        "title": "Balance It Out",
        "desc": "50/50 split: half the raise to lifestyle improvements, half to savings. A sustainable middle path.",
        "tags": [["balance", "blue"], ["steady", "green"]],
        "lifestyle_cost": 700,
        "savings_rate_boost": 0.06,
        "side_income": 0
    },
    {
        "id": "side_hustle",
        "icon": "💡",
        "title": "Start a Side Hustle",
        "desc": "Launch freelance work or a small business. Extra $15K/yr potential, but ~15 hrs/week.",
        "tags": [["income+", "green"], ["time↓", "red"], ["optionality", "blue"]],
        "lifestyle_cost": 400,
        "savings_rate_boost": 0.15,
        "side_income": 15000
    }
]

EMERGENCY_CHOICES = [
    {
        "id": "prepared",
        "icon": "🛡️",
        "title": "Use the Emergency Fund",
        "desc": "You have 6 months of expenses saved. Bridge the gap without touching investments.",
        "tags": [["resilient", "green"], ["prepared", "blue"]],
        "emergency_cost": 0,
        "stress_event": False
    },
    {
        "id": "credit",
        "icon": "💳",
        "title": "Put It on Credit Cards",
        "desc": "Charge $8,000 at 22% APR. Takes 18 months to pay off. Significant but recoverable.",
        "tags": [["quick fix", "amber"], ["debt+", "red"]],
        "emergency_cost": 8000,
        "stress_event": True
    },
    {
        "id": "withdraw_401k",
        "icon": "📉",
        "title": "Withdraw from 401k",
        "desc": "Pull $12K early. 10% penalty + income tax + lose years of compound growth.",
        "tags": [["available", "amber"], ["costly", "red"], ["penalty", "red"]],
        "emergency_cost": 16000,
        "stress_event": True
    },
    {
        "id": "family_loan",
        "icon": "🤝",
        "title": "Borrow from Family",
        "desc": "Interest-free loan from family. Paid back over 2 years. Some relational tension.",
        "tags": [["low cost", "green"], ["relational", "amber"]],
        "emergency_cost": 2000,
        "stress_event": False
    }
]

# ─── CAREER THEME POOLS for varied Gemini prompts ──────────────────────────────

# Each call picks a random theme cluster to keep jobs fresh across playthroughs
CAREER_THEME_CLUSTERS = [
    {
        "label": "creative and media industries",
        "examples": "graphic designer, podcast producer, video editor, UX researcher, copywriter, museum curator, sound engineer, art director, motion graphics artist, book editor"
    },
    {
        "label": "skilled trades and blue-collar",
        "examples": "union electrician, commercial diver, elevator mechanic, boilermaker, sheet metal worker, industrial painter, locomotive engineer, pipeline inspector, crane operator, millwright"
    },
    {
        "label": "government, legal, and civic",
        "examples": "paralegal, court reporter, city planner, customs officer, postal inspector, public defender, legislative aide, municipal auditor, immigration officer, probation officer"
    },
    {
        "label": "healthcare and life sciences",
        "examples": "dental hygienist, radiologic technologist, EMT, medical coder, clinical researcher, optician, occupational therapist, phlebotomist, health educator, surgical tech"
    },
    {
        "label": "tech-adjacent and emerging fields",
        "examples": "data annotator, cybersecurity analyst, drone operator, AR/VR developer, technical writer, IT support specialist, cloud systems admin, SEO specialist, QA tester, database administrator"
    },
    {
        "label": "hospitality, food, and service industries",
        "examples": "executive chef, hotel manager, sommelier, food scientist, event coordinator, wedding planner, catering manager, cruise director, personal trainer, spa director"
    },
    {
        "label": "finance, insurance, and real estate",
        "examples": "actuary, claims adjuster, mortgage broker, title examiner, financial planner, insurance underwriter, tax preparer, bank examiner, escrow officer, credit analyst"
    },
    {
        "label": "nature, agriculture, and outdoors",
        "examples": "park ranger, wildlife biologist, hydrologist, arborist, soil scientist, fish hatchery manager, wildfire analyst, marine biologist, agricultural inspector, conservation officer"
    },
    {
        "label": "transportation and logistics",
        "examples": "air traffic controller, freight broker, maritime officer, supply chain analyst, dispatch operator, railroad conductor, logistics coordinator, port inspector, cargo pilot, long-haul trucker"
    },
    {
        "label": "education and social services",
        "examples": "school counselor, special education teacher, librarian, social worker, speech-language pathologist, career coach, youth program director, child welfare specialist, ESL teacher, community organizer"
    },
]

# ─── GEMINI GENERATION ─────────────────────────────────────────────────────────

def generate_all_scenarios(char_name, char_bg, post_hs_path, career_choice):
    """Generate all AI content upfront to avoid rate limits during gameplay."""
    
    context = f"""
Character: {char_name}
Background: {char_bg['label']} - {char_bg['desc']}
Post-high school path: {post_hs_path['title']} - {post_hs_path['desc']}
Career: {career_choice['title']} - {career_choice['desc']}
"""

    prompt = f"""You are writing for an interactive financial planning game called "Life Simulator". 
The player's character is:
{context}

Generate 15 annual life events (ages 18-32 roughly, one per year) that create emotional storytelling AND financial impact. 
Each event should be personal, specific to this character, and feel real.

Some should be positive (bonus, promotion, unexpected windfall, new relationship milestone), some negative (medical bill, car breakdown, recession impact, job change), some neutral but thought-provoking.

IMPORTANT: Make them feel like a real person's life story, not generic financial advice. Include personal details, relationships, emotions.

Respond with ONLY a JSON array, no markdown, no explanation:
[
  {{
    "age": 19,
    "title": "Short punchy title",
    "story": "2-3 sentences describing what happened in first person or close third person. Make it vivid and personal.",
    "financial_impact": 1500,
    "impact_type": "one_time_gain",
    "emoji": "🎉"
  }}
]

impact_type options: "one_time_gain", "one_time_loss", "monthly_income_boost", "monthly_expense", "savings_rate_change", "investment_multiplier"
financial_impact: positive number representing the magnitude (dollar amount or percentage * 100 for rates)

Make it emotionally compelling! Ages should span 18-37 and vary the types of events."""

    result = call_gemini(prompt, max_tokens=3000)
    
    scenarios = []
    if result:
        try:
            # Strip any markdown fencing
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean[clean.find("["):clean.rfind("]")+1]
            scenarios = json.loads(clean)
        except Exception as e:
            print(f"JSON parse error: {e}")
            scenarios = []
    
    # Fallback scenarios if Gemini fails
    if not scenarios:
        scenarios = get_fallback_scenarios(char_name)
    
    return scenarios[:15]  # cap at 15


def generate_gemini_choices(char_profile, all_choices):
    """Have Gemini make all game choices at once for Beat Gemini mode."""
    
    prompt = f"""You are playing a financial planning game as an AI advisor. 
Character profile: {json.dumps(char_profile, indent=2)}

You must make the following decisions to maximize the character's financial score (net worth at age 37, savings rate, debt management).

Available choices for each decision:

POST HIGH SCHOOL PATH:
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "debt_base": c["debt_base"], "salary_base": c["salary_base"]} for c in POST_HS_CHOICES], indent=2)}

CAREER:
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "salary": c["salary"], "growth": c["growth"]} for c in CAREER_CHOICES], indent=2)}

HOUSING:
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "rent": c["rent"], "savings_mod": c["savings_mod"], "equity": c["equity"]} for c in HOUSING_CHOICES], indent=2)}

DEBT STRATEGY (only relevant if character has debt):
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "debt_payment": c["debt_payment"], "debt_years": c["debt_years"], "invest_mod": c["invest_mod"]} for c in DEBT_CHOICES], indent=2)}

LIFESTYLE:
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "savings_rate_boost": c["savings_rate_boost"], "side_income": c.get("side_income", 0)} for c in LIFESTYLE_CHOICES], indent=2)}

EMERGENCY:
{json.dumps([{"id": c["id"], "title": c["title"], "desc": c["desc"], "emergency_cost": c["emergency_cost"]} for c in EMERGENCY_CHOICES], indent=2)}

Think strategically about long-term wealth building. Consider: compound interest, debt costs vs investment returns, housing equity, income growth.

Respond with ONLY a JSON object:
{{
  "post_hs": "choice_id",
  "career": "choice_id", 
  "housing": "choice_id",
  "debt": "choice_id",
  "lifestyle": "choice_id",
  "emergency": "choice_id",
  "reasoning": "2-3 sentences explaining your overall strategy"
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
    
    # Fallback: Gemini makes reasonable choices
    return {
        "post_hs": "four_year",
        "career": "bigtech",
        "housing": "rent_cheap",
        "debt": "refinance",
        "lifestyle": "invest_first",
        "emergency": "prepared",
        "reasoning": "Prioritizing high income, low housing costs, and disciplined investing for maximum compound growth."
    }


BACKSTORY_FALLBACKS = {
    "working_class": "You grew up watching your parents stretch every dollar. You learned early that nothing comes free — you've been hustling since you were old enough to mow lawns. School was something you fit in between shifts. Now at 18, you're the first in your family who gets to choose what comes next.",
    "middle_class": "You grew up in a comfortable house in a decent neighborhood — not rich, but never really worried about rent either. Your parents worked hard and expected you to do the same. You've had opportunities, and now it's on you to actually use them.",
    "upper_middle": "Your parents are professionals who gave you every advantage — good schools, SAT prep, family vacations. You've never had to think much about money. That might be your biggest blind spot. Now the training wheels come off.",
    "challenging": "Life has thrown everything at you and you're still standing. You've been working since 14, sometimes to help your family make rent. Hardship has made you scrappy in ways your peers can't understand. You're starting behind — but you're also starting hungry.",
}

def generate_character_backstory(name, hometown, background):
    """Generate a short personal backstory for emotional connection."""
    prompt = f"""Write a SHORT (3-4 sentences) personal backstory for {name} from {hometown} 
with a {background['label']} background: "{background['desc']}"

Make it feel real and emotionally resonant. Mention one specific memory or detail that defines them.
Write in second person ("You grew up..."). 
Keep it under 80 words. No lists. Just a short paragraph."""
    
    result = call_gemini(prompt, max_tokens=200)
    if result:
        return result.strip()
    fallback = BACKSTORY_FALLBACKS.get(background["id"], "")
    if not fallback:
        fallback = f"You grew up in {hometown}, shaped by your {background['label'].lower()} upbringing. Every dollar has taught you something. Now at 18, the whole future is open."
    return fallback


def get_fallback_scenarios(char_name):
    return [
        {"age": 19, "title": "Unexpected Medical Bill", "story": f"{char_name} got a nasty infection that required a trip to urgent care. No insurance meant paying out of pocket.", "financial_impact": 1200, "impact_type": "one_time_loss", "emoji": "🏥"},
        {"age": 20, "title": "Summer Job Bonus", "story": "The manager loved your work ethic and slipped you a cash bonus at the end of the summer.", "financial_impact": 800, "impact_type": "one_time_gain", "emoji": "💵"},
        {"age": 21, "title": "Car Breakdown", "story": "Your old car finally gave out on the highway. You needed reliable transportation for work.", "financial_impact": 3000, "impact_type": "one_time_loss", "emoji": "🚗"},
        {"age": 22, "title": "Freelance Gig", "story": "A friend connected you with a freelance project that turned into recurring monthly income.", "financial_impact": 500, "impact_type": "monthly_income_boost", "emoji": "💻"},
        {"age": 23, "title": "Stock Market Dip", "story": "The market dropped 20% and you watched your early investments decline. You held firm.", "financial_impact": 80, "impact_type": "investment_multiplier", "emoji": "📉"},
        {"age": 24, "title": "Promotion!", "story": "Your hard work paid off. Your boss called you in and offered a significant raise.", "financial_impact": 8000, "impact_type": "one_time_gain", "emoji": "🎉"},
        {"age": 25, "title": "Lease Hike", "story": "Your landlord raised rent by $300/month. You had to decide whether to move or absorb the cost.", "financial_impact": 300, "impact_type": "monthly_expense", "emoji": "🏠"},
        {"age": 26, "title": "Family Emergency", "story": "A family member needed financial help. You stepped up — because that's who you are.", "financial_impact": 4000, "impact_type": "one_time_loss", "emoji": "❤️"},
        {"age": 27, "title": "Investment Win", "story": "That index fund you've been contributing to had a remarkable year. Your portfolio surged.", "financial_impact": 115, "impact_type": "investment_multiplier", "emoji": "📈"},
        {"age": 28, "title": "Conference & Networking", "story": "You invested in a professional conference and landed a higher-paying consulting contract.", "financial_impact": 6000, "impact_type": "one_time_gain", "emoji": "🤝"},
        {"age": 29, "title": "Tax Surprise", "story": "A freelance project meant you owed more taxes than expected. The IRS is unforgiving.", "financial_impact": 2200, "impact_type": "one_time_loss", "emoji": "📋"},
        {"age": 30, "title": "Side Hustle Takeoff", "story": "That side project you've been building quietly started generating real, consistent revenue.", "financial_impact": 1000, "impact_type": "monthly_income_boost", "emoji": "🚀"},
        {"age": 31, "title": "Market Recovery", "story": "After years of steady investing through ups and downs, compound interest began to really show.", "financial_impact": 112, "impact_type": "investment_multiplier", "emoji": "💹"},
        {"age": 32, "title": "Apartment Flooding", "story": "A burst pipe damaged your belongings. Renters insurance covered some, but not all.", "financial_impact": 1800, "impact_type": "one_time_loss", "emoji": "🌊"},
        {"age": 33, "title": "Industry Recognition", "story": "You were featured in an industry publication. New clients found you. Income jumped.", "financial_impact": 12000, "impact_type": "one_time_gain", "emoji": "⭐"},
    ]


# ─── FALLBACK JOB POOLS ────────────────────────────────────────────────────────
# Large pool of diverse fallback jobs used when Gemini is unavailable.
# Each playthrough randomly samples 6 from this list, ensuring variety.

FALLBACK_JOB_POOL = [
    {"id": "park_ranger", "icon": "🌲", "title": "Park Ranger", "desc": "$48K managing public lands. Outdoors every day, but remote postings and physical demands.", "tags": [["outdoors", "green"], ["stable", "blue"], ["remote", "amber"]], "salary": 48000, "stress_start": 4, "growth": 4, "requires_college": False, "trait_bonus": "autonomy", "trait_desc": "Federal job security means near-impossible layoffs and full pension after 20 years."},
    {"id": "court_reporter", "icon": "📜", "title": "Court Reporter", "desc": "$62K transcribing legal proceedings. High accuracy required, but strong freelance upside.", "tags": [["niche skill", "blue"], ["freelance", "green"], ["quiet", "amber"]], "salary": 62000, "stress_start": 5, "growth": 5, "requires_college": False, "trait_bonus": "flexibility", "trait_desc": "Certified reporters can freelance depositions for $150+/hr on top of salaried work."},
    {"id": "actuary", "icon": "📐", "title": "Actuary", "desc": "$95K analyzing risk for insurance firms. Demanding exams, but elite earning ceiling.", "tags": [["income↑↑", "green"], ["exams", "red"], ["prestige", "blue"]], "salary": 95000, "stress_start": 6, "growth": 9, "requires_college": True, "trait_bonus": "income_ceiling", "trait_desc": "Passing all 10 actuarial exams unlocks $200K+ salaries at senior levels."},
    {"id": "ux_researcher", "icon": "🔍", "title": "UX Researcher", "desc": "$78K studying how people use products. Remote-friendly and growing fast.", "tags": [["remote", "green"], ["creative", "blue"], ["growing", "green"]], "salary": 78000, "stress_start": 5, "growth": 8, "requires_college": True, "trait_bonus": "remote_work", "trait_desc": "90% of UX roles are fully remote — skip commuting forever."},
    {"id": "elevator_mechanic", "icon": "🛗", "title": "Elevator Mechanic", "desc": "$88K installing and maintaining elevators. Union job with exceptional overtime potential.", "tags": [["union", "green"], ["overtime↑", "green"], ["physical", "amber"]], "salary": 88000, "stress_start": 5, "growth": 5, "requires_college": False, "trait_bonus": "stability", "trait_desc": "Union contracts guarantee overtime rates — many mechanics clear $120K+ annually."},
    {"id": "air_traffic_controller", "icon": "✈️", "title": "Air Traffic Controller", "desc": "$120K guiding aircraft. Extremely high stress, but one of the best-compensated federal jobs.", "tags": [["income↑↑", "green"], ["stress↑↑", "red"], ["federal", "blue"]], "salary": 120000, "stress_start": 10, "growth": 6, "requires_college": False, "trait_bonus": "income_ceiling", "trait_desc": "Federal pension plus mandatory retirement at 56 means a defined, early finish line."},
    {"id": "dental_hygienist", "icon": "🦷", "title": "Dental Hygienist", "desc": "$76K cleaning teeth and educating patients. Part-time flexibility and recession-proof demand.", "tags": [["stable", "green"], ["flexible hours", "blue"], ["people", "amber"]], "salary": 76000, "stress_start": 4, "growth": 5, "requires_college": False, "trait_bonus": "flexibility", "trait_desc": "Part-time is common — many hygienists work 3 days a week for full-time pay."},
    {"id": "supply_chain_analyst", "icon": "📦", "title": "Supply Chain Analyst", "desc": "$68K optimizing logistics for manufacturers or retailers. Desk job with solid growth trajectory.", "tags": [["growing field", "green"], ["analytical", "blue"], ["desk job", "amber"]], "salary": 68000, "stress_start": 5, "growth": 7, "requires_college": True, "trait_bonus": "networking", "trait_desc": "Supply chain certifications (APICS) can jump salary 20-30% overnight."},
    {"id": "wildlife_biologist", "icon": "🦅", "title": "Wildlife Biologist", "desc": "$55K studying animal populations for agencies or nonprofits. Meaningful but competitive.", "tags": [["meaningful", "green"], ["competitive", "red"], ["fieldwork", "blue"]], "salary": 55000, "stress_start": 4, "growth": 4, "requires_college": True, "trait_bonus": "social_impact", "trait_desc": "Grant-funded research roles can pay $80K+ with full benefits and remote fieldwork."},
    {"id": "industrial_welder", "icon": "🔥", "title": "Industrial Welder", "desc": "$58K welding pipelines, ships, and structures. Certification boosts pay fast — high overtime.", "tags": [["in demand", "green"], ["overtime↑", "green"], ["physical", "amber"]], "salary": 58000, "stress_start": 5, "growth": 6, "requires_college": False, "trait_bonus": "income_ceiling", "trait_desc": "Underwater welding and pipeline work can pay $150K+ for those willing to specialize."},
    {"id": "paralegal", "icon": "⚖️", "title": "Paralegal", "desc": "$52K supporting attorneys at law firms or corporations. Stepping stone or solid career.", "tags": [["stable", "blue"], ["detail-oriented", "green"], ["stepping stone", "amber"]], "salary": 52000, "stress_start": 6, "growth": 6, "requires_college": False, "trait_bonus": "networking", "trait_desc": "Many firms sponsor paralegal education — a pathway to law school tuition reimbursement."},
    {"id": "sound_engineer", "icon": "🎚️", "title": "Sound Engineer", "desc": "$54K mixing audio for studios, live events, or broadcasting. Creative with freelance upside.", "tags": [["creative", "green"], ["freelance", "blue"], ["variable", "amber"]], "salary": 54000, "stress_start": 5, "growth": 6, "requires_college": False, "trait_bonus": "flexibility", "trait_desc": "Top live event engineers earn $800–$2,000 per show day as independent contractors."},
    {"id": "claims_adjuster", "icon": "🏚️", "title": "Insurance Claims Adjuster", "desc": "$58K investigating and settling insurance claims. Remote-friendly with steady caseloads.", "tags": [["remote", "green"], ["stable", "blue"], ["negotiation", "amber"]], "salary": 58000, "stress_start": 5, "growth": 6, "requires_college": False, "trait_bonus": "remote_work", "trait_desc": "Catastrophe adjusters deployed after storms can earn $100K+ in a single busy season."},
    {"id": "urban_planner", "icon": "🏙️", "title": "Urban Planner", "desc": "$68K shaping city development for government agencies. Slow-moving but meaningful public work.", "tags": [["civic", "green"], ["stable", "blue"], ["slow growth", "amber"]], "salary": 68000, "stress_start": 4, "growth": 5, "requires_college": True, "trait_bonus": "social_impact", "trait_desc": "Government pension and PSLF eligibility make this deceptively lucrative long-term."},
    {"id": "radiologic_tech", "icon": "🩻", "title": "Radiologic Technologist", "desc": "$66K operating MRI/X-ray equipment. In-demand healthcare role with predictable hours.", "tags": [["healthcare", "green"], ["in demand", "blue"], ["technical", "amber"]], "salary": 66000, "stress_start": 5, "growth": 6, "requires_college": False, "trait_bonus": "stability", "trait_desc": "Specializing in MRI or CT adds $10–20K — certifications take just a few months."},
    {"id": "freight_broker", "icon": "🚛", "title": "Freight Broker", "desc": "$60K base + commission connecting shippers with carriers. High hustle, high ceiling.", "tags": [["commission", "green"], ["hustle", "blue"], ["variable", "amber"]], "salary": 60000, "stress_start": 7, "growth": 7, "requires_college": False, "trait_bonus": "income_ceiling", "trait_desc": "Top freight brokers build their own agencies and earn $300K+ in their 30s."},
    {"id": "librarian", "icon": "📚", "title": "Librarian", "desc": "$52K managing collections and community programs. Underrated job security and PSLF eligible.", "tags": [["PSLF eligible", "green"], ["quiet", "blue"], ["meaningful", "amber"]], "salary": 52000, "stress_start": 3, "growth": 4, "requires_college": True, "trait_bonus": "stability", "trait_desc": "Most library positions carry full benefits and are PSLF eligible — debt forgiveness in 10 years."},
    {"id": "executive_chef", "icon": "👨‍🍳", "title": "Executive Chef", "desc": "$65K running a restaurant kitchen. Creative and intense — brutal hours, high satisfaction.", "tags": [["creative", "green"], ["intense hours", "red"], ["prestige", "blue"]], "salary": 65000, "stress_start": 9, "growth": 6, "requires_college": False, "trait_bonus": "autonomy", "trait_desc": "Restaurant ownership opens a path to $200K+ — but comes with real financial risk."},
    {"id": "cybersecurity_analyst", "icon": "🔐", "title": "Cybersecurity Analyst", "desc": "$82K protecting systems from attacks. Exploding demand and almost no unemployment.", "tags": [["in demand↑↑", "green"], ["remote", "green"], ["technical", "blue"]], "salary": 82000, "stress_start": 6, "growth": 9, "requires_college": False, "trait_bonus": "income_ceiling", "trait_desc": "CISSP certification alone can add $30K — and there are more openings than candidates."},
    {"id": "mortgage_broker", "icon": "🏦", "title": "Mortgage Broker", "desc": "$70K + commission helping people finance homes. Income swings with housing market cycles.", "tags": [["commission", "green"], ["market-sensitive", "amber"], ["people", "blue"]], "salary": 70000, "stress_start": 6, "growth": 7, "requires_college": False, "trait_bonus": "networking", "trait_desc": "A strong referral network can make income nearly recession-proof even in slow markets."},
    {"id": "drone_operator", "icon": "🚁", "title": "Drone Operator", "desc": "$55K flying commercial drones for mapping, inspection, or media. Fast-growing niche.", "tags": [["growing", "green"], ["flexible", "blue"], ["outdoor", "amber"]], "salary": 55000, "stress_start": 4, "growth": 8, "requires_college": False, "trait_bonus": "flexibility", "trait_desc": "FAA Part 107 license takes 2 weeks — opens $150/hr freelance gigs immediately."},
    {"id": "speech_pathologist", "icon": "🗣️", "title": "Speech-Language Pathologist", "desc": "$78K helping patients communicate. Strong demand in schools and healthcare — PSLF eligible.", "tags": [["meaningful", "green"], ["PSLF", "blue"], ["stable", "green"]], "salary": 78000, "stress_start": 5, "growth": 6, "requires_college": True, "trait_bonus": "social_impact", "trait_desc": "School SLPs get summers off and full PSLF eligibility — a hidden gem of work-life balance."},
    {"id": "boilermaker", "icon": "⚙️", "title": "Boilermaker", "desc": "$72K building and repairing pressure systems. Union job with serious overtime during outages.", "tags": [["union", "green"], ["overtime↑", "green"], ["physical", "red"]], "salary": 72000, "stress_start": 6, "growth": 5, "requires_college": False, "trait_bonus": "stability", "trait_desc": "Nuclear and power plant shutdowns require boilermakers around the clock — overtime is massive."},
    {"id": "technical_writer", "icon": "✍️", "title": "Technical Writer", "desc": "$70K creating docs and manuals for software and engineering firms. Remote-first and chill.", "tags": [["remote", "green"], ["writing", "blue"], ["low stress", "green"]], "salary": 70000, "stress_start": 3, "growth": 6, "requires_college": True, "trait_bonus": "remote_work", "trait_desc": "One of the most remote-compatible careers — nearly all positions are fully work-from-home."},
    {"id": "event_coordinator", "icon": "🎪", "title": "Event Coordinator", "desc": "$48K organizing conferences and weddings. Chaotic but social — unpredictable hours.", "tags": [["social", "green"], ["irregular hours", "red"], ["creative", "blue"]], "salary": 48000, "stress_start": 7, "growth": 6, "requires_college": False, "trait_bonus": "networking", "trait_desc": "Top event planners build referral networks that generate $100K+ in independent bookings."},
    {"id": "qa_tester", "icon": "🐛", "title": "QA / Software Tester", "desc": "$58K finding bugs in software products. No coding required — gateway into tech.", "tags": [["tech adjacent", "blue"], ["entry accessible", "green"], ["methodical", "amber"]], "salary": 58000, "stress_start": 4, "growth": 7, "requires_college": False, "trait_bonus": "networking", "trait_desc": "Many QA testers transition into dev or product roles — a foot in the tech door."},
]


# ─── SIMULATION ENGINE ─────────────────────────────────────────────────────────

def compute_results(selections, scenarios=None):
    """Compute financial results based on selections and AI scenarios."""
    
    post_hs = next(c for c in POST_HS_CHOICES if c["id"] == selections["post_hs"])
    career = next((c for c in CAREER_CHOICES if c["id"] == selections["career"]), None)
    
    # Career might be an AI-generated job not in CAREER_CHOICES — use selections directly
    if career is None:
        career = {
            "salary": selections.get("career_salary", 60000),
            "growth": selections.get("career_growth", 6),
            "id": selections["career"]
        }
    
    housing = next(c for c in HOUSING_CHOICES if c["id"] == selections["housing"])
    debt = next(c for c in DEBT_CHOICES if c["id"] == selections["debt"])
    lifestyle = next(c for c in LIFESTYLE_CHOICES if c["id"] == selections["lifestyle"])
    emergency = next(c for c in EMERGENCY_CHOICES if c["id"] == selections["emergency"])
    bg = next(b for b in FAMILY_BACKGROUNDS if b["id"] == selections.get("background", "middle_class"))
    
    # Starting values
    student_debt = post_hs["debt_base"] * bg["debt_modifier"]
    if selections["debt"] == "forgiveness" and selections["career"] == "nonprofit":
        student_debt = 0
    
    base_age = 18 + post_hs["years"]  # age when career starts
    salary = career["salary"] * (1 + post_hs.get("salary_growth_bonus", 0) * post_hs["years"])
    salary_growth = career["growth"] * 0.01 + 0.02
    side_income = lifestyle.get("side_income", 0)
    
    debt_payment = debt["debt_payment"] if student_debt > 0 else 0
    debt_years = min(debt["debt_years"], 10) if student_debt > 0 else 0
    invest_mod = debt["invest_mod"]
    savings_boost = lifestyle["savings_rate_boost"]
    savings_mod = housing["savings_mod"] + bg["resilience_bonus"]
    emergency_cost = emergency["emergency_cost"]
    house_equity = housing.get("equity", 0)
    
    savings_rate = max(0.03, min(0.45, 0.10 + savings_boost + savings_mod))
    
    # Simulation: 19 years from age 18 to 37
    net_worth_by_year = []
    investments = bg["starting_savings"]
    remaining_debt = float(student_debt)
    current_salary = float(salary) * 0.6  # lower during school/training years
    
    # Pre-career years (18 to base_age)
    for age in range(18, base_age + 1):
        nw = investments - remaining_debt
        net_worth_by_year.append({"age": age, "nw": round(nw)})
    
    current_salary = float(salary)
    
    scenario_impacts = {}  # age -> financial impact
    if scenarios:
        for s in scenarios:
            if "age" in s and "financial_impact" in s:
                scenario_impacts[s["age"]] = s
    
    for yr in range(1, 38 - base_age + 1):
        age = base_age + yr
        if age > 37:
            break
        current_salary *= (1 + salary_growth)
        annual_income = current_salary + side_income
        annual_savings = annual_income * savings_rate * invest_mod
        annual_debt_pay = debt_payment * 12 if yr <= debt_years else 0
        remaining_debt = max(0, remaining_debt - annual_debt_pay)
        investments = (investments + max(0, annual_savings)) * 1.07
        
        # Apply scenario impacts
        if age in scenario_impacts:
            sc = scenario_impacts[age]
            impact = sc["financial_impact"]
            itype = sc.get("impact_type", "one_time_loss")
            if itype == "one_time_gain":
                investments += impact
            elif itype == "one_time_loss":
                investments = max(0, investments - impact)
            elif itype == "monthly_income_boost":
                investments += impact * 12 * 0.6
            elif itype == "monthly_expense":
                investments = max(0, investments - impact * 12)
            elif itype == "investment_multiplier":
                investments *= (impact / 100)
            elif itype == "savings_rate_change":
                savings_rate = max(0.03, min(0.45, savings_rate + impact / 100))
        
        # Emergency event (around age 28-30)
        if age == 28:
            investments = max(0, investments - emergency_cost)
        
        equity_value = house_equity * (1 + 0.04 * yr) - house_equity if house_equity else 0
        nw = investments - remaining_debt + equity_value
        net_worth_by_year.append({"age": age, "nw": round(nw)})
    
    final_nw = net_worth_by_year[-1]["nw"] if net_worth_by_year else 0
    final_salary = round(current_salary + side_income)
    debt_free_age = base_age + debt_years if student_debt > 0 else base_age
    
    # Score calculation
    score = 50
    if final_nw > 300000: score += 25
    elif final_nw > 150000: score += 15
    elif final_nw > 50000: score += 5
    elif final_nw < 0: score -= 25
    if savings_rate > 0.20: score += 12
    elif savings_rate > 0.15: score += 7
    if emergency["stress_event"]: score -= 10
    if selections["housing"] in ("buy_house", "family"): score += 5
    if side_income > 0: score += 5
    if bg["id"] == "working_class" and final_nw > 100000: score += 10  # bonus for overcoming obstacles
    if bg["id"] == "challenging" and final_nw > 50000: score += 15
    score = max(10, min(99, score))
    
    # Build events timeline
    career_title = career.get("title", selections["career"])
    events = [
        {"age": 18, "icon": "🎓", "text": f"High school graduation. Chose: {post_hs['title']}."},
    ]
    if post_hs["has_college"]:
        events.append({"age": base_age, "icon": "🎓", "text": f"Completed education. Starting career as: {career_title}."})
    else:
        events.append({"age": base_age, "icon": "💼", "text": f"Entered workforce: {career_title}."})
    
    events.append({"age": base_age + 1, "icon": "🏠", "text": f"Housing: {housing['title']}. Monthly cost: ${housing['rent']:,}."})
    
    if student_debt > 0:
        events.append({"age": base_age + 2, "icon": "💸", "text": f"Debt strategy: {debt['title']} on ${int(student_debt):,}."})
    
    events.append({"age": base_age + 4, "icon": "💰", "text": f"Raise arrived. Choice: {lifestyle['title']}."})
    if side_income:
        events.append({"age": base_age + 5, "icon": "💡", "text": f"Side hustle generating ~${side_income//1000}K/yr."})
    
    events.append({"age": 28, "icon": "⚠️" if emergency["stress_event"] else "✅",
                   "text": f"Emergency hit. Response: {emergency['title']}. Cost: ${emergency_cost:,}."})
    
    if debt_free_age <= 37 and student_debt > 0:
        events.append({"age": debt_free_age, "icon": "🎉", "text": "Student loans fully paid off!"})
    
    events.append({"age": 37, "icon": "📊",
                   "text": f"Net worth reaches ${round(final_nw/1000)}K at age 37."})
    
    # Add notable scenario events
    if scenarios:
        for s in scenarios[:5]:  # add top 5 scenarios to timeline
            if s.get("age") and s["age"] not in [e["age"] for e in events]:
                events.append({
                    "age": s["age"],
                    "icon": s.get("emoji", "📌"),
                    "text": s["title"]
                })
    
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
        "student_debt": student_debt
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
        "emergency_choices": EMERGENCY_CHOICES
    })

@app.route("/api/generate-character", methods=["POST"])
def generate_character():
    """Generate a random character for random/beat gemini modes."""
    data = request.json or {}
    mode = data.get("mode", "random")
    
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
    """Generate all AI scenarios upfront."""
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
    """Generate Gemini's choices for Beat Gemini mode."""
    data = request.json
    char_profile = data.get("char_profile", {})
    gemini_choices = generate_gemini_choices(char_profile, {})
    return jsonify(gemini_choices)

@app.route("/api/gemini-event-choice", methods=["POST"])
def gemini_event_choice():
    """Have Gemini pick a choice for a single in-game event."""
    data = request.json or {}
    event_title = data.get("event_title", "")
    story = data.get("story", "")
    choices = data.get("choices", [])
    state = data.get("state", {})

    if not choices:
        return jsonify({"choice": None, "reasoning": "No choices available."})

    roll = random.random()

    # 15% chance: pure random pick
    if roll < 0.15:
        picked = random.choice(choices)
        return jsonify({"choice": picked["id"], "reasoning": "Sometimes you just go with your gut."})

    # 20% chance: pick the worst-looking option
    if roll < 0.35:
        def badness(c):
            score = 0
            if c.get("riskLevel") == "high": score += 3
            if c.get("riskLevel") == "med": score += 1
            ct = c.get("consequenceText", "")
            score += ct.count("-") * 2
            score -= ct.count("+") * 2
            return score
        worst = max(choices, key=badness)
        human_reasons = [
            "This feels like the bold move.",
            "Taking the risk — fortune favors the brave, right?",
            "Going with the exciting option here.",
            "Sometimes you have to bet on yourself.",
            "This looks too good to pass up.",
        ]
        return jsonify({"choice": worst["id"], "reasoning": random.choice(human_reasons)})

    # 65%: ask Gemini for the optimal choice
    choices_text = "\n".join(
        f"{i+1}. [{c['id']}] {c['title']}: {c['desc']} ({c.get('riskLevel','?')} risk) → {c.get('consequenceText','')}"
        for i, c in enumerate(choices)
    )

    prompt = f"""You are playing a financial life simulation game. Pick the BEST choice for long-term financial health.

Character state:
- Age: {state.get('age', '?')} | Salary: ${state.get('salary', 0):,}/yr | Net Worth: ${state.get('net_worth', 0):,}
- Savings: ${state.get('savings', 0):,} | Investments: ${state.get('investments', 0):,} | Debt: ${state.get('debt', 0):,}
- Health: {state.get('health', 80)}% | Stress: {state.get('stress', 50)}% | Happiness: {state.get('happiness', 70)}%

Event: "{event_title}"
{story}

Available choices:
{choices_text}

Think about long-term compound growth, debt burden, and risk management.
Respond ONLY with valid JSON (no markdown): {{"choice": "choice_id_here", "reasoning": "one concise sentence"}}"""

    result = call_gemini(prompt, max_tokens=200)

    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                start = clean.find("{")
                end = clean.rfind("}") + 1
                clean = clean[start:end]
            parsed = json.loads(clean)
            valid_ids = [c["id"] for c in choices]
            if parsed.get("choice") in valid_ids:
                return jsonify(parsed)
        except Exception as e:
            print(f"Gemini event choice parse error: {e}")

    fallback = next((c for c in choices if c.get("riskLevel") == "low"), choices[0])
    return jsonify({"choice": fallback["id"], "reasoning": "Chose the safest available option."})


@app.route("/api/generate-random-jobs", methods=["POST"])
def generate_random_jobs():
    """
    Generate a fresh, diverse set of 6 career options every playthrough.

    Strategy:
    1. Pick a random career theme cluster to guide Gemini toward a specific industry slice.
    2. Include a random seed phrase so Gemini doesn't cache/repeat a previous response.
    3. If Gemini fails or returns bad data, sample 6 from the large FALLBACK_JOB_POOL
       (which has 26 entries), so the fallback is also varied each time.
    """
    data = request.json or {}
    has_college = data.get("has_college", True)

    # Pick a random industry theme so each call is guided differently
    theme = random.choice(CAREER_THEME_CLUSTERS)
    seed_word = random.choice([
        "innovative", "underrated", "surprising", "diverse", "eclectic",
        "uncommon", "realistic", "gritty", "varied", "unexpected"
    ])

    prompt = f"""You are generating {seed_word} career options for a financial life simulation game.
Focus primarily on {theme['label']}.
Example careers in this space (do NOT use these exact titles — invent fresh variants or related roles):
{theme['examples']}

Create exactly 6 distinct careers. Mix college-required and non-college paths.
{"At least 3 must NOT require college since the player has no degree." if not has_college else "At least 2 should NOT require college for variety."}

Rules:
- Salary range: $34,000–$115,000 (realistic for that career)
- stress_start and growth: integers 1–10
- Make descriptions vivid and specific — mention actual dollar ranges and real tradeoffs
- trait_desc should reveal a non-obvious financial insight about this career

Respond ONLY with a JSON array, no markdown:
[
  {{
    "id": "unique_snake_case_id",
    "icon": "single emoji",
    "title": "Job Title",
    "desc": "One punchy sentence: salary range, key tradeoffs, personality fit.",
    "tags": [["trait1", "green|amber|red|blue"], ["trait2", "green|amber|red|blue"], ["trait3", "green|amber|red|blue"]],
    "salary": 65000,
    "stress_start": 6,
    "growth": 7,
    "requires_college": false,
    "trait_bonus": "one_word_trait",
    "trait_desc": "Non-obvious financial insight about this career."
  }}
]

trait_bonus options: stability, creativity, autonomy, prestige, flexibility, physicality, social_impact, income_ceiling, networking, remote_work"""

    result = call_gemini(prompt, max_tokens=1800)

    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean[clean.find("["):clean.rfind("]")+1]
            jobs = json.loads(clean)
            if isinstance(jobs, list) and len(jobs) >= 4:
                cleaned = []
                for j in jobs[:6]:
                    cleaned.append({
                        "id": str(j.get("id", f"job_{len(cleaned)}")),
                        "icon": str(j.get("icon", "💼")),
                        "title": str(j.get("title", "Professional")),
                        "desc": str(j.get("desc", "A professional career path.")),
                        "tags": j.get("tags", [["career", "blue"]]),
                        "salary": int(j.get("salary", 55000)),
                        "stress_start": max(1, min(10, int(j.get("stress_start", 5)))),
                        "growth": max(1, min(10, int(j.get("growth", 5)))),
                        "requires_college": bool(j.get("requires_college", False)),
                        "trait_bonus": str(j.get("trait_bonus", "stability")),
                        "trait_desc": str(j.get("trait_desc", "A steady career path.")),
                    })
                return jsonify({"jobs": cleaned, "source": "gemini", "theme": theme["label"]})
        except Exception as e:
            print(f"Random jobs parse error: {e}")

    # Fallback: sample 6 random jobs from the large pool — varied each time
    pool = FALLBACK_JOB_POOL.copy()
    if not has_college:
        # Prefer non-college jobs but fill remaining slots from full pool
        no_degree = [j for j in pool if not j["requires_college"]]
        with_degree = [j for j in pool if j["requires_college"]]
        random.shuffle(no_degree)
        random.shuffle(with_degree)
        fallback = (no_degree[:4] + with_degree[:2])[:6]
    else:
        random.shuffle(pool)
        fallback = pool[:6]

    return jsonify({"jobs": fallback, "source": "fallback", "theme": theme["label"]})


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
        data.get("mode", "standard"),
        data.get("game_length", "")
    )
    return jsonify({"scores": scores, "success": True})

if __name__ == "__main__":
    print("🎓 Life Simulator starting on http://localhost:5000")
    app.run(debug=True, port=5000)