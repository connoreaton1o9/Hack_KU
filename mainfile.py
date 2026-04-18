#This is the top of the doc


#!/usr/bin/env python3
"""
Life After Graduation — Interactive Financial Planning Game
============================================================
A terminal-based simulation where you make life choices after college
and see how they play out over 15 years.
"""

import math
import os
import sys
import time

# ── ANSI color helpers ─────────────────────────────────────────────────────────
def clr(text, code): return f"\033[{code}m{text}\033[0m"
def bold(t):    return clr(t, "1")
def dim(t):     return clr(t, "2")
def green(t):   return clr(t, "92")
def red(t):     return clr(t, "91")
def yellow(t):  return clr(t, "93")
def blue(t):    return clr(t, "94")
def cyan(t):    return clr(t, "96")
def magenta(t): return clr(t, "95")

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def slow_print(text, delay=0.012):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def divider(char="─", width=60):
    print(dim(char * width))

def press_enter():
    input(dim("\n  Press Enter to continue…"))

# ── Chapter data ───────────────────────────────────────────────────────────────
CHAPTERS = [
    {
        "id": "career",
        "label": "Chapter 1  ·  Age 22",
        "title": "The first fork in the road",
        "story": (
            "It's graduation week. Your inbox has two responses. Your phone keeps\n"
            "  buzzing with your parents asking about your plans. What you choose\n"
            "  now will shape the next decade."
        ),
        "choices": [
            {
                "id": "bigtech",
                "icon": "[💻]",
                "title": "Big Tech job",
                "desc": "$95K salary at a large tech company. High pressure, long hours,\n"
                        "         but strong comp and rapid career growth.",
                "tags": [green("income↑"), red("stress↑"), blue("growth↑")],
                "salary": 95000, "stress": 7, "growth": 9,
            },
            {
                "id": "nonprofit",
                "icon": "[🌱]",
                "title": "Nonprofit work",
                "desc": "$42K at a mission-driven org. Meaningful work and PSLF\n"
                        "         loan forgiveness eligibility after 10 years.",
                "tags": [green("fulfillment↑"), blue("forgiveness"), yellow("income↓")],
                "salary": 42000, "stress": 4, "growth": 5,
            },
            {
                "id": "startup",
                "icon": "[🚀]",
                "title": "Early-stage startup",
                "desc": "$65K + equity. Risky but with real upside potential.\n"
                        "         60% chance the company succeeds.",
                "tags": [green("equity"), red("risk↑"), blue("learning↑")],
                "salary": 65000, "stress": 8, "growth": 8,
            },
            {
                "id": "gradschool",
                "icon": "[📚]",
                "title": "Graduate school",
                "desc": "2-year program, $22K stipend or $60K more loans.\n"
                        "         Higher earning ceiling afterwards.",
                "tags": [blue("credentials"), red("debt risk"), green("ceiling↑")],
                "salary": 22000, "stress": 6, "growth": 7,
            },
        ],
    },
    {
        "id": "housing",
        "label": "Chapter 2  ·  Age 23",
        "title": "Where do you live?",
        "story": (
            "Your lease is up. Rent in your city just jumped 18%. Your college\n"
            "  roommate wants to buy a house together. A family friend offers a\n"
            "  cheap room back home. What's the move?"
        ),
        "choices": [
            {
                "id": "rent_city",
                "icon": "[🏙️]",
                "title": "Rent in the city",
                "desc": "$1,800/mo for a 1BR. Close to work and social life,\n"
                        "         but expensive.",
                "tags": [blue("convenience"), red("high cost")],
                "rent": 1800, "savings_mod": -0.15, "equity": 0,
            },
            {
                "id": "buy_house",
                "icon": "[🏠]",
                "title": "Buy with roommate",
                "desc": "Split a starter home. $2,200/mo mortgage total ($1,100\n"
                        "         each). Builds equity but illiquid.",
                "tags": [green("equity"), yellow("illiquid"), red("risk")],
                "rent": 1100, "savings_mod": 0.05, "equity": 120000,
            },
            {
                "id": "rent_cheap",
                "icon": "[🏘️]",
                "title": "Cheap suburban rental",
                "desc": "$950/mo with roommates. Long commute, but frees up\n"
                        "         significant monthly cash.",
                "tags": [green("savings↑"), red("commute")],
                "rent": 950, "savings_mod": 0.20, "equity": 0,
            },
            {
                "id": "family",
                "icon": "[👨‍👩‍👧]",
                "title": "Move back home",
                "desc": "$300/mo to family. Maximum savings potential with\n"
                        "         some social tradeoffs.",
                "tags": [green("max savings"), yellow("social↓")],
                "rent": 300, "savings_mod": 0.35, "equity": 0,
            },
        ],
    },
    {
        "id": "debt",
        "label": "Chapter 3  ·  Age 24",
        "title": "Dealing with the loans",
        "story": (
            "You have $38,000 in student loans (more if grad school). Your\n"
            "  6-month grace period just ended. The minimum payment is $380/month.\n"
            "  But there are other strategies worth considering."
        ),
        "choices": [
            {
                "id": "minimum",
                "icon": "[🐢]",
                "title": "Minimum payments",
                "desc": "Pay $380/mo. Keep cash free for investing and life.\n"
                        "         Loans paid off in ~10 years.",
                "tags": [green("cash flow"), red("interest↑")],
                "debt_payment": 380, "debt_years": 10, "invest_mod": 1.0,
            },
            {
                "id": "aggressive",
                "icon": "[💪]",
                "title": "Aggressive payoff",
                "desc": "Pay $1,200/mo. Debt-free in ~3 years, then redirect\n"
                        "         everything to investing.",
                "tags": [green("debt-free"), red("cash-poor")],
                "debt_payment": 1200, "debt_years": 3, "invest_mod": 0.4,
            },
            {
                "id": "refinance",
                "icon": "[🔄]",
                "title": "Refinance + balance",
                "desc": "Refinance to 4.5% rate, pay $600/mo. A middle path\n"
                        "         between speed and flexibility.",
                "tags": [green("lower rate"), blue("balanced")],
                "debt_payment": 600, "debt_years": 7, "invest_mod": 0.7,
            },
            {
                "id": "forgiveness",
                "icon": "[🎁]",
                "title": "Pursue forgiveness",
                "desc": "Income-driven plan ($180/mo). Aim for PSLF if at\n"
                        "         nonprofit. Long game, but potentially powerful.",
                "tags": [green("low payments"), yellow("risky"), blue("long term")],
                "debt_payment": 180, "debt_years": 20, "invest_mod": 1.2,
            },
        ],
    },
    {
        "id": "lifestyle",
        "label": "Chapter 4  ·  Age 26",
        "title": "The upgrade temptation",
        "story": (
            "Two years in, you got a raise. You're making more, but lifestyle\n"
            "  creep is real. Your friends are booking European vacations. Your\n"
            "  car just died. How do you handle the extra income?"
        ),
        "choices": [
            {
                "id": "lifestyle_up",
                "icon": "[✈️]",
                "title": "Upgrade your lifestyle",
                "desc": "New car, nice apartment, travel twice a year. Enjoy the\n"
                        "         fruits of your hard work now.",
                "tags": [green("enjoyment"), red("savings↓")],
                "lifestyle_cost": 1500, "savings_rate_boost": -0.03, "side_income": 0,
            },
            {
                "id": "invest_first",
                "icon": "[📈]",
                "title": "Invest most of the raise",
                "desc": "Keep lifestyle flat, funnel 80% of raise into index\n"
                        "         funds and max out 401k contributions.",
                "tags": [green("wealth↑"), blue("discipline")],
                "lifestyle_cost": 300, "savings_rate_boost": 0.12, "side_income": 0,
            },
            {
                "id": "balanced_life",
                "icon": "[⚖️]",
                "title": "Balance it out",
                "desc": "50/50 split: half the raise to lifestyle improvements,\n"
                        "         half to savings. A sustainable middle path.",
                "tags": [blue("balance"), green("steady")],
                "lifestyle_cost": 700, "savings_rate_boost": 0.06, "side_income": 0,
            },
            {
                "id": "side_hustle",
                "icon": "[💡]",
                "title": "Start a side hustle",
                "desc": "Launch freelance work. Extra $15K/yr potential, but\n"
                        "         costs ~15 hours per week.",
                "tags": [green("income+"), red("time↓"), blue("optionality")],
                "lifestyle_cost": 400, "savings_rate_boost": 0.15, "side_income": 15000,
            },
        ],
    },
    {
        "id": "emergency",
        "label": "Chapter 5  ·  Age 28",
        "title": "When life hits hard",
        "story": (
            "It's been 6 years since graduation. Out of nowhere: a layoff,\n"
            "  a medical bill, or a family emergency totaling $8-12K.\n"
            "  How prepared are you — and how do you respond?"
        ),
        "choices": [
            {
                "id": "prepared",
                "icon": "[🛡️]",
                "title": "Use the emergency fund",
                "desc": "You have 6 months of expenses saved. Bridge the gap\n"
                        "         without touching investments.",
                "tags": [green("resilient"), blue("prepared")],
                "emergency_cost": 0, "stress_event": False,
            },
            {
                "id": "credit",
                "icon": "[💳]",
                "title": "Put it on credit cards",
                "desc": "Charge $8,000 at 22% APR. Takes 18 months to pay off.\n"
                        "         A significant but recoverable setback.",
                "tags": [yellow("quick fix"), red("debt+")],
                "emergency_cost": 8000, "stress_event": True,
            },
            {
                "id": "withdraw_401k",
                "icon": "[📉]",
                "title": "Withdraw from 401k",
                "desc": "Pull $12K early. 10% penalty + income tax + you lose\n"
                        "         all future compound growth on that money.",
                "tags": [yellow("available"), red("costly"), red("penalty")],
                "emergency_cost": 16000, "stress_event": True,
            },
            {
                "id": "family_loan",
                "icon": "[🤝]",
                "title": "Borrow from family",
                "desc": "Interest-free loan from family. Paid back over 2 years.\n"
                        "         Some relational tension as a side effect.",
                "tags": [green("low cost"), yellow("relational")],
                "emergency_cost": 2000, "stress_event": False,
            },
        ],
    },
]

