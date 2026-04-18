#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          LIFE AFTER GRADUATION: THE FINANCIAL GAME           ║
║        Powered by Google Gemini for Dynamic Storytelling     ║
╚══════════════════════════════════════════════════════════════╝

A text-based financial simulation game where your choices shape
your financial future — with AI-generated surprises along the way.

Every playthrough is unique: careers, housing, lifestyles, and
mid-year decisions are all generated fresh by Gemini.
"""

import os
import sys
import time
import random
import textwrap
import json
from dataclasses import dataclass, field
import google.generativeai as genai

# ── Gemini Setup ──────────────────────────────────────────────────────────────
try:
    with open('gemini-api-key', 'r') as f:
        API_KEY = f.read().strip()
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# ── Terminal Helpers ──────────────────────────────────────────────────────────
WIDTH = 70

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def slow_print(text: str, delay: float = 0.022):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def box(title: str, char="═"):
    bar = char * (WIDTH - 2)
    print(f"╔{bar}╗")
    pad = (WIDTH - 2 - len(title)) // 2
    print(f"║{' ' * pad}{title}{' ' * (WIDTH - 2 - pad - len(title))}║")
    print(f"╚{bar}╝")

def divider(char="─"):
    print(char * WIDTH)

def wrap(text: str, indent: int = 0) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=WIDTH, initial_indent=prefix, subsequent_indent=prefix)

def choose(prompt: str, options: list[str]) -> int:
    """Display numbered choices and return 0-based index."""
    print()
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print()
    while True:
        try:
            raw = input(f"  {prompt} (1-{len(options)}): ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"  ⚠  Please enter a number between 1 and {len(options)}.")

def fmt_money(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.0f}"

def pause(msg="  Press ENTER to continue..."):
    input(msg)

def _call_gemini(prompt: str) -> str:
    """Raw Gemini call — raises on failure."""
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()

# ── Game State ────────────────────────────────────────────────────────────────
@dataclass
class Player:
    name: str = "Graduate"
    age: int = 22
    year: int = 0

    career: str = ""
    salary: float = 0.0
    job_stability: float = 0.8

    savings: float = 1_000.0
    debt: float = 0.0
    monthly_expenses: float = 0.0
    investment_rate: float = 0.0

    housing: str = ""
    housing_cost: float = 0.0
    lifestyle: str = ""
    lifestyle_options: list = field(default_factory=list)  # stored for cut_spending

    happiness: int = 60
    stress: int = 30

    events: list[str] = field(default_factory=list)
    net_worth_history: list[float] = field(default_factory=list)

    @property
    def net_worth(self) -> float:
        return self.savings - self.debt

    @property
    def monthly_surplus(self) -> float:
        monthly_income = self.salary / 12
        debt_payment = self.debt * 0.015 if self.debt > 0 else 0
        return monthly_income - self.monthly_expenses - self.housing_cost - debt_payment

    def annual_update(self):
        surplus = self.monthly_surplus * 12
        self.savings += surplus
        if self.savings < 0:
            self.debt += abs(self.savings)
            self.savings = 0

        invested = self.savings * self.investment_rate
        market_return = random.gauss(0.08, 0.12)
        self.savings += invested * market_return

        raise_pct = random.uniform(0.01, 0.05)
        self.salary *= (1 + raise_pct)

        if self.debt > 0:
            self.debt *= 1.065

        self.age += 1
        self.year += 1
        self.net_worth_history.append(self.net_worth)

# ── Static Fallbacks ──────────────────────────────────────────────────────────
# Used when Gemini is unavailable or returns bad JSON.

FALLBACK_CAREERS = [
    {"title": "Software Engineer",       "salary": 95000, "stability": 0.85,
     "desc": "Tech startup or large company. High demand, long hours.",             "emoji": "💻"},
    {"title": "Teacher / Educator",      "salary": 45000, "stability": 0.95,
     "desc": "Stable public sector role. Summers off, loan forgiveness.",           "emoji": "📚"},
    {"title": "Marketing Specialist",    "salary": 55000, "stability": 0.75,
     "desc": "Creative agency life. Fast-paced, client-driven.",                    "emoji": "📣"},
    {"title": "Nurse / Healthcare",      "salary": 72000, "stability": 0.90,
     "desc": "High demand, shift work. Emotionally rewarding.",                     "emoji": "🏥"},
    {"title": "Freelancer / Gig Worker", "salary": 38000, "stability": 0.55,
     "desc": "Total freedom. Feast or famine income. No benefits.",                 "emoji": "🎯"},
    {"title": "Finance Analyst",         "salary": 80000, "stability": 0.80,
     "desc": "Wall Street adjacent. Bonuses possible, stress high.",                "emoji": "📈"},
    {"title": "UX / Product Designer",   "salary": 78000, "stability": 0.80,
     "desc": "Shape how people interact with software. Creative meets technical.",   "emoji": "🎨"},
    {"title": "Entrepreneur",            "salary": 28000, "stability": 0.40,
     "desc": "High risk, high reward. Could be worth millions — or nothing.",       "emoji": "🚀"},
    {"title": "Cybersecurity Analyst",   "salary": 88000, "stability": 0.88,
     "desc": "Defending systems from hackers. Fast-growing field, always in demand.","emoji": "🔐"},
    {"title": "Physical Therapist",      "salary": 68000, "stability": 0.92,
     "desc": "Help people recover and rebuild. Fulfilling hands-on healthcare role.","emoji": "🦴"},
]

FALLBACK_HOUSING = [
    {"title": "Roommates / Shared Apt", "monthly_cost": 700,  "requires_down": False,
     "desc": "Split costs with friends. Less privacy, more savings.",         "emoji": "🏘️"},
    {"title": "Solo Apartment",         "monthly_cost": 1400, "requires_down": False,
     "desc": "Your own space. Higher cost, but freedom.",                     "emoji": "🏙️"},
    {"title": "Live with Parents",      "monthly_cost": 0,    "requires_down": False,
     "desc": "Free rent! Social stigma, but rocket-fuel for savings.",        "emoji": "👨‍👩‍👧"},
    {"title": "Buy a Condo",            "monthly_cost": 1600, "requires_down": True,
     "desc": "Building equity. Requires $20K down payment.",                  "emoji": "🏠"},
]

FALLBACK_LIFESTYLES = [
    {"title": "Frugal Minimalist", "monthly_cost": 1200, "happiness_delta": +10,
     "stress_delta": -5,  "desc": "Cooking at home, thrift stores, no subscriptions.",     "emoji": "🌱"},
    {"title": "Balanced",          "monthly_cost": 2000, "happiness_delta":   0,
     "stress_delta":  0,  "desc": "Occasional dining out, some hobbies, modest fun.",      "emoji": "⚖️"},
    {"title": "Social Spender",    "monthly_cost": 3200, "happiness_delta": +15,
     "stress_delta": +10, "desc": "Concerts, travel, great restaurants — YOLO.",           "emoji": "🎉"},
    {"title": "Luxury Seeker",     "monthly_cost": 5000, "happiness_delta":  +5,
     "stress_delta": +20, "desc": "Premium everything. Designer goods, frequent trips.",   "emoji": "💎"},
]

FALLBACK_DEBT = [
    {"label": "No debt",            "amount": 0,      "desc": "Scholarships or worked through school. Lucky!"},
    {"label": "Low ($15,000)",      "amount": 15000,  "desc": "Some loans. Manageable with discipline."},
    {"label": "Average ($35,000)",  "amount": 35000,  "desc": "Typical 4-year university debt. Requires a plan."},
    {"label": "High ($75,000)",     "amount": 75000,  "desc": "Grad school or private university. Heavy burden."},
]

FALLBACK_INVESTMENTS = [
    {"label": "None — keep it in savings",   "rate": 0.00, "desc": "Safe but loses to inflation (2–3%/yr)."},
    {"label": "Conservative (20% invested)", "rate": 0.20, "desc": "Some growth, low risk. Bonds + index funds."},
    {"label": "Moderate (50% invested)",     "rate": 0.50, "desc": "Balanced portfolio. Recommended for most."},
    {"label": "Aggressive (90% invested)",   "rate": 0.90, "desc": "Max growth potential. Can lose big in crashes."},
]

# ── Gemini: Dynamic Option Generators ────────────────────────────────────────

def gemini_generate_careers() -> list[dict]:
    """Generate 10 fresh career options — including unusual ones — per run."""
    prompt = """You are generating career options for a financial life simulation game. 
