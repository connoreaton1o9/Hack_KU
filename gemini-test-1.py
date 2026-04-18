"""
╔══════════════════════════════════════════════════════════════╗
║          LIFE AFTER GRADUATION: THE FINANCIAL GAME           ║
║        Powered by Google Gemini for Dynamic Storytelling     ║
╚══════════════════════════════════════════════════════════════╝

A text-based financial simulation game where your choices shape
your financial future — with AI-generated surprises along the way.
"""

import os
import sys
import time
import random
import textwrap
import json
from dataclasses import dataclass, field
from typing import Optional
import google.generativeai as genai

# ── Gemini Setup ──────────────────────────────────────────────────────────────
apikey_file = open('gemini-api-key', 'r')
for line in apikey_file:
    API_KEY = line.strip('\n')
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

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

# ── Game State ────────────────────────────────────────────────────────────────
@dataclass
class Player:
    name: str = "Graduate"
    age: int = 22
    year: int = 0                    # years since graduation
    
    # Career
    career: str = ""
    salary: float = 0.0
    job_stability: float = 0.8       # 0–1, chance of keeping job each year
    
    # Finances
    savings: float = 1_000.0
    debt: float = 0.0
    monthly_expenses: float = 0.0
    investment_rate: float = 0.0     # fraction of savings in market
    
    # Lifestyle
    housing: str = ""
    housing_cost: float = 0.0
    lifestyle: str = ""
    
    # Stats (displayed as 0–100)
    happiness: int = 60
    stress: int = 30
    
    # History
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
        """Apply one year of financial change."""
        surplus = self.monthly_surplus * 12
        self.savings += surplus
        if self.savings < 0:
            self.debt += abs(self.savings)
            self.savings = 0

        # Investment growth (avg 8% market, with variance)
        invested = self.savings * self.investment_rate
        market_return = random.gauss(0.08, 0.12)
        self.savings += invested * market_return

        # Salary raise (1–5% annually)
        raise_pct = random.uniform(0.01, 0.05)
        self.salary *= (1 + raise_pct)

        # Debt interest
        if self.debt > 0:
            self.debt *= 1.065  # 6.5% average student loan rate

        self.age += 1
        self.year += 1
        self.net_worth_history.append(self.net_worth)

# ── Gemini AI Helpers ─────────────────────────────────────────────────────────

def gemini_event(player: Player) -> dict:
    """Ask Gemini to generate a random life event with financial impact."""
    prompt = f"""
You are the narrator of a financial life simulation game. Generate a realistic random life event 
for a {player.age}-year-old who works as a {player.career}, earns {fmt_money(player.salary)}/year, 
has {fmt_money(player.savings)} in savings, {fmt_money(player.debt)} in debt, and lives a 
"{player.lifestyle}" lifestyle.

Return ONLY a JSON object (no markdown fences) with these exact keys:
  "title": short dramatic event title (max 8 words)
  "story": 2–3 sentence narrative description of what happened
  "financial_impact": an integer dollar amount (negative = expense, positive = windfall). 
                      Keep it realistic and proportional to their income.
  "happiness_delta": integer -20 to +20
  "stress_delta": integer -20 to +20
  "insight": one actionable financial lesson from this event (1 sentence)

Examples of event types (pick randomly): medical bill, car breakdown, promotion bonus, 
inheritance, identity theft, side hustle success, market crash, unexpected tax refund, 
friendship wedding expense, freelance opportunity, apartment repair, scholarship award.
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        # Fallback event if API fails
        return {
            "title": "Unexpected Car Repair",
            "story": "Your car suddenly broke down on the way to work. The mechanic quoted you for a costly repair that couldn't wait.",
            "financial_impact": -random.randint(400, 1200),
            "happiness_delta": -8,
            "stress_delta": 12,
            "insight": "An emergency fund of 3–6 months of expenses protects you from unexpected costs."
        }

def gemini_career_story(career: str, salary: float) -> str:
    """Generate a short onboarding story for the chosen career."""
    prompt = f"""Write a vivid 3-sentence story about the FIRST WEEK of work for a new graduate 
starting their career as a {career} earning {fmt_money(salary)}/year. 
Keep it grounded, slightly humorous, and relatable. No lists, just narrative prose."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"You nervously walked into your first day as a {career}. The office was a blur of new faces, passwords, and orientation packets. But as the week wrapped up, you felt a quiet pride — this was the beginning of something real."