# ── Rendering helpers ──────────────────────────────────────────────────────────
def render_intro():
    clear()
    print()
    print(bold("  🎓  Life After Graduation"))
    print(dim("  ─────────────────────────────────────────────────────────────"))
    slow_print(
        "  You just graduated. You have a degree, some debt, and a world of\n"
        "  choices ahead. Every decision you make in the next 15 years will\n"
        "  shape your financial future.\n",
        delay=0.008,
    )
    print(f"  {dim('Age 22 — Graduation')}   {dim('5 chapters ahead')}   {dim('Your path, your rules')}")
    print()
    input(bold("  Press Enter to begin your journey → "))


def render_chapter(chapter, current_idx, selections):
    clear()
    print()
    total = len(CHAPTERS)

    # progress bar
    bar = ""
    for i in range(total):
        if i < current_idx:
            bar += green("●")
        elif i == current_idx:
            bar += cyan("●")
        else:
            bar += dim("○")
        if i < total - 1:
            bar += dim("─")
    print(f"  {bar}  {dim(f'Chapter {current_idx+1} of {total}')}")
    print()

    print(f"  {dim(chapter['label'])}")
    print(f"  {bold(chapter['title'])}")
    divider()
    print(f"  {dim(chapter['story'])}")
    print()

    choices = chapter["choices"]
    already = selections.get(chapter["id"])

    for i, c in enumerate(choices, 1):
        marker = cyan(f"[{i}]") if already == c["id"] else dim(f" {i} ")
        sel_indicator = green(" ✓") if already == c["id"] else "  "
        print(f"  {marker}{sel_indicator} {bold(c['icon'])} {bold(c['title'])}")
        print(f"         {c['desc']}")
        tags_str = "  ".join(c["tags"])
        print(f"         {tags_str}")
        print()

    return choices