Create exactly 10 DIVERSE career paths for a recent college graduate.
Include a wide spread across these categories:
  - Traditional high-paying (e.g. software engineer, finance analyst, pharmacist)
  - Healthcare / public sector (e.g. nurse, teacher, social worker, physical therapist)
  - Creative / media (e.g. graphic designer, content creator, film editor, copywriter)
  - Unconventional / niche (e.g. sommelier, park ranger, esports coach, patent agent, maritime officer, urban beekeeper, legislative aide)
  - High-risk / entrepreneurial (e.g. startup founder, day trader, freelance consultant)
  - Emerging fields (e.g. AI prompt engineer, cybersecurity analyst, climate tech researcher, UX researcher)

Each run should feel fresh — avoid repeating the same careers across playthroughs.

Return ONLY a JSON array of exactly 10 objects. Each object must have:
  "title": career name (max 5 words)
  "salary": realistic starting annual salary as integer (range: 28000–115000)
  "stability": job stability 0.0–1.0 (1.0 = very stable, 0.4 = risky)
  "desc": one engaging sentence about this career path (max 15 words)
  "emoji": one relevant emoji

Vary the salaries realistically across the full range. No markdown. No extra text. Just the JSON array."""
    try:
        text = _call_gemini(prompt)
        careers = json.loads(text)
        # Validate structure
        for c in careers:
            assert all(k in c for k in ("title", "salary", "stability", "desc", "emoji"))
            c["salary"] = int(c["salary"])
            c["stability"] = float(c["stability"])
        return careers[:10]
    except Exception:
        return FALLBACK_CAREERS


def gemini_generate_housing(career: str, salary: float) -> list[dict]:
    """Generate 4 housing options tailored to the player's career and salary."""
    prompt = f"""You are generating housing choices for a financial life simulation game.
The player is a {career} earning {fmt_money(salary)}/year who just graduated.

Create exactly 4 DISTINCT housing options that make sense for this person.
Include creative/realistic variety: could include co-living spaces, micro-apartments,
house hacking, living in a van, rural cheap rental, buying a duplex, etc.
At least one option should be surprisingly cheap and one should be aspirationally expensive.

Return ONLY a JSON array of exactly 4 objects. Each must have:
  "title": housing name (max 5 words)
  "monthly_cost": monthly cost in dollars as integer (0–3500)
  "requires_down": true if buying (needs $20K down payment), otherwise false
  "desc": one vivid sentence about this choice (max 15 words)
  "emoji": one relevant emoji

No markdown. No extra text. Just the JSON array."""
    try:
        text = _call_gemini(prompt)
        options = json.loads(text)
        for h in options:
            assert all(k in h for k in ("title", "monthly_cost", "requires_down", "desc", "emoji"))
            h["monthly_cost"] = int(h["monthly_cost"])
            h["requires_down"] = bool(h["requires_down"])
        return options[:4]
    except Exception:
        return FALLBACK_HOUSING