def gemini_year_recap(player: Player) -> str:
    """Generate an end-of-year narrative summary."""
    prompt = f"""You are narrating a financial life game. Write a SHORT (3 sentences) 
year-in-review for a {player.age}-year-old {player.career}. 
Their net worth is {fmt_money(player.net_worth)}, savings {fmt_money(player.savings)}, 
debt {fmt_money(player.debt)}, happiness {player.happiness}/100, stress {player.stress}/100.
Recent events: {'; '.join(player.events[-3:]) if player.events else 'none yet'}.
Make it feel like a personal journal entry — reflective and human."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"Year {player.year} has come and gone. Your net worth stands at {fmt_money(player.net_worth)}."

def gemini_final_verdict(player: Player) -> str:
    """Generate the final game ending narrative."""
    prompt = f"""Write a compelling 4-sentence financial life verdict for a {player.age}-year-old 
who started at 22 with $1,000. Final stats: Net Worth {fmt_money(player.net_worth)}, 
Career: {player.career}, Lifestyle: {player.lifestyle}, Happiness: {player.happiness}/100.
Be honest — celebrate wins, acknowledge mistakes, and end with one piece of wisdom.
No lists. Pure narrative. Make it feel earned."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"After {player.year} years, you've built a net worth of {fmt_money(player.net_worth)}. Every decision shaped this outcome."

# ── Character Setup ───────────────────────────────────────────────────────────

CAREERS = [
    ("Software Engineer",       95_000,  0.85, "Tech startup or large company. High demand, long hours."),
    ("Teacher / Educator",      45_000,  0.95, "Stable public sector role. Summers off, loan forgiveness possible."),
    ("Marketing Specialist",    55_000,  0.75, "Creative agency life. Fast-paced, client-driven."),
    ("Nurse / Healthcare",      72_000,  0.90, "High demand, shift work. Emotionally rewarding."),
    ("Freelancer / Gig Worker", 38_000,  0.55, "Total freedom. Feast or famine income. No benefits."),
    ("Finance Analyst",         80_000,  0.80, "Wall Street adjacent. Bonuses possible, stress high."),
    ("Non-Profit Worker",       40_000,  0.88, "Mission-driven. Loan forgiveness eligible. Low pay."),
    ("Entrepreneur",            25_000,  0.40, "High risk, high reward. Could be worth millions — or nothing."),
]

HOUSING = [
    ("Roommates / Shared Apt",  700,   "Split costs with friends. Less privacy, more savings."),
    ("Solo Apartment",         1_400,  "Your own space. Higher cost, but freedom."),
    ("Live with Parents",         0,   "Free rent! Social stigma, but rocket-fuel for savings."),
    ("Buy a Condo / House",    1_600,  "Building equity. Requires down payment from savings."),
]

LIFESTYLES = [
    ("Frugal Minimalist",   1_200,  +10, -5,  "Cooking at home, thrift stores, no subscriptions."),
    ("Balanced",            2_000,   0,   0,  "Occasional dining out, some hobbies, modest fun."),
    ("Social Spender",      3_200,  +15, +10, "Concerts, travel, great restaurants — YOLO."),
    ("Luxury Seeker",       5_000,  +5,  +20, "Premium everything. Designer goods, frequent trips."),
]

DEBT_OPTIONS = [
    ("No debt",           0,      "You worked through school or got scholarships. Lucky!"),
    ("Low ($15,000)",    15_000,  "Some loans. Manageable with discipline."),
    ("Average ($35,000)",35_000,  "Typical 4-year university debt. Requires a plan."),
    ("High ($75,000)",   75_000,  "Graduate school or private university. Heavy burden."),
]

INVESTMENT_OPTIONS = [
    ("None — keep it in savings",   0.00, "Safe but loses to inflation (2–3%/yr)."),
    ("Conservative (20% invested)", 0.20, "Some growth, low risk. Bonds + index funds."),
    ("Moderate (50% invested)",     0.50, "Balanced portfolio. Recommended for most."),
    ("Aggressive (90% invested)",   0.90, "Max growth potential. Can lose big in crashes."),
]

# ── Screens ───────────────────────────────────────────────────────────────────