def prompt_choice(chapter, choices, selections):
    already = selections.get(chapter["id"])
    while True:
        if already:
            cur_idx = next((i for i, c in enumerate(choices) if c["id"] == already), None)
            suffix = f" [currently {cur_idx+1}]" if cur_idx is not None else ""
        else:
            suffix = ""
        raw = input(f"  Choose 1–{len(choices)}{suffix}: ").strip()
        if raw == "" and already:
            return already
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]["id"]
        print(red(f"  Please enter a number between 1 and {len(choices)}."))


# ── Simulation math ────────────────────────────────────────────────────────────
def compute_results(selections):
    career   = next(c for c in CHAPTERS[0]["choices"] if c["id"] == selections["career"])
    housing  = next(c for c in CHAPTERS[1]["choices"] if c["id"] == selections["housing"])
    debt     = next(c for c in CHAPTERS[2]["choices"] if c["id"] == selections["debt"])
    lifestyle= next(c for c in CHAPTERS[3]["choices"] if c["id"] == selections["lifestyle"])
    emergency= next(c for c in CHAPTERS[4]["choices"] if c["id"] == selections["emergency"])

    salary = career["salary"]
    if selections["career"] == "gradschool":
        salary = 90000
    salary_growth = career["growth"] * 0.01 + 0.02
    side_income = lifestyle.get("side_income", 0)

    student_debt = 38000
    if selections["career"] == "gradschool":
        student_debt = 98000
    if selections["debt"] == "forgiveness" and selections["career"] == "nonprofit":
        student_debt = 0

    debt_payment  = debt["debt_payment"]
    debt_years    = min(debt["debt_years"], 10)
    invest_mod    = debt["invest_mod"]
    savings_boost = lifestyle["savings_rate_boost"]
    rent          = housing["rent"]
    savings_mod   = housing["savings_mod"]
    emergency_cost= emergency["emergency_cost"]
    house_equity  = housing.get("equity", 0)

    base_savings_rate = 0.10 + savings_boost + savings_mod
    savings_rate = max(0.03, min(0.45, base_savings_rate))

    net_worth_by_year = []
    investments = 0.0
    remaining_debt = float(student_debt)
    current_salary = float(salary)
    net_worth = -float(student_debt)
    net_worth_by_year.append({"age": 22, "nw": round(net_worth)})

    for yr in range(1, 16):
        current_salary *= (1 + salary_growth)
        annual_income  = current_salary + side_income
        annual_savings = annual_income * savings_rate * invest_mod
        annual_debt_pay= debt_payment * 12 if yr <= debt_years else 0
        remaining_debt = max(0, remaining_debt - annual_debt_pay)
        investments    = (investments + max(0, annual_savings)) * 1.07
        if yr == 6:
            investments = max(0, investments - emergency_cost)
        equity_value = house_equity * (1 + 0.04 * yr) - house_equity if house_equity else 0
        net_worth = investments - remaining_debt + equity_value
        net_worth_by_year.append({"age": 22 + yr, "nw": round(net_worth)})

    final_nw     = net_worth
    final_salary = round(current_salary + side_income)
    debt_free_age = 22 + debt_years

    # score
    score = 50
    if final_nw > 200000:  score += 20
    elif final_nw > 100000: score += 10
    elif final_nw < 0:      score -= 20
    if savings_rate > 0.15: score += 10
    if emergency["stress_event"]: score -= 10
    if selections["housing"] in ("buy_house", "family"): score += 5
    score = max(12, min(99, score))

    events = [
        {"age": 22, "icon": "🎓", "text": f"Graduated. Accepted {career['title']} offer."},
        {"age": 23, "icon": "🏠", "text": f"Housing: {housing['title']}. Monthly cost: ${rent:,}."},
        {"age": 24, "icon": "💸", "text": f"Debt strategy: {debt['title']} on ${student_debt:,} in loans."},
    ]
    if selections["career"] == "gradschool":
        events.append({"age": 24, "icon": "📚", "text": "Finished grad school, started higher-paying career."})
    events.append({"age": 26, "icon": "💰", "text": f"Got a raise. Choice: {lifestyle['title']}."})
    if side_income:
        events.append({"age": 27, "icon": "💡", "text": f"Side hustle generating ~${side_income//1000}K/yr."})
    events.append({"age": 28, "icon": "⚠️" if emergency["stress_event"] else "✅",
                   "text": f"Emergency hit. Response: {emergency['title']}. Cost: ${emergency_cost:,}."})
    if debt_free_age <= 37:
        events.append({"age": debt_free_age, "icon": "🎉", "text": "Student loans fully paid off!"})
    events.append({"age": 37, "icon": "📊",
                   "text": f"Net worth reaches ${round(final_nw/1000)}K at age 37."})

    return {
        "net_worth_by_year": net_worth_by_year,
        "final_nw": final_nw,
        "final_salary": final_salary,
        "score": score,
        "events": events,
        "savings_rate": savings_rate,
        "debt_free_age": debt_free_age,
        "career": career,
        "housing": housing,
        "lifestyle": lifestyle,
        "emergency": emergency,
    }


