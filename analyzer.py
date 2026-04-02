import re
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Path for persisting streak data
STREAK_DATA_PATH = os.path.join(os.path.expandvars("%APPDATA%"), "AdharshBrowserAuditor", "wellness_streak.json")


class BrowserHistoryAnalyzer:
    def __init__(self):
        # Premium/Enterprise categorization dictionaries — 6 distinct categories
        self.categories = {
            "Productivity & Development": {
                "keywords": ["github", "stackoverflow", "docs", "api", "vscode", "python",
                             "javascript", "react", "programming", "tutorial", "learn",
                             "course", "udemy", "coursera", "edx", "codecademy",
                             "freecodecamp", "leetcode", "hackerrank", "geeksforgeeks",
                             "w3schools", "mdn", "developer", "coding", "devops",
                             "docker", "kubernetes", "npm", "pypi", "gitlab"],
                "icon": "💻",
                "color": "#3b82f6",  # Primary blue
                "weight": 1.0       # Positive weight for wellness score
            },
            "Career & Professional": {
                "keywords": ["linkedin", "indeed", "naukri", "glassdoor", "resume", "cv",
                             "portfolio", "interview", "hiring", "job", "career",
                             "internship", "placement", "recruit", "salary", "apna",
                             "monster", "ziprecruiter", "angel.co", "wellfound",
                             "upwork", "freelancer", "fiverr", "toptal"],
                "icon": "💼",
                "color": "#10b981",
                "weight": 1.0
            },
            "News & Information": {
                "keywords": ["news", "bbc", "cnn", "nytimes", "forbes", "bloomberg",
                             "reuters", "wsj", "thehindu", "timesofindia", "weather",
                             "wiki", "article", "ndtv", "aljazeera", "guardian",
                             "washingtonpost", "quora", "medium", "substack",
                             "hindustan", "republic", "livemint", "scroll"],
                "icon": "📰",
                "color": "#8b5cf6",
                "weight": 0.8
            },
            "Social Media": {
                "keywords": ["instagram", "facebook", "twitter", "reddit", "tiktok",
                             "snapchat", "pinterest", "tumblr", "discord",
                             "telegram", "whatsapp", "messenger", "wechat",
                             "linkedin.com/feed", "threads", "mastodon", "bluesky",
                             "x.com", "meta.com"],
                "icon": "💬",
                "color": "#06b6d4",
                "weight": 0.3       # Moderate — not harmful but not productive
            },
            "Entertainment": {
                "keywords": ["youtube", "netflix", "primevideo", "spotify", "twitch",
                             "gaming", "steam", "movie", "song", "music", "hotstar",
                             "jiocinema", "sonyliv", "zee5", "voot", "crunchyroll",
                             "anime", "manga", "imdb", "rotten", "hulu",
                             "disneyplus", "epic games", "xbox", "playstation",
                             "valorant", "minecraft", "roblox"],
                "icon": "🎮",
                "color": "#f59e0b",
                "weight": 0.2
            },
            "Adult & NSFW": {
                "keywords": ["porn", "sex", "nude", "nsfw", "xxx", "onlyfans",
                             "xvideos", "pornhub", "rule34", "hentai",
                             "xhamster", "redtube", "brazzers", "chaturbate",
                             "stripchat", "livejasmin"],
                "icon": "🔞",
                "color": "#db2777",
                "weight": -0.5      # Negative weight
            }
        }

        # Critical intervention triggers — grouped by concern type
        self.critical_triggers = {
            "self_harm": {
                "keywords": [
                    "suicide", "kill myself", "want to die", "how to tie a noose",
                    "painless death", "end it all", "overdose", "self harm",
                    "ways to die", "depression help", "cut myself", "hurt myself",
                    "ending my life", "no reason to live", "better off dead",
                    "suicidal thoughts", "can't go on", "take my life",
                    "jump off", "wrist cutting", "slit wrist", "hang myself",
                    "i want to disappear", "goodbye letter", "suicide note",
                    "nothing to live for", "life is pointless"
                ],
                "severity": "CRITICAL",
                "score_penalty": -40
            },
            "violence": {
                "keywords": [
                    "how to make a bomb", "build explosive", "make a weapon",
                    "mass shooting", "attack plan", "pipe bomb", "terrorism",
                    "how to make poison", "school attack", "shooting plan",
                    "bomb threat", "kill people", "revenge attack",
                    "homemade explosive", "ricin", "anthrax"
                ],
                "severity": "CRITICAL",
                "score_penalty": -50
            },
            "academic_stress": {
                "keywords": [
                    "exam stress", "failing exam", "academic pressure",
                    "can't study", "too much pressure", "hate school",
                    "drop out", "academic anxiety", "exam fear",
                    "failing grades", "study burnout", "can't concentrate",
                    "parents pressure", "board exam stress", "jee stress",
                    "neet pressure", "competitive exam pressure",
                    "academic depression", "study depression",
                    "college stress", "homework anxiety"
                ],
                "severity": "WARNING",
                "score_penalty": -20
            }
        }

        # Wellness resources for each trigger type
        self.wellness_resources = {
            "self_harm": {
                "title": "💛 You Are Not Alone — Help Is Available",
                "icon": "🤝",
                "color": "#ef4444",
                "message": (
                    "If you or someone you know is struggling with thoughts of "
                    "self-harm or suicide, please know that help is just a call away. "
                    "You matter, and people care about you deeply."
                ),
                "hotlines": [
                    {"name": "National Suicide Prevention Lifeline (US)", "number": "988", "type": "call"},
                    {"name": "Crisis Text Line (US)", "number": "Text HOME to 741741", "type": "text"},
                    {"name": "iCall (India)", "number": "+91-9152987821", "type": "call"},
                    {"name": "Vandrevala Foundation (India)", "number": "1860-2662-345", "type": "call"},
                    {"name": "AASRA (India)", "number": "+91-9820466726", "type": "call"},
                    {"name": "Snehi (India)", "number": "+91-44-2464 0050", "type": "call"},
                    {"name": "Samaritans (UK)", "number": "116 123", "type": "call"},
                ],
                "web_resources": [
                    "https://988lifeline.org",
                    "https://www.crisistextline.org",
                    "https://icallhelpline.org"
                ]
            },
            "violence": {
                "title": "🚨 Report Concerning Activity",
                "icon": "⚠️",
                "color": "#dc2626",
                "message": (
                    "If you have information about a potential threat or harmful activity, "
                    "please report it immediately to the appropriate authorities. "
                    "Your action could save lives."
                ),
                "hotlines": [
                    {"name": "Emergency Services (US)", "number": "911", "type": "call"},
                    {"name": "Emergency Services (India)", "number": "112", "type": "call"},
                    {"name": "FBI Tips (US)", "number": "1-800-CALL-FBI", "type": "call"},
                    {"name": "Anti-Terror Helpline (India)", "number": "1800-11-3600", "type": "call"},
                ],
                "web_resources": [
                    "https://tips.fbi.gov",
                    "https://www.mha.gov.in"
                ]
            },
            "academic_stress": {
                "title": "📚 Academic Support Is Available",
                "icon": "🌟",
                "color": "#f59e0b",
                "message": (
                    "Academic pressure is real, and it's completely okay to feel overwhelmed. "
                    "You are more than your grades. Reaching out for support is a sign of "
                    "strength, not weakness. Let someone help you through this."
                ),
                "hotlines": [
                    {"name": "Student Helpline (India)", "number": "1800-599-0019", "type": "call"},
                    {"name": "Crisis Text Line (US)", "number": "Text HELLO to 741741", "type": "text"},
                    {"name": "iCall (India)", "number": "+91-9152987821", "type": "call"},
                    {"name": "Childline India", "number": "1098", "type": "call"},
                    {"name": "NIMHANS (India)", "number": "+91-80-46110007", "type": "call"},
                ],
                "web_resources": [
                    "https://icallhelpline.org",
                    "https://www.nimhans.ac.in"
                ]
            }
        }

        # Time-of-day slots for heatmap
        self.time_slots = {
            "🌅 Early Morning (5-8 AM)":   (5, 8),
            "☀️ Morning (8 AM-12 PM)":     (8, 12),
            "🌤️ Afternoon (12-4 PM)":      (12, 16),
            "🌇 Evening (4-8 PM)":          (16, 20),
            "🌙 Night (8 PM-12 AM)":        (20, 24),
            "🌑 Late Night (12-5 AM)":      (0, 5),
        }

    def analyze_history(self, history_data):
        """
        Analyzes a list of history dictionaries containing 'url', 'title', and 'time'.
        Returns categorization, wellness score, time heatmap, trend analysis, and alerts.
        """
        results = {
            "total_analyzed": 0,
            "categories": {cat: {"count": 0, "color": data["color"], "icon": data["icon"], "entries": []}
                           for cat, data in self.categories.items()},
            "uncategorized": {"count": 0, "color": "#64748b", "icon": "❓", "entries": []},
            "needs_intervention": False,
            "triggered_types": [],
            "critical_matches": [],
            "wellness_resources": [],
            # New fields
            "wellness_score": 100,
            "wellness_grade": "A+",
            "wellness_color": "#10b981",
            "wellness_label": "Excellent",
            "time_heatmap": {slot: 0 for slot in self.time_slots},
            "late_night_concern": False,
            "late_night_harmful_count": 0,
            "trends": {},
            "streak_days": 0,
            "is_healthy": True,
        }

        if not history_data:
            results["streak_days"] = self._load_streak()
            return results

        # Tracking for trends (entries by week)
        this_week_cats = defaultdict(int)
        last_week_cats = defaultdict(int)
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        for entry in history_data:
            url = entry.get("url", "").lower()
            title = entry.get("title", "").lower()
            combined_text = f"{url} {title}"

            if not combined_text.strip():
                continue

            results["total_analyzed"] += 1
            categorized = False

            # Parse timestamp for heatmap & trend
            entry_time = self._parse_time(entry.get("time", ""))

            # Time-of-day heatmap
            if entry_time:
                hour = entry_time.hour
                for slot_name, (start_h, end_h) in self.time_slots.items():
                    if start_h <= hour < end_h:
                        results["time_heatmap"][slot_name] += 1
                        break

            # Check critical triggers first
            is_harmful = False
            for trigger_type, trigger_data in self.critical_triggers.items():
                for keyword in trigger_data["keywords"]:
                    if re.search(rf"\b{re.escape(keyword)}\b", combined_text):
                        results["needs_intervention"] = True
                        results["is_healthy"] = False
                        is_harmful = True
                        if trigger_type not in results["triggered_types"]:
                            results["triggered_types"].append(trigger_type)
                        results["critical_matches"].append({
                            "time": entry.get("time", "Unknown"),
                            "title": entry.get("title", "Unknown"),
                            "url": entry.get("url", ""),
                            "trigger_type": trigger_type,
                            "severity": trigger_data["severity"]
                        })
                        # Check if late-night harmful
                        if entry_time and (0 <= entry_time.hour < 5):
                            results["late_night_harmful_count"] += 1
                            results["late_night_concern"] = True
                        break

            # Categorize the entry
            matched_cat = None
            for cat, data in self.categories.items():
                for keyword in data["keywords"]:
                    if keyword in combined_text:
                        results["categories"][cat]["count"] += 1
                        results["categories"][cat]["entries"].append(entry)
                        categorized = True
                        matched_cat = cat
                        break
                if categorized:
                    break

            if not categorized:
                results["uncategorized"]["count"] += 1
                results["uncategorized"]["entries"].append(entry)

            # Trend tracking: this week vs last week
            if entry_time:
                cat_for_trend = matched_cat or "Uncategorized"
                if entry_time >= week_ago:
                    this_week_cats[cat_for_trend] += 1
                elif entry_time >= two_weeks_ago:
                    last_week_cats[cat_for_trend] += 1

        # Calculate percentages
        total = results["total_analyzed"]
        if total > 0:
            for cat in results["categories"]:
                count = results["categories"][cat]["count"]
                results["categories"][cat]["percentage"] = (count / total) * 100
            results["uncategorized"]["percentage"] = (results["uncategorized"]["count"] / total) * 100
        else:
            for cat in results["categories"]:
                results["categories"][cat]["percentage"] = 0
            results["uncategorized"]["percentage"] = 0

        # Attach wellness resources
        for trigger_type in results["triggered_types"]:
            if trigger_type in self.wellness_resources:
                results["wellness_resources"].append(self.wellness_resources[trigger_type])

        # ===== WELLNESS SCORE CALCULATION (1-100) =====
        results["wellness_score"] = self._compute_wellness_score(results, total)
        score = results["wellness_score"]

        if score >= 85:
            results["wellness_grade"] = "A+"
            results["wellness_color"] = "#10b981"
            results["wellness_label"] = "Excellent"
        elif score >= 70:
            results["wellness_grade"] = "A"
            results["wellness_color"] = "#22c55e"
            results["wellness_label"] = "Good"
        elif score >= 55:
            results["wellness_grade"] = "B"
            results["wellness_color"] = "#eab308"
            results["wellness_label"] = "Moderate"
        elif score >= 40:
            results["wellness_grade"] = "C"
            results["wellness_color"] = "#f97316"
            results["wellness_label"] = "Concerning"
        else:
            results["wellness_grade"] = "D"
            results["wellness_color"] = "#ef4444"
            results["wellness_label"] = "Needs Attention"

        if score < 55:
            results["is_healthy"] = False

        # ===== TREND ANALYSIS =====
        all_trend_cats = set(list(this_week_cats.keys()) + list(last_week_cats.keys()))
        for cat in all_trend_cats:
            tw = this_week_cats.get(cat, 0)
            lw = last_week_cats.get(cat, 0)
            if lw > 0:
                change_pct = ((tw - lw) / lw) * 100
            elif tw > 0:
                change_pct = 100.0  # New activity
            else:
                change_pct = 0

            if abs(change_pct) >= 5:  # Only show meaningful changes
                results["trends"][cat] = {
                    "this_week": tw,
                    "last_week": lw,
                    "change_pct": change_pct,
                    "direction": "up" if change_pct > 0 else "down"
                }

        # ===== STREAK TRACKING =====
        results["streak_days"] = self._update_streak(results["is_healthy"])

        # Sort categories by count descending
        sorted_cats = {k: v for k, v in sorted(results["categories"].items(),
                       key=lambda item: item[1]["count"], reverse=True)}
        results["categories"] = sorted_cats

        return results

    def _compute_wellness_score(self, results, total):
        """Compute a 1-100 wellness score based on browsing patterns."""
        if total == 0:
            return 100  # No data = clean

        score = 70.0  # Base score

        # Positive contribution from productive/career/news categories
        for cat_name, data in self.categories.items():
            weight = data.get("weight", 0)
            count = results["categories"][cat_name]["count"]
            percentage = (count / total) * 100 if total > 0 else 0

            if weight >= 0.8:
                score += percentage * 0.2  # Boost for productive content
            elif weight <= 0:
                score -= percentage * 0.3  # Penalty for negative content

        # Critical trigger penalties
        for trigger_type in results["triggered_types"]:
            penalty = self.critical_triggers.get(trigger_type, {}).get("score_penalty", -10)
            score += penalty  # penalty is negative

        # Late-night harmful browsing extra penalty
        if results.get("late_night_harmful_count", 0) > 0:
            score -= results["late_night_harmful_count"] * 5

        # Clamp to 1-100
        return max(1, min(100, int(round(score))))

    def _parse_time(self, time_str):
        """Parse a time string into a datetime object. Returns None on failure."""
        if not time_str or time_str in ("Unknown", "N/A"):
            return None
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None

    def _load_streak(self):
        """Load the wellness streak from persistent storage."""
        try:
            if os.path.exists(STREAK_DATA_PATH):
                with open(STREAK_DATA_PATH, "r") as f:
                    data = json.load(f)
                    return data.get("streak_days", 0)
        except Exception:
            pass
        return 0

    def _update_streak(self, is_healthy_today):
        """Update and persist the wellness streak counter."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        streak_data = {"streak_days": 0, "last_date": "", "last_healthy": True}

        try:
            os.makedirs(os.path.dirname(STREAK_DATA_PATH), exist_ok=True)
            if os.path.exists(STREAK_DATA_PATH):
                with open(STREAK_DATA_PATH, "r") as f:
                    streak_data = json.load(f)
        except Exception:
            pass

        last_date = streak_data.get("last_date", "")
        current_streak = streak_data.get("streak_days", 0)

        if last_date == today_str:
            # Already checked today — update health status but don't double-count
            if not is_healthy_today:
                streak_data["streak_days"] = 0
                streak_data["last_healthy"] = False
        else:
            # New day
            if is_healthy_today:
                # Check if it's consecutive
                try:
                    last_dt = datetime.strptime(last_date, "%Y-%m-%d") if last_date else None
                    today_dt = datetime.strptime(today_str, "%Y-%m-%d")
                    if last_dt and (today_dt - last_dt).days == 1 and streak_data.get("last_healthy", True):
                        streak_data["streak_days"] = current_streak + 1
                    elif last_dt and (today_dt - last_dt).days == 0:
                        pass  # Same day
                    else:
                        streak_data["streak_days"] = 1  # Reset or start new streak
                except Exception:
                    streak_data["streak_days"] = 1
                streak_data["last_healthy"] = True
            else:
                streak_data["streak_days"] = 0
                streak_data["last_healthy"] = False

        streak_data["last_date"] = today_str

        try:
            with open(STREAK_DATA_PATH, "w") as f:
                json.dump(streak_data, f)
        except Exception:
            pass

        return streak_data["streak_days"]