def splash_screen():
    clear()
    print()
    box("  LIFE AFTER GRADUATION  ")
    print()
    slow_print(wrap("Welcome to the financial simulation game where YOUR choices shape your future."))
    print()
    slow_print(wrap("Make decisions about careers, housing, debt, and lifestyle — then watch as AI-powered random events test your plan."))
    print()
    divider()
    slow_print("  Each playthrough is unique. Powered by Google Gemini.")
    divider()
    print()
    pause("  Press ENTER to begin your story...")

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
    slow_print(wrap("  Fresh diploma in hand, you scan the job listings. Which path calls to you?"))
    print()
    for i, (title, salary, stability, desc) in enumerate(CAREERS, 1):
        print(f"  [{i}] {title:<28} {fmt_money(salary)}/yr")
        print(f"      {desc}")
        print()
    idx = choose("Your career choice", [c[0] for c in CAREERS])
    c = CAREERS[idx]
    player.career = c[0]
    player.salary = c[1] * random.uniform(0.92, 1.10)  # salary variance
    player.job_stability = c[2]
    print()
    slow_print(f"  ✓ You accepted an offer as a {player.career} at {fmt_money(player.salary)}/yr.")

    # Gemini career story
    print()
    slow_print("  Generating your first week story...", 0.03)
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
    for i, (label, amount, desc) in enumerate(DEBT_OPTIONS, 1):
        print(f"  [{i}] {label:<25} {desc}")
    print()
    idx = choose("Your debt situation", [d[0] for d in DEBT_OPTIONS])
    d = DEBT_OPTIONS[idx]
    player.debt = d[1]
    if player.debt == 0:
        slow_print("\n  ✓ Debt-free! You're starting with a huge advantage.")
    else:
        slow_print(f"\n  ✓ You owe {fmt_money(player.debt)} in student loans.")
    pause()

    # ── Housing ──
    clear()
    box("WHERE WILL YOU LIVE?")
    print()
    slow_print(wrap("  The apartment search begins. What's your housing situation?"))
    print()
    for i, (label, cost, desc) in enumerate(HOUSING, 1):
        print(f"  [{i}] {label:<28} {fmt_money(cost)}/mo")
        print(f"      {desc}")
        print()
    idx = choose("Your housing choice", [h[0] for h in HOUSING])
    h = HOUSING[idx]
    player.housing = h[0]
    player.housing_cost = h[1]

    # Buying requires down payment
    if "Buy" in player.housing and player.savings < 20_000:
        slow_print("\n  ⚠  You don't have enough for a down payment. Switching to a solo apartment.")
        player.housing = "Solo Apartment"
        player.housing_cost = HOUSING[1][1]
    elif "Buy" in player.housing:
        player.savings -= 20_000
        slow_print(f"\n  ✓ Down payment made! {fmt_money(20_000)} removed from savings.")
    pause()

    # ── Lifestyle ──
    clear()
    box("CHOOSE YOUR LIFESTYLE")
    print()
    slow_print(wrap("  How do you want to live? This affects monthly spending, happiness, and stress."))
    print()
    for i, (label, cost, hap, stress, desc) in enumerate(LIFESTYLES, 1):
        print(f"  [{i}] {label:<22} {fmt_money(cost)}/mo  😊+{hap:+d}  😰{stress:+d}")
        print(f"      {desc}")
        print()
    idx = choose("Your lifestyle", [l[0] for l in LIFESTYLES])
    l = LIFESTYLES[idx]
    player.lifestyle = l[0]
    player.monthly_expenses = l[1]
    player.happiness = min(100, player.happiness + l[2])
    player.stress = max(0, min(100, player.stress + l[3]))
    pause()

    # ── Investment Strategy ──
    clear()
    box("INVESTMENT STRATEGY")
    print()
    slow_print(wrap("  Your HR portal asks how you'd like to handle your savings. What's your strategy?"))
    print()
    for i, (label, rate, desc) in enumerate(INVESTMENT_OPTIONS, 1):
        print(f"  [{i}] {label:<38} {rate*100:.0f}% in market")
        print(f"      {desc}")
        print()
    idx = choose("Your investment strategy", [inv[0] for inv in INVESTMENT_OPTIONS])
    inv = INVESTMENT_OPTIONS[idx]
    player.investment_rate = inv[1]
    slow_print(f"\n  ✓ Strategy set: {inv[0]}")
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
    """Present optional decisions the player can make during the year."""
    decisions = []

    # Debt payoff opportunity
    if player.debt > 0 and player.savings > 5_000:
        decisions.append(("Pay extra $2,000 toward debt", "debt_payoff"))

    # Side hustle
    decisions.append(("Start a side hustle (risk vs reward)", "side_hustle"))

    # Skill upgrade
    decisions.append(("Invest in a professional course ($500)", "upskill"))

    # Reduce lifestyle
    if player.lifestyle not in ("Frugal Minimalist",):
        decisions.append(("Cut back on spending (reduce lifestyle)", "cut_spending"))

    decisions.append(("Do nothing — stay the course", "nothing"))

    print()
    slow_print("  📋  MID-YEAR DECISION TIME")
    divider("-")
    slow_print(wrap("  Life keeps moving. What action will you take this year?"))
    idx = choose("Your action", [d[0] for d in decisions])
    action = decisions[idx][1]

    if action == "debt_payoff":
        extra = min(2_000, player.savings - 1_000)
        player.savings -= extra
        player.debt = max(0, player.debt - extra)
        slow_print(f"\n  💪 You put {fmt_money(extra)} extra toward your debt. Remaining: {fmt_money(player.debt)}")

    elif action == "side_hustle":
        success = random.random() < 0.55
        if success:
            income = random.randint(2_000, 8_000)
            player.savings += income
            player.stress = min(100, player.stress + 8)
            player.happiness = min(100, player.happiness + 5)
            slow_print(f"\n  🎉 Your side hustle paid off! You earned {fmt_money(income)} extra this year.")
        else:
            cost = random.randint(200, 800)
            player.savings -= cost
            player.stress = min(100, player.stress + 15)
            slow_print(f"\n  😓 The side hustle flopped. You lost {fmt_money(cost)} on tools and subscriptions.")

    elif action == "upskill":
        if player.savings >= 500:
            player.savings -= 500
            boost = random.randint(1_500, 4_000)
            player.salary += boost
            slow_print(f"\n  📚 Smart move! Your new skills earned you a {fmt_money(boost)}/yr raise next review.")
        else:
            slow_print("\n  ⚠  Not enough savings for the course right now.")

    elif action == "cut_spending":
        idx_life = [l[0] for l in LIFESTYLES].index(player.lifestyle)
        if idx_life > 0:
            new = LIFESTYLES[idx_life - 1]
            savings_gain = player.monthly_expenses - new[1]
            player.monthly_expenses = new[1]
            player.lifestyle = new[0]
            player.happiness = max(0, player.happiness + new[2] - LIFESTYLES[idx_life][2])
            slow_print(f"\n  ✂️  Downgraded to '{new[0]}'. Saving {fmt_money(savings_gain)}/mo more.")

    elif action == "nothing":
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
    """Possible job disruption."""
    roll = random.random()
    if roll > player.job_stability:
        # Job loss
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
        slow_print(wrap(f"  You were laid off from your {player.career} role and spent {months_out} months finding new work. You lost roughly {fmt_money(lost)} in income."))
        divider("═")
        pause()
    elif roll > 0.85:
        # Promotion
        boost = random.uniform(0.05, 0.15)
        player.salary *= (1 + boost)
        player.happiness = min(100, player.happiness + 10)
        print()
        slow_print(f"\n  🎊  PROMOTION! Your salary jumped {boost*100:.0f}% to {fmt_money(player.salary)}/yr!")
        pause()