# ── ASCII net-worth chart ──────────────────────────────────────────────────────
def ascii_chart(data_points, width=54, height=10):
    values = [d["nw"] for d in data_points]
    ages   = [d["age"] for d in data_points]
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        max_v = min_v + 1

    def normalize(v):
        return int((v - min_v) / (max_v - min_v) * (height - 1))

    grid = [[" "] * width for _ in range(height)]
    step = max(1, len(values) // width)
    sampled = values[::step][:width]

    for x, v in enumerate(sampled):
        y = normalize(v)
        row = height - 1 - y
        char = green("█") if v >= 0 else red("█")
        grid[row][x] = char

    lines = []
    for r, row in enumerate(grid):
        frac = 1 - r / (height - 1)
        label_v = min_v + frac * (max_v - min_v)
        label = f"${label_v/1000:>5.0f}K"
        lines.append(f"  {dim(label)} │ {''.join(row)}")

    x_axis = "  " + " " * 9 + "└" + "─" * width
    age_label = (
        "  " + " " * 10
        + dim(f"Age {ages[0]}")
        + " " * (width // 2 - 6)
        + dim(f"Age {ages[len(ages)//2]}")
        + " " * (width // 2 - 8)
        + dim(f"Age {ages[-1]}")
    )
    return "\n".join(lines) + "\n" + x_axis + "\n" + age_label


def get_top_insight(selections, r):
    if selections["career"] == "bigtech":
        return ("Your high starting salary accelerated compound growth from day one —\n"
                "    the single biggest lever in the simulation.")
    if selections["housing"] in ("family", "rent_cheap"):
        return ("Low housing costs in your early years freed up capital that\n"
                "    compounded significantly over time.")
    if selections["lifestyle"] == "invest_first":
        return ("Investing most of your raise before lifestyle inflated was the\n"
                "    highest-leverage decision of your mid-20s.")
    return ("Staying disciplined through multiple life transitions helped you\n"
            "    maintain steady savings momentum.")

def get_worst_insight(selections, r):
    if selections["emergency"] == "withdraw_401k":
        return ("Withdrawing from your 401k cost you both the penalty/tax and\n"
                "    years of future compound growth on that money.")
    if selections["emergency"] == "credit":
        return ("High-interest credit card debt during the emergency erased\n"
                "    months of savings progress.")
    if selections["lifestyle"] == "lifestyle_up":
        return ("Upgrading lifestyle after your raise locked in high fixed costs\n"
                "    before your savings base was strong enough.")
    if selections["housing"] == "rent_city":
        return ("City rent consumed a large share of income, limiting how much\n"
                "    you could invest during your prime compounding years.")
    return ("Without a tight savings strategy, small spending decisions\n"
            "    gradually eroded your savings rate.")

def get_advice(selections, r):
    if r["final_nw"] < 50000:
        return ("Try maxing your 401k first — the tax break alone improves\n"
                "    outcomes, and it forces savings discipline automatically.")
    if selections["emergency"] in ("credit", "withdraw_401k"):
        return ("Build a 3-6 month emergency fund before aggressive investing.\n"
                "    One crisis without a buffer can set you back 2-3 years.")
    if selections["lifestyle"] == "lifestyle_up":
        return ("Try 'pay yourself first': automate savings before you see the\n"
                "    money so lifestyle spending is naturally constrained.")
    return ("You're on a solid path. Next frontier: Roth IRA, HSA, and\n"
            "    making sure your allocation matches your time horizon.")


# ── Results screen ─────────────────────────────────────────────────────────────
def render_results(selections):
    r = compute_results(selections)
    clear()
    print()
    print(dim("  ── Your financial story ──────────────────────────────────────"))
    print(f"  {bold('Age 37: Your financial snapshot')}")
    print()

    # score ring (text version)
    score = r["score"]
    if score >= 65:
        score_color, grade = green, "Strong"
    elif score >= 45:
        score_color, grade = yellow, "Steady"
    else:
        score_color, grade = red, "Rebuilding"

    print(f"  Financial score: {score_color(bold(str(score)))} / 99  {dim(f'({grade})')}")
    print()

    # outcome banner
    nw = r["final_nw"]
    nw_str = f"${round(nw/1000)}K" if nw >= 0 else f"-${round(abs(nw)/1000)}K"
    if score >= 65:
        print(green("  ┌─ Strong financial foundation built ─────────────────────┐"))
        print(green(f"  │ Net worth {nw_str} · Salary ${round(r['final_salary']/1000)}K/yr                       │"))
        print(green("  │ Disciplined choices compounded powerfully over 15 years.  │"))
        print(green("  └──────────────────────────────────────────────────────────┘"))
    elif score >= 45:
        print(yellow("  ┌─ Steady progress, room to grow ─────────────────────────┐"))
        print(yellow(f"  │ Net worth {nw_str} · Salary ${round(r['final_salary']/1000)}K/yr                       │"))
        print(yellow("  │ Reasonable choices, but a few tradeoffs slowed momentum.  │"))
        print(yellow("  └──────────────────────────────────────────────────────────┘"))
    else:
        print(red("  ┌─ Rebuilding is always possible ─────────────────────────┐"))
        print(red(f"  │ Net worth {nw_str} · Salary ${round(r['final_salary']/1000)}K/yr                       │"))
        print(red("  │ Setbacks hit hard. The next 15 years can change the arc.  │"))
        print(red("  └──────────────────────────────────────────────────────────┘"))
    print()

    # metrics
    divider()
    print(f"  {bold('Key metrics at age 37')}")
    divider()
    print(f"  Net worth        {score_color(bold(nw_str))}")
    print(f"  Annual salary    {bold('$'+str(round(r['final_salary']/1000))+'K')}")
    print(f"  Debt-free age    {bold(str(r['debt_free_age']))}")
    print(f"  Savings rate     {bold(str(round(r['savings_rate']*100))+'%')}")
    print()

    # chart
    divider()
    print(f"  {bold('Net worth over time')}")
    divider()
    print(ascii_chart(r["net_worth_by_year"]))
    print()

    # timeline
    divider()
    print(f"  {bold('Key life events')}")
    divider()
    for e in sorted(r["events"], key=lambda x: x["age"]):
        age_str = f"Age {e['age']:>2}"
        print(f"  {dim(age_str)}  {e['icon']}  {e['text']}")
    print()

    # insights
    divider()
    print(f"  {bold('Insights')}")
    divider()
    print(f"  {green('What helped most')}")
    print(f"    {get_top_insight(selections, r)}")
    print()
    print(f"  {red('What hurt most')}")
    print(f"    {get_worst_insight(selections, r)}")
    print()
    print(f"  {blue('What to change next time')}")
    print(f"    {get_advice(selections, r)}")
    print()
    print(f"  {cyan('The compound effect')}")
    print(f"    Every extra $100/mo saved at 22 becomes ~$5,800 by age 37")
    print(f"    at a 7% return. Your choices determined how much of that")
    print(f"    potential you captured.")
    print()
    divider()


# ── Main game loop ─────────────────────────────────────────────────────────────
def main():
    while True:
        render_intro()
        selections = {}

        i = 0
        while i < len(CHAPTERS):
            ch = CHAPTERS[i]
            choices = render_chapter(ch, i, selections)
            print(dim("  (Press Enter to keep current selection, or type a number)") if selections.get(ch["id"]) else "")

            nav = input(f"\n  Enter choice 1–{len(choices)}"
                        + (f", or B to go back" if i > 0 else "")
                        + ": ").strip().lower()

            if nav == "b" and i > 0:
                i -= 1
                continue

            if nav == "" and selections.get(ch["id"]):
                i += 1
                continue

            if nav.isdigit() and 1 <= int(nav) <= len(choices):
                selections[ch["id"]] = choices[int(nav) - 1]["id"]
                i += 1
            else:
                print(red(f"  Please enter a number 1–{len(choices)}" + (" or B to go back." if i > 0 else ".")))

        render_results(selections)

        again = input("  Play again? [y/N]: ").strip().lower()
        if again != "y":
            print()
            print(bold("  Thanks for playing. Your real financial story starts now. 🎓"))
            print()
            break


if __name__ == "__main__":
    main()