def gemini_generate_lifestyles(career: str, salary: float) -> list[dict]:
    """Generate 4 lifestyle archetypes appropriate to the player's situation."""
    prompt = f"""You are generating lifestyle choices for a financial life simulation game.
The player is a {career} earning {fmt_money(salary)}/year.

Create exactly 4 DISTINCT lifestyle archetypes ranging from very frugal to extravagant.
Be creative — avoid generic names. Examples: 'Digital Nomad', 'Quiet Quitter', 
'Fitness Obsessed', 'Foodie & Traveler', 'Homesteader', 'FIRE Devotee', 'Social Butterfly'.

Return ONLY a JSON array of exactly 4 objects, ordered from cheapest to most expensive. Each must have:
  "title": lifestyle name (2–4 words, creative)
  "monthly_cost": non-housing monthly spending as integer (800–6000)
  "happiness_delta": integer from -5 to +20 (how much it shifts happiness 0–100)
  "stress_delta": integer from -10 to +25 (how much it shifts stress 0–100)
  "desc": one evocative sentence about how this person lives (max 15 words)
  "emoji": one relevant emoji

No markdown. No extra text. Just the JSON array."""
    try:
        text = _call_gemini(prompt)
        options = json.loads(text)
        for l in options:
            assert all(k in l for k in ("title", "monthly_cost", "happiness_delta", "stress_delta", "desc", "emoji"))
            l["monthly_cost"] = int(l["monthly_cost"])
            l["happiness_delta"] = int(l["happiness_delta"])
            l["stress_delta"] = int(l["stress_delta"])
        return options[:4]
    except Exception:
        return FALLBACK_LIFESTYLES