# ── Year Loop ──────────────────────────────────────────────────────────────────

def run_year(player: Player):
    show_hud(player)

    # Mid-year decision
    mid_year_choices(player)

    # Random Gemini event (70% chance each year)
    if random.random() < 0.70:
        trigger_random_event(player)

    # Job stability roll
    job_event(player)

    # Annual financial update
    player.annual_update()

    # Year recap from Gemini
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
    """ASCII net worth over time."""
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

# ── Final Score ────────────────────────────────────────────────────────────────

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

    # Rating
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

    # Key events
    if player.events:
        slow_print("  📌  MEMORABLE EVENTS:")
        for e in player.events[-6:]:
            print(f"       • {e}")
    print()

    show_chart(player)

    # Gemini final verdict
    clear()
    box("YOUR FINANCIAL LEGACY")
    print()
    slow_print("  Generating your final life verdict...", 0.03)
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

    # How many years to simulate
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

    # Game loop
    for _ in range(years):
        run_year(player)

    final_screen(player)

    # Play again?
    print()
    again = input("  Play again? (y/n): ").strip().lower()
    if again == "y":
        main()
    else:
        slow_print("\n  Thanks for playing! May your finances be ever in your favour. 👋\n")


if __name__ == "__main__":
    main()
"""
╔══════════════════════════════════════════════════════════════╗
║          LIFE AFTER GRADUATION: THE FINANCIAL GAME           ║
║        Powered by Google Gemini for Dynamic Storytelling     ║
╚══════════════════════════════════════════════════════════════╝

A text-based financial simulation game where your choices shape
your financial future — with AI-generated surprises along the way.
"""

import os
import sys
import time
import random
import textwrap
import json
from dataclasses import dataclass, field
from typing import Optional
import google.generativeai as genai

# ── Gemini Setup ──────────────────────────────────────────────────────────────
apikey_file = open('gemini-api-key', 'r')
for line in apikey_file:
    API_KEY = line.strip('\n')
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

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

# ── Game State ────────────────────────────────────────────────────────────────
@dataclass
class Player:
    name: str = "Graduate"
    age: int = 22
    year: int = 0                    # years since graduation
    
    # Career
    career: str = ""
    salary: float = 0.0
    job_stability: float = 0.8       # 0–1, chance of keeping job each year
    
    # Finances
    savings: float = 1_000.0
    debt: float = 0.0
    monthly_expenses: float = 0.0
    investment_rate: float = 0.0     # fraction of savings in market
    
    # Lifestyle
    housing: str = ""
    housing_cost: float = 0.0
    lifestyle: str = ""
    
    # Stats (displayed as 0–100)
    happiness: int = 60
    stress: int = 30
    
    # History
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
        """Apply one year of financial change."""
        surplus = self.monthly_surplus * 12
        self.savings += surplus
        if self.savings < 0:
            self.debt += abs(self.savings)
            self.savings = 0

        # Investment growth (avg 8% market, with variance)
        invested = self.savings * self.investment_rate
        market_return = random.gauss(0.08, 0.12)
        self.savings += invested * market_return

        # Salary raise (1–5% annually)
        raise_pct = random.uniform(0.01, 0.05)
        self.salary *= (1 + raise_pct)

        # Debt interest
        if self.debt > 0:
            self.debt *= 1.065  # 6.5% average student loan rate

        self.age += 1
        self.year += 1
        self.net_worth_history.append(self.net_worth)

# ── Gemini AI Helpers ─────────────────────────────────────────────────────────

def gemini_event(player: Player) -> dict:
    """Ask Gemini to generate a random life event with financial impact."""
    prompt = f"""
You are the narrator of a financial life simulation game. Generate a realistic random life event 
for a {player.age}-year-old who works as a {player.career}, earns {fmt_money(player.salary)}/year, 
has {fmt_money(player.savings)} in savings, {fmt_money(player.debt)} in debt, and lives a 
"{player.lifestyle}" lifestyle.

Return ONLY a JSON object (no markdown fences) with these exact keys:
  "title": short dramatic event title (max 8 words)
  "story": 2–3 sentence narrative description of what happened
  "financial_impact": an integer dollar amount (negative = expense, positive = windfall). 
                      Keep it realistic and proportional to their income.
  "happiness_delta": integer -20 to +20
  "stress_delta": integer -20 to +20
  "insight": one actionable financial lesson from this event (1 sentence)

Examples of event types (pick randomly): medical bill, car breakdown, promotion bonus, 
inheritance, identity theft, side hustle success, market crash, unexpected tax refund, 
friendship wedding expense, freelance opportunity, apartment repair, scholarship award.
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        # Fallback event if API fails
        return {
            "title": "Unexpected Car Repair",
            "story": "Your car suddenly broke down on the way to work. The mechanic quoted you for a costly repair that couldn't wait.",
            "financial_impact": -random.randint(400, 1200),
            "happiness_delta": -8,
            "stress_delta": 12,
            "insight": "An emergency fund of 3–6 months of expenses protects you from unexpected costs."
        }

def gemini_career_story(career: str, salary: float) -> str:
    """Generate a short onboarding story for the chosen career."""
    prompt = f"""Write a vivid 3-sentence story about the FIRST WEEK of work for a new graduate 
starting their career as a {career} earning {fmt_money(salary)}/year. 
Keep it grounded, slightly humorous, and relatable. No lists, just narrative prose."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"You nervously walked into your first day as a {career}. The office was a blur of new faces, passwords, and orientation packets. But as the week wrapped up, you felt a quiet pride — this was the beginning of something real."