def gemini_generate_mid_year_decision(player: Player) -> dict:
    """Generate a unique, contextual mid-year decision for this specific player."""
    prompt = f"""You are the narrator of a financial life simulation game. 
Generate a UNIQUE mid-year financial decision moment for this player:

Player: {player.age}-year-old {player.career}
Salary: {fmt_money(player.salary)}/yr | Savings: {fmt_money(player.savings)} | Debt: {fmt_money(player.debt)}
Lifestyle: {player.lifestyle} | Housing: {player.housing}
Happiness: {player.happiness}/100 | Stress: {player.stress}/100
Recent events: {'; '.join(player.events[-2:]) if player.events else 'none yet'}

Create a realistic, specific dilemma this person would actually face. Examples:
- A friend offers them a stake in a restaurant for $8K
- Their company offers unpaid sabbatical
- They're offered a job in another city for 20% more pay
- A relative asks for a $5K loan
- They can join a group investment property deal
- A startup wants to hire them for equity + lower salary
- Their landlord offers to sell them the unit

Return ONLY a JSON object with:
  "prompt": 2-sentence setup of the situation (vivid, specific)
  "choices": array of exactly 3 choice objects, each with:
    "label": short option name (max 6 words)  
    "desc": one sentence consequence/detail
    "savings_delta": one-time dollar impact on savings (negative or positive integer, 0 if neutral)
    "salary_delta": annual salary change (can be 0)
    "happiness_delta": integer -15 to +15
    "stress_delta": integer -15 to +15
    "action_key": unique snake_case identifier

No markdown. No extra text. Just the JSON object."""
    try:
        text = _call_gemini(prompt)
        decision = json.loads(text)
        assert "prompt" in decision and "choices" in decision
        assert len(decision["choices"]) == 3
        return decision
    except Exception:
        # Fallback: static but decent
        return {
            "prompt": "Your company is offering a professional development budget of $1,500. You could spend it on a certification course, donate it to your emergency fund, or use it for a networking conference.",
            "choices": [
                {"label": "Take the certification course", "desc": "Boosts your credentials and likely salary.",
                 "savings_delta": 0, "salary_delta": 2000, "happiness_delta": 5, "stress_delta": -3, "action_key": "cert"},
                {"label": "Pocket it toward savings", "desc": "Direct cash boost to your emergency fund.",
                 "savings_delta": 1500, "salary_delta": 0, "happiness_delta": 3, "stress_delta": -5, "action_key": "save"},
                {"label": "Go to the conference", "desc": "Networking opportunity — connections could pay off later.",
                 "savings_delta": 0, "salary_delta": 0, "happiness_delta": 10, "stress_delta": 5, "action_key": "network"},
            ]
        }

# ── Gemini: Narrative Generators ──────────────────────────────────────────────

def gemini_event(player: Player) -> dict:
    prompt = f"""You are the narrator of a financial life simulation game. Generate a realistic random life event 
for a {player.age}-year-old who works as a {player.career}, earns {fmt_money(player.salary)}/year, 
has {fmt_money(player.savings)} in savings, {fmt_money(player.debt)} in debt, and lives a 
"{player.lifestyle}" lifestyle.

Return ONLY a JSON object with these exact keys:
  "title": short dramatic event title (max 8 words)
  "story": 2–3 sentence narrative description
  "financial_impact": integer dollar amount (negative = expense, positive = windfall)
  "happiness_delta": integer -20 to +20
  "stress_delta": integer -20 to +20
  "insight": one actionable financial lesson (1 sentence)

Event types to draw from: medical bill, car breakdown, promotion bonus, inheritance, 
identity theft, side hustle success, market crash, unexpected tax refund, 
wedding expense, freelance opportunity, apartment repair, scholarship, 
relocation offer, viral moment, product recall, crypto windfall/crash.
No markdown. Just the JSON."""
    try:
        return json.loads(_call_gemini(prompt))
    except Exception:
        return {
            "title": "Unexpected Car Repair",
            "story": "Your car suddenly broke down on the way to work. The mechanic quoted you for a costly repair that couldn't wait.",
            "financial_impact": -random.randint(400, 1200),
            "happiness_delta": -8,
            "stress_delta": 12,
            "insight": "An emergency fund of 3–6 months protects you from unexpected costs."
        }

def gemini_career_story(career: str, salary: float) -> str:
    prompt = f"""Write a vivid 3-sentence story about the FIRST WEEK of work for a new graduate 
starting their career as a {career} earning {fmt_money(salary)}/year. 
Keep it grounded, slightly humorous, and relatable. No lists, just narrative prose."""
    try:
        return model.generate_content(prompt).text.strip()
    except Exception:
        return f"You nervously walked into your first day as a {career}. The office was a blur of new faces, passwords, and orientation packets. But as the week wrapped up, you felt a quiet pride — this was the beginning of something real."

def gemini_year_recap(player: Player) -> str:
    prompt = f"""You are narrating a financial life game. Write a SHORT (3 sentences) 
year-in-review for a {player.age}-year-old {player.career}. 
Net worth: {fmt_money(player.net_worth)}, savings: {fmt_money(player.savings)}, 
debt: {fmt_money(player.debt)}, happiness: {player.happiness}/100, stress: {player.stress}/100.
Recent events: {'; '.join(player.events[-3:]) if player.events else 'none yet'}.
Make it feel like a personal journal entry — reflective and human."""
    try:
        return model.generate_content(prompt).text.strip()
    except Exception:
        return f"Year {player.year} has come and gone. Your net worth stands at {fmt_money(player.net_worth)}."

def gemini_final_verdict(player: Player) -> str:
    prompt = f"""Write a compelling 4-sentence financial life verdict for a {player.age}-year-old 
who started at 22 with $1,000. Final stats: Net Worth {fmt_money(player.net_worth)}, 
Career: {player.career}, Lifestyle: {player.lifestyle}, Happiness: {player.happiness}/100.
Be honest — celebrate wins, acknowledge mistakes, end with one piece of wisdom.
No lists. Pure narrative. Make it feel earned."""
    try:
        return model.generate_content(prompt).text.strip()
    except Exception:
        return f"After {player.year} years, you've built a net worth of {fmt_money(player.net_worth)}. Every decision shaped this outcome."

# ── Screens ───────────────────────────────────────────────────────────────────

def splash_screen():
    clear()
    print()
    box("  LIFE AFTER GRADUATION  ")
    print()
    slow_print(wrap("Welcome to the financial simulation where YOUR choices shape your future."))
    print()
    slow_print(wrap("Careers, housing, and life decisions are generated fresh by Gemini — no two runs are the same."))
    print()
    divider()
    if GEMINI_AVAILABLE:
        slow_print("  ✓ Gemini connected. Full dynamic mode active.")
    else:
        slow_print("  ⚠  Gemini unavailable. Running with built-in fallbacks.")
    divider()
    print()
    pause("  Press ENTER to begin your story...")

def _loading(msg: str):
    slow_print(f"  ✨ {msg}", delay=0.03)
    time.sleep(0.3)

def setup_player() -> Player:
    clear()
    box("CHARACTER CREATION")
    print()
    name = input("  What is your name, graduate? ").strip() or "Alex"
    player = Player(name=name)

    # ── Career ──
    clear()
    box("CHOOSE YOUR CAREER PATH")
    print()
    _loading("Gemini is generating your job offers...")
    careers = gemini_generate_careers()
    clear()
    box("CHOOSE YOUR CAREER PATH")
    print()
    slow_print(wrap("  Fresh diploma in hand, your inbox has several offers. Which path calls to you?"))
    print()
    for i, c in enumerate(careers, 1):
        print(f"  [{i}] {c['emoji']}  {c['title']:<30} {fmt_money(c['salary'])}/yr")
        print(f"      {c['desc']}")
        print()
    idx = choose("Your career choice", [c["title"] for c in careers])
    chosen_career = careers[idx]
    player.career = chosen_career["title"]
    player.salary = chosen_career["salary"] * random.uniform(0.92, 1.10)
    player.job_stability = chosen_career["stability"]
    print()
    slow_print(f"  ✓ Offer accepted: {player.career} at {fmt_money(player.salary)}/yr.")

    # First-week story
    print()
    _loading("Writing your first week on the job...")
    story = gemini_career_story(player.career, player.salary)
    print()
    slow_print(wrap(story), 0.018)
    pause()

    # ── Student Debt ──
    clear()
    box("STUDENT DEBT")
    print()
    slow_print(wrap("  Before you celebrate, there's the matter of your student loans..."))
    print()
    for i, d in enumerate(FALLBACK_DEBT, 1):
        print(f"  [{i}] {d['label']:<25} {d['desc']}")
    print()
    idx = choose("Your debt situation", [d["label"] for d in FALLBACK_DEBT])
    chosen_debt = FALLBACK_DEBT[idx]
    player.debt = chosen_debt["amount"]
    if player.debt == 0:
        slow_print("\n  ✓ Debt-free! You're starting with a huge advantage.")
    else:
        slow_print(f"\n  ✓ You owe {fmt_money(player.debt)} in student loans.")
    pause()

    # ── Housing ──
    clear()
    box("WHERE WILL YOU LIVE?")
    print()
    _loading("Gemini is scouting housing options for you...")
    housing_options = gemini_generate_housing(player.career, player.salary)
    clear()
    box("WHERE WILL YOU LIVE?")
    print()
    slow_print(wrap("  The apartment search begins. What's your housing situation?"))
    print()
    for i, h in enumerate(housing_options, 1):
        down = "  [needs $20K down]" if h["requires_down"] else ""
        print(f"  [{i}] {h['emoji']}  {h['title']:<30} {fmt_money(h['monthly_cost'])}/mo{down}")
        print(f"      {h['desc']}")
        print()
    idx = choose("Your housing choice", [h["title"] for h in housing_options])
    chosen_housing = housing_options[idx]
    player.housing = chosen_housing["title"]
    player.housing_cost = chosen_housing["monthly_cost"]

    if chosen_housing["requires_down"]:
        if player.savings < 20_000:
            slow_print("\n  ⚠  Not enough savings for a down payment. Switching to the cheapest option.")
            cheapest = min(housing_options, key=lambda h: h["monthly_cost"])
            player.housing = cheapest["title"]
            player.housing_cost = cheapest["monthly_cost"]
        else:
            player.savings -= 20_000
            slow_print(f"\n  ✓ Down payment made! {fmt_money(20_000)} removed from savings.")
    pause()

    # ── Lifestyle ──
    clear()
    box("CHOOSE YOUR LIFESTYLE")
    print()
    _loading("Gemini is crafting lifestyle archetypes for your situation...")
    lifestyle_options = gemini_generate_lifestyles(player.career, player.salary)
    player.lifestyle_options = lifestyle_options  # store for cut_spending later
    clear()
    box("CHOOSE YOUR LIFESTYLE")
    print()
    slow_print(wrap("  How do you want to live? This shapes your spending, happiness, and stress."))
    print()
    for i, l in enumerate(lifestyle_options, 1):
        print(f"  [{i}] {l['emoji']}  {l['title']:<26} {fmt_money(l['monthly_cost'])}/mo  "
              f"😊{l['happiness_delta']:+d}  😰{l['stress_delta']:+d}")
        print(f"      {l['desc']}")
        print()
    idx = choose("Your lifestyle", [l["title"] for l in lifestyle_options])
    chosen_lifestyle = lifestyle_options[idx]
    player.lifestyle = chosen_lifestyle["title"]
    player.monthly_expenses = chosen_lifestyle["monthly_cost"]
    player.happiness = min(100, player.happiness + chosen_lifestyle["happiness_delta"])
    player.stress = max(0, min(100, player.stress + chosen_lifestyle["stress_delta"]))
    pause()

    # ── Investment Strategy ──
    clear()
    box("INVESTMENT STRATEGY")
    print()
    slow_print(wrap("  Your HR portal asks how you'd like to handle your savings. What's your plan?"))
    print()
    for i, inv in enumerate(FALLBACK_INVESTMENTS, 1):
        print(f"  [{i}] {inv['label']:<38} {inv['rate']*100:.0f}% in market")
        print(f"      {inv['desc']}")
        print()
    idx = choose("Your investment strategy", [inv["label"] for inv in FALLBACK_INVESTMENTS])
    chosen_inv = FALLBACK_INVESTMENTS[idx]
    player.investment_rate = chosen_inv["rate"]
    slow_print(f"\n  ✓ Strategy set: {chosen_inv['label']}")
    pause()

    return player