def gemini_year_recap(player: Player) -> str:
    """Generate an end-of-year narrative summary."""
    prompt = f"""You are narrating a financial life game. Write a SHORT (3 sentences) 
year-in-review for a {player.age}-year-old {player.career}. 
Their net worth is {fmt_money(player.net_worth)}, savings {fmt_money(player.savings)}, 
debt {fmt_money(player.debt)}, happiness {player.happiness}/100, stress {player.stress}/100.
Recent events: {'; '.join(player.events[-3:]) if player.events else 'none yet'}.
Make it feel like a personal journal entry — reflective and human."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"Year {player.year} has come and gone. Your net worth stands at {fmt_money(player.net_worth)}."

def gemini_final_verdict(player: Player) -> str:
    """Generate the final game ending narrative."""
    prompt = f"""Write a compelling 4-sentence financial life verdict for a {player.age}-year-old 
who started at 22 with $1,000. Final stats: Net Worth {fmt_money(player.net_worth)}, 
Career: {player.career}, Lifestyle: {player.lifestyle}, Happiness: {player.happiness}/100.
Be honest — celebrate wins, acknowledge mistakes, and end with one piece of wisdom.
No lists. Pure narrative. Make it feel earned."""
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"After {player.year} years, you've built a net worth of {fmt_money(player.net_worth)}. Every decision shaped this outcome."

# ── Character Setup ───────────────────────────────────────────────────────────

CAREERS = [
    ("Software Engineer",       95_000,  0.85, "Tech startup or large company. High demand, long hours."),
    ("Teacher / Educator",      45_000,  0.95, "Stable public sector role. Summers off, loan forgiveness possible."),
    ("Marketing Specialist",    55_000,  0.75, "Creative agency life. Fast-paced, client-driven."),
    ("Nurse / Healthcare",      72_000,  0.90, "High demand, shift work. Emotionally rewarding."),
    ("Freelancer / Gig Worker", 38_000,  0.55, "Total freedom. Feast or famine income. No benefits."),
    ("Finance Analyst",         80_000,  0.80, "Wall Street adjacent. Bonuses possible, stress high."),
    ("Non-Profit Worker",       40_000,  0.88, "Mission-driven. Loan forgiveness eligible. Low pay."),
    ("Entrepreneur",            25_000,  0.40, "High risk, high reward. Could be worth millions — or nothing."),
]

HOUSING = [
    ("Roommates / Shared Apt",  700,   "Split costs with friends. Less privacy, more savings."),
    ("Solo Apartment",         1_400,  "Your own space. Higher cost, but freedom."),
    ("Live with Parents",         0,   "Free rent! Social stigma, but rocket-fuel for savings."),
    ("Buy a Condo / House",    1_600,  "Building equity. Requires down payment from savings."),
]

LIFESTYLES = [
    ("Frugal Minimalist",   1_200,  +10, -5,  "Cooking at home, thrift stores, no subscriptions."),
    ("Balanced",            2_000,   0,   0,  "Occasional dining out, some hobbies, modest fun."),
    ("Social Spender",      3_200,  +15, +10, "Concerts, travel, great restaurants — YOLO."),
    ("Luxury Seeker",       5_000,  +5,  +20, "Premium everything. Designer goods, frequent trips."),
]

DEBT_OPTIONS = [
    ("No debt",           0,      "You worked through school or got scholarships. Lucky!"),
    ("Low ($15,000)",    15_000,  "Some loans. Manageable with discipline."),
    ("Average ($35,000)",35_000,  "Typical 4-year university debt. Requires a plan."),
    ("High ($75,000)",   75_000,  "Graduate school or private university. Heavy burden."),
]

INVESTMENT_OPTIONS = [
    ("None — keep it in savings",   0.00, "Safe but loses to inflation (2–3%/yr)."),
    ("Conservative (20% invested)", 0.20, "Some growth, low risk. Bonds + index funds."),
    ("Moderate (50% invested)",     0.50, "Balanced portfolio. Recommended for most."),
    ("Aggressive (90% invested)",   0.90, "Max growth potential. Can lose big in crashes."),
]

# ── Screens ───────────────────────────────────────────────────────────────────

def splash_screen():
    clear()
    print()
    box("  LIFE AFTER GRADUATION  ")
    print()
    slow_print(wrap("Welcome to the financial simulation game where YOUR choices shape your future."))
    print()
    slow_print(wrap("Make decisions about careers, housing, debt, and lifestyle — then watch as AI-powered random events test your plan."))
    print()
    divider()
    slow_print("  Each playthrough is unique. Powered by Google Gemini.")
    divider()
    print()
    pause("  Press ENTER to begin your story...")

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
    slow_print(wrap("  Fresh diploma in hand, you scan the job listings. Which path calls to you?"))
    print()
    for i, (title, salary, stability, desc) in enumerate(CAREERS, 1):
        print(f"  [{i}] {title:<28} {fmt_money(salary)}/yr")
        print(f"      {desc}")
        print()
    idx = choose("Your career choice", [c[0] for c in CAREERS])
    c = CAREERS[idx]
    player.career = c[0]
    player.salary = c[1] * random.uniform(0.92, 1.10)  # salary variance
    player.job_stability = c[2]
    print()
    slow_print(f"  ✓ You accepted an offer as a {player.career} at {fmt_money(player.salary)}/yr.")

    # Gemini career story
    print()
    slow_print("  Generating your first week story...", 0.03)
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
    for i, (label, amount, desc) in enumerate(DEBT_OPTIONS, 1):
        print(f"  [{i}] {label:<25} {desc}")
    print()
    idx = choose("Your debt situation", [d[0] for d in DEBT_OPTIONS])
    d = DEBT_OPTIONS[idx]
    player.debt = d[1]
    if player.debt == 0:
        slow_print("\n  ✓ Debt-free! You're starting with a huge advantage.")
    else:
        slow_print(f"\n  ✓ You owe {fmt_money(player.debt)} in student loans.")
    pause()

    # ── Housing ──
    clear()
    box("WHERE WILL YOU LIVE?")
    print()
    slow_print(wrap("  The apartment search begins. What's your housing situation?"))
    print()
    for i, (label, cost, desc) in enumerate(HOUSING, 1):
        print(f"  [{i}] {label:<28} {fmt_money(cost)}/mo")
        print(f"      {desc}")
        print()
    idx = choose("Your housing choice", [h[0] for h in HOUSING])
    h = HOUSING[idx]
    player.housing = h[0]
    player.housing_cost = h[1]

    # Buying requires down payment
    if "Buy" in player.housing and player.savings < 20_000:
        slow_print("\n  ⚠  You don't have enough for a down payment. Switching to a solo apartment.")
        player.housing = "Solo Apartment"
        player.housing_cost = HOUSING[1][1]
    elif "Buy" in player.housing:
        player.savings -= 20_000
        slow_print(f"\n  ✓ Down payment made! {fmt_money(20_000)} removed from savings.")
    pause()

    # ── Lifestyle ──
    clear()
    box("CHOOSE YOUR LIFESTYLE")
    print()
    slow_print(wrap("  How do you want to live? This affects monthly spending, happiness, and stress."))
    print()
    for i, (label, cost, hap, stress, desc) in enumerate(LIFESTYLES, 1):
        print(f"  [{i}] {label:<22} {fmt_money(cost)}/mo  😊+{hap:+d}  😰{stress:+d}")
        print(f"      {desc}")
        print()
    idx = choose("Your lifestyle", [l[0] for l in LIFESTYLES])
    l = LIFESTYLES[idx]
    player.lifestyle = l[0]
    player.monthly_expenses = l[1]
    player.happiness = min(100, player.happiness + l[2])
    player.stress = max(0, min(100, player.stress + l[3]))
    pause()

    # ── Investment Strategy ──
    clear()
    box("INVESTMENT STRATEGY")
    print()
    slow_print(wrap("  Your HR portal asks how you'd like to handle your savings. What's your strategy?"))
    print()
    for i, (label, rate, desc) in enumerate(INVESTMENT_OPTIONS, 1):
        print(f"  [{i}] {label:<38} {rate*100:.0f}% in market")
        print(f"      {desc}")
        print()
    idx = choose("Your investment strategy", [inv[0] for inv in INVESTMENT_OPTIONS])
    inv = INVESTMENT_OPTIONS[idx]
    player.investment_rate = inv[1]
    slow_print(f"\n  ✓ Strategy set: {inv[0]}")
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
    """Present optional decisions the player can make during the year."""
    decisions = []

    # Debt payoff opportunity
    if player.debt > 0 and player.savings > 5_000:
        decisions.append(("Pay extra $2,000 toward debt", "debt_payoff"))

    # Side hustle
    decisions.append(("Start a side hustle (risk vs reward)", "side_hustle"))

    # Skill upgrade
    decisions.append(("Invest in a professional course ($500)", "upskill"))

    # Reduce lifestyle
    if player.lifestyle not in ("Frugal Minimalist",):
        decisions.append(("Cut back on spending (reduce lifestyle)", "cut_spending"))

    decisions.append(("Do nothing — stay the course", "nothing"))

    print()
    slow_print("  📋  MID-YEAR DECISION TIME")
    divider("-")
    slow_print(wrap("  Life keeps moving. What action will you take this year?"))
    idx = choose("Your action", [d[0] for d in decisions])
    action = decisions[idx][1]

    if action == "debt_payoff":
        extra = min(2_000, player.savings - 1_000)
        player.savings -= extra
        player.debt = max(0, player.debt - extra)
        slow_print(f"\n  💪 You put {fmt_money(extra)} extra toward your debt. Remaining: {fmt_money(player.debt)}")

    elif action == "side_hustle":
        success = random.random() < 0.55
        if success:
            income = random.randint(2_000, 8_000)
            player.savings += income
            player.stress = min(100, player.stress + 8)
            player.happiness = min(100, player.happiness + 5)
            slow_print(f"\n  🎉 Your side hustle paid off! You earned {fmt_money(income)} extra this year.")
        else:
            cost = random.randint(200, 800)
            player.savings -= cost
            player.stress = min(100, player.stress + 15)
            slow_print(f"\n  😓 The side hustle flopped. You lost {fmt_money(cost)} on tools and subscriptions.")

    elif action == "upskill":
        if player.savings >= 500:
            player.savings -= 500
            boost = random.randint(1_500, 4_000)
            player.salary += boost
            slow_print(f"\n  📚 Smart move! Your new skills earned you a {fmt_money(boost)}/yr raise next review.")
        else:
            slow_print("\n  ⚠  Not enough savings for the course right now.")

    elif action == "cut_spending":
        idx_life = [l[0] for l in LIFESTYLES].index(player.lifestyle)
        if idx_life > 0:
            new = LIFESTYLES[idx_life - 1]
            savings_gain = player.monthly_expenses - new[1]
            player.monthly_expenses = new[1]
            player.lifestyle = new[0]
            player.happiness = max(0, player.happiness + new[2] - LIFESTYLES[idx_life][2])
            slow_print(f"\n  ✂️  Downgraded to '{new[0]}'. Saving {fmt_money(savings_gain)}/mo more.")

    elif action == "nothing":
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
    """Possible job disruption."""
    roll = random.random()
    if roll > player.job_stability:
        # Job loss
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
        slow_print(wrap(f"  You were laid off from your {player.career} role and spent {months_out} months finding new work. You lost roughly {fmt_money(lost)} in income."))
        divider("═")
        pause()
    elif roll > 0.85:
        # Promotion
        boost = random.uniform(0.05, 0.15)
        player.salary *= (1 + boost)
        player.happiness = min(100, player.happiness + 10)
        print()
        slow_print(f"\n  🎊  PROMOTION! Your salary jumped {boost*100:.0f}% to {fmt_money(player.salary)}/yr!")
        pause()

# ── Year Loop ──────────────────────────────────────────────────────────────────

def run_year(player: Player):
    show_hud(player)

    # Mid-year decision
    mid_year_choices(player)

    # Random Gemini event (70% chance each year)
    if random.random() < 0.70:
        trigger_random_event(player)

    # Job stability roll
    job_event(player)

    # Annual financial update
    player.annual_update()

    # Year recap from Gemini
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
    """ASCII net worth over time."""
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

# ── Final Score ────────────────────────────────────────────────────────────────

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

    # Rating
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

    # Key events
    if player.events:
        slow_print("  📌  MEMORABLE EVENTS:")
        for e in player.events[-6:]:
            print(f"       • {e}")
    print()

    show_chart(player)

    # Gemini final verdict
    clear()
    box("YOUR FINANCIAL LEGACY")
    print()
    slow_print("  Generating your final life verdict...", 0.03)
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

    # How many years to simulate
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

    # Game loop
    for _ in range(years):
        run_year(player)

    final_screen(player)

    # Play again?
    print()
    again = input("  Play again? (y/n): ").strip().lower()
    if again == "y":
        main()
    else:
        slow_print("\n  Thanks for playing! May your finances be ever in your favour. 👋\n")


if __name__ == "__main__":
    main()