# ── HUD ────────────────────────────────────────────────────────────────────────

def show_hud(player: Player):
    clear()
    box(f"  YEAR {player.year}  |  Age {player.age}  |  {player.career}  ")
    print()
    print(f"  {'Salary:':<20} {fmt_money(player.salary)}/yr    {'Net Worth:':<15} {fmt_money(player.net_worth)}")
    print(f"  {'Savings:':<20} {fmt_money(player.savings)}      {'Debt:':<15} {fmt_money(player.debt)}")
    monthly = player.monthly_surplus
    sign = "+" if monthly >= 0 else ""
    print(f"  {'Monthly Surplus:':<20} {sign}{fmt_money(monthly)}/mo  {'Housing:':<15} {player.housing}")
    print(f"  {'Lifestyle:':<20} {player.lifestyle}")
    print()
    hap_bar = "█" * (player.happiness // 5) + "░" * (20 - player.happiness // 5)
    str_bar = "█" * (player.stress // 5) + "░" * (20 - player.stress // 5)
    print(f"  Happiness [{hap_bar}] {player.happiness:3d}/100")
    print(f"  Stress    [{str_bar}] {player.stress:3d}/100")
    print()
    divider()

# ── Mid-Year Decisions ─────────────────────────────────────────────────────────

def mid_year_choices(player: Player):
    """AI-generated contextual mid-year decision, plus optional manual actions."""
    print()
    slow_print("  📋  MID-YEAR DECISION TIME")
    divider("-")

    # Always offer standard manual options
    manual = []
    if player.debt > 0 and player.savings > 5_000:
        manual.append(("💪 Pay extra $2,000 toward debt", "debt_payoff"))
    if player.lifestyle_options:
        titles = [l["title"] for l in player.lifestyle_options]
        if player.lifestyle in titles:
            idx_life = titles.index(player.lifestyle)
            if idx_life > 0:
                manual.append(("✂️  Cut back spending (downgrade lifestyle)", "cut_spending"))
    manual.append(("🧘 Stay the course — do nothing", "nothing"))

    # Generate a Gemini dilemma
    _loading("Gemini is crafting your mid-year dilemma...")
    decision = gemini_generate_mid_year_decision(player)

    print()
    slow_print(wrap(f"  {decision['prompt']}"))
    print()

    # Show AI choices first, then manual options
    all_options = [(c["label"], f"ai_{c['action_key']}", c) for c in decision["choices"]]
    display_labels = [f"[AI] {c['label']}" for c in decision["choices"]]

    for lbl, key, c in all_options:
        print(f"       → {c['desc']}")

    divider("-")
    slow_print(wrap("  Or choose a standard action:"))

    combined_labels = display_labels + [m[0] for m in manual]
    combined_keys   = [(k, c) for _, k, c in all_options] + [(m[1], None) for m in manual]

    print()
    for i, lbl in enumerate(combined_labels, 1):
        print(f"  [{i}] {lbl}")
    print()

    while True:
        try:
            raw = input(f"  Your choice (1-{len(combined_labels)}): ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(combined_labels):
                break
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"  ⚠  Please enter 1–{len(combined_labels)}.")

    chosen_key, chosen_ai = combined_keys[idx]

    if chosen_ai is not None:
        # Apply AI dilemma choice
        c = chosen_ai
        if c["savings_delta"] != 0:
            delta = c["savings_delta"]
            player.savings = max(0, player.savings + delta)
            if player.savings == 0 and delta < 0:
                player.debt += abs(delta)
            verb = "gained" if delta > 0 else "spent"
            slow_print(f"\n  💰 You {verb} {fmt_money(abs(delta))}.")
        if c["salary_delta"] != 0:
            player.salary += c["salary_delta"]
            slow_print(f"\n  📈 Salary adjusted by {fmt_money(c['salary_delta'])}/yr.")
        player.happiness = max(0, min(100, player.happiness + c["happiness_delta"]))
        player.stress = max(0, min(100, player.stress + c["stress_delta"]))
        slow_print(f"\n  ✓ Choice made: {c['label']}")
        player.events.append(c["label"])

    elif chosen_key == "debt_payoff":
        extra = min(2_000, player.savings - 1_000)
        player.savings -= extra
        player.debt = max(0, player.debt - extra)
        slow_print(f"\n  💪 Extra {fmt_money(extra)} toward debt. Remaining: {fmt_money(player.debt)}")

    elif chosen_key == "cut_spending":
        titles = [l["title"] for l in player.lifestyle_options]
        idx_life = titles.index(player.lifestyle)
        if idx_life > 0:
            new = player.lifestyle_options[idx_life - 1]
            old = player.lifestyle_options[idx_life]
            savings_gain = player.monthly_expenses - new["monthly_cost"]
            player.monthly_expenses = new["monthly_cost"]
            player.lifestyle = new["title"]
            player.happiness = max(0, player.happiness + new["happiness_delta"] - old["happiness_delta"])
            slow_print(f"\n  ✂️  Downgraded to '{new['title']}'. Saving {fmt_money(savings_gain)}/mo more.")

    elif chosen_key == "nothing":
        slow_print("\n  🧘 You stayed the course. Sometimes that's the wisest move.")

    pause()

# ── Random AI Event ─────────────────────────────────────────────────────────────

def trigger_random_event(player: Player):
    print()
    slow_print("  🎲  RANDOM EVENT (powered by Gemini AI)...", 0.04)
    time.sleep(0.5)
    event = gemini_event(player)
    print()
    divider("═")
    slow_print(f"  ⚡  {event['title'].upper()}")
    divider("═")
    print()
    slow_print(wrap(event["story"]), 0.020)
    print()
    impact = event["financial_impact"]
    if impact < 0:
        player.savings += impact
        if player.savings < 0:
            player.debt += abs(player.savings)
            player.savings = 0
        slow_print(f"  💸 Financial Impact: {fmt_money(impact)}")
    else:
        player.savings += impact
        slow_print(f"  💰 Financial Impact: +{fmt_money(impact)}")
    player.happiness = max(0, min(100, player.happiness + event["happiness_delta"]))
    player.stress = max(0, min(100, player.stress + event["stress_delta"]))
    print()
    slow_print(f"  💡 Insight: {event['insight']}", 0.018)
    print()
    player.events.append(event["title"])
    pause()

# ── Job Event ──────────────────────────────────────────────────────────────────

def job_event(player: Player):
    roll = random.random()
    if roll > player.job_stability:
        months_out = random.randint(2, 6)
        lost = player.salary / 12 * months_out
        player.savings -= lost
        if player.savings < 0:
            player.debt += abs(player.savings)
            player.savings = 0
        player.stress = min(100, player.stress + 25)
        player.happiness = max(0, player.happiness - 20)
        print()
        divider("═")
        slow_print(f"  🚨  JOB DISRUPTION!")
        slow_print(wrap(f"  Laid off from your {player.career} role. {months_out} months to find new work. Lost roughly {fmt_money(lost)} in income."))
        divider("═")
        pause()
    elif roll > 0.85:
        boost = random.uniform(0.05, 0.15)
        player.salary *= (1 + boost)
        player.happiness = min(100, player.happiness + 10)
        print()
        slow_print(f"\n  🎊  PROMOTION! Salary jumped {boost*100:.0f}% to {fmt_money(player.salary)}/yr!")
        pause()

# ── Year Loop ──────────────────────────────────────────────────────────────────

def run_year(player: Player):
    show_hud(player)
    mid_year_choices(player)

    if random.random() < 0.70:
        trigger_random_event(player)

    job_event(player)
    player.annual_update()

    show_hud(player)
    slow_print("  📖  YEAR IN REVIEW (Gemini Narrator)...")
    time.sleep(0.3)
    recap = gemini_year_recap(player)
    print()
    slow_print(wrap(recap), 0.018)
    print()
    pause(f"  Press ENTER to advance to Year {player.year + 1}...")

# ── Net Worth Chart ────────────────────────────────────────────────────────────

def show_chart(player: Player):
    history = player.net_worth_history
    if not history:
        return
    clear()
    box("NET WORTH OVER TIME")
    print()
    max_val = max(history)
    min_val = min(history)
    span = max_val - min_val or 1
    rows = 12
    for r in range(rows, 0, -1):
        threshold = min_val + (span * r / rows)
        label = f"{fmt_money(threshold):>12}"
        line = label + "  │"
        for val in history:
            line += "▓▓ " if val >= threshold else "   "
        print(line)
    print(" " * 14 + "  └" + "───" * len(history))
    x_axis = " " * 16
    for i in range(1, len(history) + 1):
        x_axis += f"Y{i:<2}"
    print(x_axis)
    print()
    pause()

# ── Final Screen ───────────────────────────────────────────────────────────────

RATINGS = [
    (500_000,  "🏆 LEGENDARY — Financial Freedom Achieved!"),
    (200_000,  "🥇 EXCELLENT — Solid foundations built."),
    (100_000,  "🥈 GOOD — You're on the right track."),
    (50_000,   "🥉 FAIR — Some progress, but room to grow."),
    (0,        "📈 DEVELOPING — The journey continues."),
    (-1e9,     "😬 IN THE RED — Debt won this round."),
]

def final_screen(player: Player):
    clear()
    box(f"  GAME OVER — {player.name}'s {player.year}-YEAR JOURNEY  ")
    print()
    rating = RATINGS[-1][1]
    for threshold, label in RATINGS:
        if player.net_worth >= threshold:
            rating = label
            break
    slow_print(f"  {rating}")
    print()
    divider()
    print(f"  {'Final Net Worth:':<25} {fmt_money(player.net_worth)}")
    print(f"  {'Final Salary:':<25} {fmt_money(player.salary)}/yr")
    print(f"  {'Savings:':<25} {fmt_money(player.savings)}")
    print(f"  {'Remaining Debt:':<25} {fmt_money(max(0, player.debt))}")
    print(f"  {'Happiness:':<25} {player.happiness}/100")
    print(f"  {'Stress:':<25} {player.stress}/100")
    print(f"  {'Career:':<25} {player.career}")
    print(f"  {'Lifestyle:':<25} {player.lifestyle}")
    print(f"  {'Housing:':<25} {player.housing}")
    divider()
    print()
    if player.events:
        slow_print("  📌  MEMORABLE EVENTS:")
        for e in player.events[-6:]:
            print(f"       • {e}")
    print()
    show_chart(player)
    clear()
    box("YOUR FINANCIAL LEGACY")
    print()
    _loading("Generating your final life verdict...")
    verdict = gemini_final_verdict(player)
    print()
    slow_print(wrap(verdict), 0.018)
    print()
    divider()
    slow_print(wrap("  Thank you for playing LIFE AFTER GRADUATION. Real financial planning starts with understanding — and now you do."))
    print()

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    splash_screen()
    player = setup_player()

    clear()
    box("SIMULATION LENGTH")
    print()
    slow_print(wrap("  How many years into the future would you like to simulate?"))
    idx = choose("Your choice", [
        "5 years  — Quick playthrough",
        "10 years — Standard game",
        "20 years — Long-term vision",
    ])
    years = [5, 10, 20][idx]

    for _ in range(years):
        run_year(player)

    final_screen(player)

    print()
    again = input("  Play again? (y/n): ").strip().lower()
    if again == "y":
        main()
    else:
        slow_print("\n  Thanks for playing! May your finances be ever in your favour. 👋\n")


if __name__ == "__main__":
    main()