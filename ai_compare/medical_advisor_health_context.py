"""
Medical Advisor Health Context System
Stores and retrieves ongoing health information for personalized medical guidance.
Each user has a persistent health profile that accumulates over conversations.
"""
import json
from decimal import Decimal
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


HEALTH_DATA_DIR = Path(__file__).parent.parent / "health_profiles"


def _ollama_health_chat(messages, max_tokens=2000, temperature=0.1):
    """Call a local Ollama server for health-profile analysis."""
    import urllib.request

    host = os.getenv('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')
    models_env = os.getenv('OLLAMA_MODEL', 'deepseek-r1,qwen2.5,llama3.2')
    models = [m.strip() for m in models_env.split(',') if m.strip()]
    timeout = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    last_err = None

    for model in models:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                host + '/api/chat',
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode('utf-8'))
            text = (body.get('message', {}) or {}).get('content', '') or ''
            if text:
                return text
        except Exception as e:
            last_err = e
            print(f"[OLLAMA] {model} failed: {e}")
            continue

    raise last_err if last_err else Exception("All Ollama models failed")


def _health_ai_chat(messages, max_tokens=2000, temperature=0.1, model=None):
    """
    Generate a response for health-profile analysis.
    Prefers Ollama when AI_PREFER_FREE is set or OPENAI_API_KEY is missing,
    otherwise uses the configured OpenAI-compatible endpoint.
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = os.getenv('OPENAI_API_KEY')
    api_key = api_key if api_key and api_key.strip() else None
    prefer_free = os.getenv('AI_PREFER_FREE', '').lower() in ('1', 'true', 'yes')

    if not api_key or prefer_free:
        try:
            return _ollama_health_chat(messages, max_tokens, temperature)
        except Exception:
            if not api_key:
                raise RuntimeError("No OpenAI API key configured and Ollama is not reachable")

    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        timeout=60.0,
        max_retries=3
    )
    response = client.chat.completions.create(
        model=model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


class HealthProfile:
    """Persistent health profile for a user"""

    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        self.file_path = HEALTH_DATA_DIR / f"{self.user_id}.json"
        self.data = self._load()
        changed = self._normalize_test_results()
        changed += self._deduplicate_test_results()
        if changed:
            self.save()

    def _load(self) -> Dict:
        """Load profile from disk or create default"""
        HEALTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_profile()

    def _default_profile(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "personal": {
                "age": None,
                "gender": None,
                "location": "",
                "blood_type": ""
            },
            "conditions": [],
            "symptoms": [],
            "medications": [],
            "supplements": [],
            "diet": {
                "preferences": [],
                "restrictions": [],
                "daily_foods": [],
                "cooking_methods": [],
                "notes": []
            },
            "test_results": [],
            "action_plans": [],
            "follow_ups": [],
            "questions_for_doctor": [],
            "lifestyle": {
                "exercise": [],
                "sleep": {},
                "stress_factors": [],
                "habits": []
            },
            "provider_notes": [],
            "conversation_insights": [],
            "upload_settings": {
                "retention_days": 365
            },
            "uploaded_documents": []
        }

    def save(self):
        """Persist to disk"""
        self.data["updated_at"] = datetime.now().isoformat()
        HEALTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _normalize_test_results(self) -> int:
        """Expand legacy test results whose value is a dict into one row per sub-test.
        Also flattens any dict reference_range to a readable string."""
        results = self.data.get("test_results", [])
        changed = 0
        new_results = []
        for t in results:
            value = t.get("value")
            ref = t.get("reference_range")
            if isinstance(value, dict):
                for sub_name, sub_value in value.items():
                    if not sub_name or not isinstance(sub_name, str):
                        continue
                    sub_ref = ref.get(sub_name, "") if isinstance(ref, dict) else str(ref)
                    new_results.append({
                        "test_name": sub_name,
                        "value": self._stringify_test_result_value(sub_value),
                        "reference_range": self._stringify_test_result_value(sub_ref),
                        "date": t.get("date", ""),
                        "notes": t.get("notes", ""),
                        "added_at": t.get("added_at", "")
                    })
                changed += 1
                continue
            if isinstance(ref, dict):
                t["reference_range"] = '; '.join(f"{k}: {v}" for k, v in ref.items())
                changed += 1
            new_results.append(t)
        if new_results:
            self.data["test_results"] = new_results

        # Re-clean all stored values so existing H/L flag mistakes get fixed on load
        for t in self.data.get("test_results", []):
            ref = t.get("reference_range", "")
            if not isinstance(ref, str):
                ref = str(ref) if ref is not None else ""
            cleaned = self._clean_test_value(str(t.get("value", "")), ref)
            cleaned = self._reorder_test_value(cleaned)
            if str(t.get("value", "")) != cleaned:
                t["value"] = cleaned
                changed += 1

        return changed

    @staticmethod
    def _stringify_test_result_value(v) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return '; '.join(f"{k}: {val}" for k, val in v.items())
        if v is None:
            return ''
        return str(v)

    # --- Accessors ---

    @property
    def name(self) -> str:
        return self.data.get("name", "")

    @name.setter
    def name(self, value: str):
        self.data["name"] = value

    def set_personal(self, **kwargs):
        """Update personal info (age, gender, location, blood_type)"""
        for k, v in kwargs.items():
            if k in self.data["personal"]:
                self.data["personal"][k] = v
        self.save()

    def add_medication(self, name: str, dose: str = "", purpose: str = "", frequency: str = "", prescribed_date: str = "") -> bool:
        """Add a prescribed medication. Returns True if actually added/updated."""
        self.data.setdefault("medications", [])
        existing = self.data["medications"]
        name_lower = name.lower().strip()
        for m in existing:
            if m.get("name", "").lower().strip() == name_lower:
                updated = False
                if dose and not m.get("dose"):
                    m["dose"] = dose
                    updated = True
                if purpose and not m.get("purpose"):
                    m["purpose"] = purpose
                    updated = True
                if frequency and not m.get("frequency"):
                    m["frequency"] = frequency
                    updated = True
                if prescribed_date and not m.get("prescribed_date"):
                    m["prescribed_date"] = prescribed_date
                    updated = True
                return updated  # Duplicate — skip (may have updated fields)
        entry = {
            "name": name,
            "dose": dose,
            "purpose": purpose,
            "frequency": frequency,
            "prescribed_date": prescribed_date,
            "added_at": datetime.now().isoformat()
        }
        self.data["medications"].append(entry)
        return True

    def add_condition(self, name: str, details: str = "", status: str = "active",
                     diagnosed_date: str = "") -> bool:
        """Add a health condition. Returns True if actually added/updated."""
        existing = self.data.get("conditions", [])
        for c in existing:
            if c.get("name", "").lower().strip() == name.lower().strip():
                updated = False
                if details and not c.get("details"):
                    c["details"] = details
                    updated = True
                if diagnosed_date and not c.get("diagnosed_date"):
                    c["diagnosed_date"] = diagnosed_date
                    updated = True
                if status and status != "active" and c.get("status") != status:
                    c["status"] = status
                    updated = True
                return updated  # Duplicate — skip (may have updated fields)
        entry = {
            "name": name,
            "details": details,
            "status": status,
            "diagnosed_date": diagnosed_date,
            "added_at": datetime.now().isoformat()
        }
        self.data["conditions"].append(entry)
        return True

    def add_symptom(self, description: str, triggers: List[str] = None,
                    severity: str = "moderate", onset: str = "", frequency: str = "") -> bool:
        """Add a symptom. Returns True if actually added."""
        existing = self.data.get("symptoms", [])
        desc_lower = description.lower().strip()
        for s in existing:
            if s.get("description", "").lower().strip() == desc_lower:
                return False  # Duplicate — skip
        entry = {
            "description": description,
            "triggers": triggers or [],
            "severity": severity,
            "onset": onset,
            "frequency": frequency,
            "added_at": datetime.now().isoformat()
        }
        self.data["symptoms"].append(entry)
        return True

    def add_test_result(self, test_name: str, value: str, reference_range: str = "",
                       date: str = "", notes: str = "") -> bool:
        """Add a lab/test result. Returns True if actually added."""
        # Normalize non-string values (e.g., AI may return dict with value/unit/flag)
        if not isinstance(value, str):
            if isinstance(value, dict):
                v = value.get('value')
                if v is None:
                    v = value.get('result', '')
                v = str(v)
                u = str(value.get('unit') or value.get('units') or '').strip()
                f = str(value.get('flag') or value.get('status') or '').strip()
                parts = [p for p in [v, f, u] if p]
                value = ' '.join(parts) if parts else str(value)
            else:
                value = str(value)
        if not isinstance(reference_range, str):
            if isinstance(reference_range, dict):
                reference_range = '; '.join(f"{k}: {v}" for k, v in reference_range.items())
            else:
                reference_range = str(reference_range)
        value = self._clean_test_value(value, reference_range)
        value = self._reorder_test_value(value)
        existing = self.data.get("test_results", [])
        date_val = self._normalize_test_date(date or datetime.now().strftime("%Y-%m-%d"))
        for t in existing:
            if self._is_duplicate_test_result(t, test_name, value, date_val):
                # Same mineral on the same date: overwrite with the latest value
                t["value"] = value
                t["test_name"] = test_name
                if date_val:
                    t["date"] = date_val
                if reference_range:
                    t["reference_range"] = reference_range
                if notes:
                    t["notes"] = notes
                t["added_at"] = datetime.now().isoformat()
                return True  # Updated existing entry
        entry = {
            "test_name": test_name,
            "value": value,
            "reference_range": reference_range,
            "date": date_val,
            "notes": notes,
            "added_at": datetime.now().isoformat()
        }
        self.data["test_results"].append(entry)

        # Auto-refresh critical test interpretation so latest values supersede older analysis.
        self._refresh_auto_test_analysis(test_name)
        return True

    def _normalize_test_date(self, date_text: str, added_at: str = "") -> str:
        """Normalize medical dates to YYYY-MM-DD when parseable."""
        entry = {"date": date_text, "added_at": added_at}
        dt = self._parse_test_date_for_sort(entry)
        if dt == datetime.min:
            return (date_text or "").strip()
        return dt.strftime("%Y-%m-%d")

    def _normalize_value_for_compare(self, value: str) -> str:
        """Normalize value for duplicate checks, preferring numeric equivalence."""
        text = re.sub(r'\s+', ' ', str(value or '').lower()).strip()
        numeric = self._extract_numeric_value(text)
        if numeric is not None:
            return f"num:{numeric:.8f}"
        return f"txt:{text}"

    def _is_duplicate_test_result(self, existing_entry: Dict, test_name: str, value: str, date_text: str) -> bool:
        """Return True when the same test (mineral) was performed on the same date."""
        existing_key = self._normalize_test_key(existing_entry.get("test_name", ""))
        incoming_key = self._normalize_test_key(test_name)
        if existing_key != incoming_key:
            return False

        existing_date = self._normalize_test_date(existing_entry.get("date", ""), existing_entry.get("added_at", ""))
        incoming_date = self._normalize_test_date(date_text)
        if existing_date and incoming_date and existing_date != incoming_date:
            return False
        if not existing_date and not incoming_date:
            # Same test with no date on either side counts as a duplicate
            return True
        if not existing_date or not incoming_date:
            # One has a date and the other does not: treat as distinct
            return False
        return True

    def _deduplicate_test_results(self) -> int:
        """Collapse duplicate test rows in-place and return number removed."""
        results = self.data.get("test_results", [])
        deduped = []
        removed = 0

        for row in results:
            duplicate = None
            normalized_date = self._normalize_test_date(row.get("date", ""), row.get("added_at", ""))
            row_value = row.get("value", "")
            row_name = row.get("test_name", "")

            for kept in deduped:
                if self._is_duplicate_test_result(kept, row_name, row_value, normalized_date):
                    duplicate = kept
                    break

            if duplicate is None:
                if normalized_date:
                    row["date"] = normalized_date
                deduped.append(row)
                continue

            removed += 1
            # Keep the first/earlier row's value; backfill missing metadata from the later row
            if not duplicate.get("reference_range") and row.get("reference_range"):
                duplicate["reference_range"] = row["reference_range"]
            if not duplicate.get("notes") and row.get("notes"):
                duplicate["notes"] = row["notes"]

        if removed:
            self.data["test_results"] = deduped

        return removed

    def add_action_plan(self, title: str, steps: List[str], status: str = "active",
                       priority: str = "medium") -> bool:
        """Add an action plan item. Returns True if actually added."""
        existing = self.data.get("action_plans", [])
        title_lower = title.lower().strip()
        for p in existing:
            if p.get("title", "").lower().strip() == title_lower:
                return False  # Duplicate — skip
        entry = {
            "title": title,
            "steps": steps,
            "status": status,
            "priority": priority,
            "added_at": datetime.now().isoformat()
        }
        self.data["action_plans"].append(entry)
        return True

    def add_follow_up(self, title: str, steps: List[str], due_date: str = "",
                      priority: str = "medium", source: str = "ai") -> bool:
        """Add a follow-up action. Returns True if actually added."""
        existing = self.data.get("follow_ups", [])
        title_lower = title.lower().strip()
        for f in existing:
            if f.get("title", "").lower().strip() == title_lower:
                return False
        entry = {
            "title": title,
            "steps": steps,
            "due_date": due_date,
            "priority": priority,
            "status": "active",
            "source": source,
            "added_at": datetime.now().isoformat()
        }
        self.data.setdefault("follow_ups", []).append(entry)
        return True

    def add_doctor_question(self, question: str, context: str = "",
                            priority: str = "medium", source: str = "ai") -> bool:
        """Add a question to ask the doctor. Returns True if actually added."""
        existing = self.data.get("questions_for_doctor", [])
        question_lower = question.lower().strip()
        for q in existing:
            if q.get("question", "").lower().strip() == question_lower:
                return False
        entry = {
            "question": question,
            "context": context,
            "priority": priority,
            "answered": False,
            "source": source,
            "added_at": datetime.now().isoformat()
        }
        self.data.setdefault("questions_for_doctor", []).append(entry)
        return True

    def update_diet(self, daily_foods: List[str] = None, preferences: List[str] = None,
                   restrictions: List[str] = None, cooking_methods: List[str] = None,
                   notes: List[str] = None):
        """Update diet information"""
        if daily_foods is not None:
            self.data["diet"]["daily_foods"] = daily_foods
        if preferences is not None:
            self.data["diet"]["preferences"] = preferences
        if restrictions is not None:
            self.data["diet"]["restrictions"] = restrictions
        if cooking_methods is not None:
            self.data["diet"]["cooking_methods"] = cooking_methods
        if notes is not None:
            self.data["diet"]["notes"] = notes
        self.save()

    def update_lifestyle(self, sleep: Dict = None, exercise: List[str] = None,
                        stress_factors: List[str] = None, habits: List[str] = None):
        """Update lifestyle information"""
        if sleep is not None:
            self.data["lifestyle"]["sleep"] = sleep
        if exercise is not None:
            self.data["lifestyle"]["exercise"] = exercise
        if stress_factors is not None:
            self.data["lifestyle"]["stress_factors"] = stress_factors
        if habits is not None:
            self.data["lifestyle"]["habits"] = habits
        self.save()

    def add_supplement(self, name: str, dose: str = "", purpose: str = "", frequency: str = "", prescribed_date: str = "") -> bool:
        """Add a supplement or herb. Returns True if actually added/updated."""
        existing = self.data.get("supplements", [])
        name_lower = name.lower().strip()
        for s in existing:
            if s.get("name", "").lower().strip() == name_lower:
                updated = False
                if dose and not s.get("dose"):
                    s["dose"] = dose
                    updated = True
                if purpose and not s.get("purpose"):
                    s["purpose"] = purpose
                    updated = True
                if frequency and not s.get("frequency"):
                    s["frequency"] = frequency
                    updated = True
                if prescribed_date and not s.get("prescribed_date"):
                    s["prescribed_date"] = prescribed_date
                    updated = True
                return updated  # Duplicate — skip (may have updated fields)
        entry = {
            "name": name,
            "dose": dose,
            "purpose": purpose,
            "frequency": frequency,
            "prescribed_date": prescribed_date,
            "added_at": datetime.now().isoformat()
        }
        self.data["supplements"].append(entry)
        return True

    def apply_extracted_data(self, extracted: dict) -> list:
        """
        Shared method: apply extracted health data to this profile.
        Used by BOTH conversation profile updates and paste/upload analysis.
        Returns list of action descriptions for what was stored.
        """
        actions = []

        removed_duplicates = self._deduplicate_test_results()
        if removed_duplicates:
            actions.append(f"Removed {removed_duplicates} duplicate test result(s)")

        # Foods
        new_foods = extracted.get("foods", []) + extracted.get("new_foods", [])
        if new_foods:
            current_foods = self.data.get("diet", {}).get("daily_foods", [])
            current_lower = [f.lower() for f in current_foods]
            added = []
            for food in new_foods:
                if food and food.lower() not in current_lower:
                    current_foods.append(food)
                    added.append(food)
                    current_lower.append(food.lower())
            if added:
                self.data.setdefault("diet", {})["daily_foods"] = current_foods
                actions.append(f"Added {len(added)} foods: {', '.join(added)}")

        # Food notes
        food_notes = extracted.get("food_notes", [])
        if food_notes:
            existing_notes = self.data.get("diet", {}).get("notes", [])
            for note in food_notes:
                if note and note not in existing_notes:
                    existing_notes.append(note)
            self.data.setdefault("diet", {})["notes"] = existing_notes
            actions.append(f"Added {len(food_notes)} diet note(s)")

        # Restrictions
        restrictions = extracted.get("restrictions", []) + extracted.get("new_restrictions", [])
        if restrictions:
            existing_r = self.data.get("diet", {}).get("restrictions", [])
            for r in restrictions:
                if r and r not in existing_r:
                    existing_r.append(r)
            self.data.setdefault("diet", {})["restrictions"] = existing_r
            actions.append(f"Added {len(restrictions)} restriction(s)")

        # Medications (prescribed drugs) — stored in medications[], NOT supplements[]
        for med in extracted.get("medications", []) + extracted.get("new_medications", []):
            if med.get("name"):
                if self.add_medication(med["name"], med.get("dose", ""), med.get("purpose", "")):
                    actions.append(f"Added medication: {med['name']}")

        # Supplements (vitamins, herbs, minerals)
        for sup in extracted.get("supplements", []) + extracted.get("new_supplements", []):
            if sup.get("name"):
                if self.add_supplement(sup["name"], sup.get("dose", ""), sup.get("purpose", "")):
                    actions.append(f"Added supplement: {sup['name']}")

        # Symptoms
        for sym in extracted.get("symptoms", []) + extracted.get("new_symptoms", []):
            if sym.get("description"):
                if self.add_symptom(sym["description"], sym.get("triggers", []), sym.get("severity", "moderate")):
                    actions.append(f"Added symptom: {sym['description']}")

        # Conditions
        for cond in extracted.get("conditions", []) + extracted.get("new_conditions", []):
            if cond.get("name"):
                if self.add_condition(
                    cond["name"], cond.get("details", ""),
                    cond.get("status", "active"), cond.get("diagnosed_date", "")
                ):
                    actions.append(f"Added condition: {cond['name']}" + (f" ({cond['diagnosed_date']})" if cond.get('diagnosed_date') else ""))

        # Test results
        for test in extracted.get("test_results", []) + extracted.get("new_test_results", []):
            if not test.get("test_name"):
                continue
            value = test.get("value", "")
            if isinstance(value, dict):
                ref_map = test.get("reference_range", {}) if isinstance(test.get("reference_range"), dict) else {}
                for sub_name, sub_value in value.items():
                    if not sub_name or not isinstance(sub_name, str):
                        continue
                    sub_ref = ref_map.get(sub_name, "") if ref_map else str(test.get("reference_range", ""))
                    if self.add_test_result(sub_name, sub_value, sub_ref, test.get("date", ""), test.get("notes", "")):
                        actions.append(f"Added test: {sub_name}")
            else:
                if self.add_test_result(
                    test["test_name"], value,
                    test.get("reference_range", ""), test.get("date", ""), test.get("notes", "")
                ):
                    actions.append(f"Added test: {test['test_name']}")

        # Collapse duplicate test rows after applying extracted results
        self._deduplicate_test_results()

        # Action plans
        for plan in extracted.get("action_plans", []):
            if plan.get("title"):
                if self.add_action_plan(plan["title"], plan.get("steps", []), plan.get("priority", "medium")):
                    actions.append(f"Added plan: {plan['title']}")

        # Next steps / follow-ups
        for step in extracted.get("next_steps", []):
            if step.get("title"):
                if self.add_follow_up(step["title"], step.get("steps", []), step.get("due_date", ""), step.get("priority", "medium")):
                    actions.append(f"Added follow-up: {step['title']}")

        # Questions for the doctor
        for q in extracted.get("questions_for_doctor", []):
            if q.get("question"):
                if self.add_doctor_question(q["question"], q.get("context", ""), q.get("priority", "medium")):
                    actions.append(f"Added question for doctor: {q['question'][:60]}...")

        # Lifestyle notes
        for note in extracted.get("lifestyle_notes", []) + extracted.get("lifestyle_updates", []):
            if note:
                if self.add_conversation_insight(note, category="lifestyle"):
                    actions.append(f"Added lifestyle note")

        # Clinical notes
        for note in extracted.get("clinical_notes", []):
            if note:
                text = note
                if isinstance(note, dict):
                    date = note.get("date", "")
                    value = note.get("note", "")
                    if date and value:
                        text = f"{date}: {value}"
                    else:
                        text = value or date
                if text:
                    existing = self.data.setdefault("provider_notes", [])
                    if text not in existing:
                        existing.append(text)
                        actions.append(f"Added clinical note: {text[:60]}")

        # Warnings
        for w in extracted.get("warnings", []):
            if w:
                if self.add_conversation_insight(f"⚠️ WARNING: {w}", category="warning"):
                    actions.append(f"Added warning")

        # Insights
        for ins in extracted.get("insights", []):
            if isinstance(ins, dict) and ins.get("insight"):
                if self.add_conversation_insight(ins["insight"], ins.get("category", "general")):
                    actions.append(f"Added insight: {ins['insight'][:60]}...")
            elif isinstance(ins, str) and ins:
                if self.add_conversation_insight(ins, category="general"):
                    actions.append(f"Added insight")

        # Advice (from conversation)
        for adv in extracted.get("advice", []):
            if adv and len(adv) > 10:
                if self.add_conversation_insight(adv, category="advice_from_conversation"):
                    actions.append(f"Added advice")

        # Allergies
        for allergy in extracted.get("allergies", []) + extracted.get("new_allergies", []):
            if allergy:
                existing_r = self.data.get("diet", {}).get("restrictions", [])
                allergy_entry = f"ALLERGY: {allergy}"
                if allergy_entry not in existing_r and allergy not in existing_r:
                    self.data.setdefault("diet", {}).setdefault("restrictions", []).append(allergy_entry)
                    actions.append(f"Added allergy: {allergy}")

        # Personal info (age, weight, height, blood_type)
        personal_data = extracted.get("personal", extracted.get("personal_updates", {}))
        if personal_data and isinstance(personal_data, dict):
            for key in ['age', 'weight', 'height', 'blood_type']:
                val = personal_data.get(key)
                if val:
                    self.data.setdefault("personal", {})[key] = val
                    actions.append(f"Updated personal: {key} = {val}")

        # Procedures / surgeries
        for proc in extracted.get("procedures", []):
            if proc.get("name"):
                detail = proc.get("notes", "")
                date = proc.get("date", "")
                if self.add_condition(f"[Procedure] {proc['name']}", detail, "resolved", date):
                    actions.append(f"Added procedure: {proc['name']}")

        # Family history
        for fh in extracted.get("family_history", []):
            if fh:
                if self.add_conversation_insight(f"Family history: {fh}", category="family_history"):
                    actions.append(f"Added family history: {fh}")

        if actions:
            self.save()

        return actions

    MAX_INSIGHTS = 200  # Cap to prevent unbounded growth

    def add_conversation_insight(self, insight: str, category: str = "general") -> bool:
        """Store an insight. Returns True if actually added. Caps at MAX_INSIGHTS (oldest non-warning removed)."""
        existing = self.data.get("conversation_insights", [])
        # Check for near-duplicate: same first 60 chars (normalized) = duplicate
        insight_key = insight.lower().strip()[:60]
        for e in existing:
            existing_key = e.get("insight", "").lower().strip()[:60]
            if existing_key == insight_key:
                return False  # Duplicate — skip

        # Cap: remove oldest non-critical entries if at limit
        if len(existing) >= self.MAX_INSIGHTS:
            # Keep warnings/interactions/family_history, prune oldest general/lifestyle/advice
            removable = ['general', 'lifestyle', 'advice_from_conversation', 'symptom']
            for i, e in enumerate(existing):
                if e.get("category") in removable:
                    existing.pop(i)
                    break
            else:
                # All are critical — remove the very oldest
                existing.pop(0)

        entry = {
            "insight": insight,
            "category": category,
            "date": datetime.now().isoformat()
        }
        self.data["conversation_insights"].append(entry)
        return True

    def _normalize_test_key(self, test_name: str) -> str:
        """Normalize test name for grouping trend updates (e.g., 'TSH (Roche)' -> 'tsh')."""
        if not test_name:
            return ""
        key = test_name.lower().strip()
        key = re.sub(r'\(.*?\)', '', key).strip()
        key = key.replace("historical", "").strip()
        key = re.sub(r'\s+', ' ', key)
        return key

    def _clean_test_value(self, value: str, reference_range: str) -> str:
        """Strip H/L/High/Low markers from a value when the numeric value is within the reference range.
        This fixes AI/OCR cases where a flag is incorrectly attached to a normal value."""
        if not value or not reference_range:
            return value
        numeric = self._extract_numeric_value(value)
        if numeric is None:
            return value
        ref = str(reference_range).strip().strip('()')
        nums = re.findall(r'\d+(?:\.\d+)?', ref)
        if len(nums) < 2:
            return value
        try:
            lower = min(float(nums[0]), float(nums[1]))
            upper = max(float(nums[0]), float(nums[1]))
        except ValueError:
            return value
        if lower <= numeric <= upper:
            cleaned = re.sub(r'\s+\b(H|L|High|Low)\b', '', str(value), flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'^(H|L|High|Low)\s+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+(H|L|High|Low)$', '', cleaned, flags=re.IGNORECASE)
            return re.sub(r'\s+', ' ', cleaned).strip()
        return value

    def _reorder_test_value(self, value: str) -> str:
        """Normalize a test result string so H/L flags sit right after the numeric value and before any unit."""
        if not value:
            return value
        text = re.sub(r'\s+', ' ', str(value).strip())
        match = re.search(r'-?\d+(?:\.\d+)?', text)
        if not match:
            return value
        num = match.group(0)
        rest = text[match.end():].strip()
        flag = ''
        if re.search(r'(?<!\S)(H|High)(?!\S)', rest, re.IGNORECASE):
            flag = 'H'
        elif re.search(r'(?<!\S)(L|Low)(?!\S)', rest, re.IGNORECASE):
            flag = 'L'
        rest = re.sub(r'(?<!\S)(H|L|High|Low)(?!\S)\s*', '', rest, flags=re.IGNORECASE).strip()
        parts = [num]
        if flag:
            parts.append(flag)
        if rest:
            parts.append(rest)
        return ' '.join(parts)

    def _extract_numeric_value(self, value: str) -> Optional[float]:
        """Extract first numeric value from a test result string."""
        if not value:
            return None
        match = re.search(r'-?\d+(?:\.\d+)?', str(value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _parse_test_date_for_sort(self, test_entry: Dict) -> datetime:
        """Best-effort parse of medical test date for chronological sorting."""
        date_text = (test_entry.get("date") or "").strip()
        fmts = [
            "%Y-%m-%d", "%Y-%m", "%Y", "%d/%m/%Y", "%d-%b-%y", "%d-%b-%Y", "%d %b %Y"
        ]
        for fmt in fmts:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        added_at = (test_entry.get("added_at") or "").strip()
        if added_at:
            try:
                return datetime.fromisoformat(added_at)
            except ValueError:
                pass

        return datetime.min

    def _upsert_auto_test_insight(self, test_key: str, insight: str, category: str = "test_results") -> None:
        """Replace prior auto insight for a test family and append updated interpretation."""
        insights = self.data.setdefault("conversation_insights", [])
        filtered = []
        for item in insights:
            if item.get("source") == "auto_test_analysis" and item.get("test_key") == test_key:
                continue
            filtered.append(item)
        self.data["conversation_insights"] = filtered

        self.data["conversation_insights"].append({
            "insight": insight,
            "category": category,
            "date": datetime.now().isoformat(),
            "source": "auto_test_analysis",
            "test_key": test_key
        })

    def _build_tsh_auto_insight(self) -> Optional[str]:
        """Create a superseding TSH interpretation from latest available TSH results."""
        tsh_entries = [
            t for t in self.data.get("test_results", [])
            if "tsh" in self._normalize_test_key(t.get("test_name", ""))
            and "historical" not in (t.get("test_name", "").lower())
        ]
        if not tsh_entries:
            return None

        sorted_entries = sorted(tsh_entries, key=self._parse_test_date_for_sort)
        latest = sorted_entries[-1]
        previous = sorted_entries[-2] if len(sorted_entries) > 1 else None

        latest_value_text = latest.get("value", "")
        latest_numeric = self._extract_numeric_value(latest_value_text)
        latest_date = latest.get("date", "unknown date")
        latest_ref = latest.get("reference_range", "")

        if latest_numeric is None:
            return (
                f"Latest TSH update ({latest_date}): {latest_value_text}. "
                "Use this latest TSH result for current thyroid interpretation; older TSH interpretations are historical."
            )

        if latest_numeric > 5.5:
            thyroid_state = "above the stated reference range"
        elif latest_numeric < 0.4:
            thyroid_state = "below the stated reference range"
        else:
            thyroid_state = "within the stated reference range"

        trend_text = ""
        if previous:
            prev_numeric = self._extract_numeric_value(previous.get("value", ""))
            prev_text = previous.get("value", "")
            prev_date = previous.get("date", "previous")
            if prev_numeric is not None:
                delta = latest_numeric - prev_numeric
                if delta < 0:
                    trend_text = f" It improved from {prev_text} ({prev_date}) to {latest_value_text}."
                elif delta > 0:
                    trend_text = f" It increased from {prev_text} ({prev_date}) to {latest_value_text}."
                else:
                    trend_text = f" It is unchanged from {prev_text} ({prev_date})."

        ref_text = f" (ref: {latest_ref})" if latest_ref else ""
        return (
            f"Latest TSH update ({latest_date}): {latest_value_text}{ref_text}, {thyroid_state}.{trend_text} "
            "This latest TSH result supersedes older TSH interpretations, which should be treated as historical trend context."
        )

    def _refresh_auto_test_analysis(self, changed_test_name: str) -> None:
        """Refresh deterministic auto-analysis when critical tests are updated."""
        key = self._normalize_test_key(changed_test_name)
        if "tsh" in key:
            insight = self._build_tsh_auto_insight()
            if insight:
                self._upsert_auto_test_insight("tsh", insight, category="test_results")

    def _display_test_name(self, test_name: str) -> str:
        """Human-readable test label without parenthetical noise."""
        if not test_name:
            return "Unknown Test"
        cleaned = re.sub(r'\(.*?\)', '', test_name)
        cleaned = re.sub(r'historical', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned or test_name.strip()

    def _format_for_display(self, value, max_len: int = 80) -> str:
        """Convert a test value or reference to a short human-readable string."""
        if not value:
            return ""
        if isinstance(value, dict):
            items = [f"{k}: {v}" for k, v in value.items() if v is not None]
            text = ", ".join(items)
        else:
            text = str(value)
        text = text.replace('\n', ' ').replace('\r', '')
        if len(text) > max_len:
            text = text[:max_len - 3] + "..."
        return text

    def _assess_against_reference(self, value: str, reference_range: str) -> str:
        """Return high, low, normal, or unknown based on reference range text."""
        numeric = self._extract_numeric_value(value)
        if numeric is None or not reference_range:
            return "unknown"

        ref = str(reference_range).strip()

        range_match = re.search(
            r'(-?\d+(?:\.\d+)?)\s*(?:[-–—]|to)\s*(-?\d+(?:\.\d+)?)',
            ref,
            re.IGNORECASE,
        )
        if range_match:
            low, high = float(range_match.group(1)), float(range_match.group(2))
            if numeric < low:
                return "low"
            if numeric > high:
                return "high"
            return "normal"

        lt_match = re.search(r'[<≤]\s*(-?\d+(?:\.\d+)?)', ref)
        if lt_match:
            return "high" if numeric > float(lt_match.group(1)) else "normal"

        gt_match = re.search(r'[>≥]\s*(-?\d+(?:\.\d+)?)', ref)
        if gt_match:
            return "low" if numeric < float(gt_match.group(1)) else "normal"

        return "unknown"

    def _compute_test_trend(self, entries: List[Dict]) -> str:
        """Compare latest vs previous numeric reading."""
        if len(entries) < 2:
            return "single"

        sorted_entries = sorted(entries, key=self._parse_test_date_for_sort)
        latest = self._extract_numeric_value(sorted_entries[-1].get("value", ""))
        previous = self._extract_numeric_value(sorted_entries[-2].get("value", ""))
        if latest is None or previous is None:
            return "unknown"

        delta = latest - previous
        if abs(delta) < 1e-9:
            return "stable"
        return "up" if delta > 0 else "down"

    def _format_summary_date(self, dt: datetime) -> str:
        if dt == datetime.min:
            return "Unknown"
        return dt.strftime("%d %b %Y")

    def _build_test_results_text_report(self, overview: Dict, groups: List[Dict],
                                        flagged: List[Dict], insights: List[str],
                                        concise: bool = False) -> str:
        """Render a plain-text summary report; concise mode fits one page."""
        patient = self.data.get("name") or "Patient"
        date_range = overview.get("date_range") or {}

        if concise:
            lines = ["CONCISE LAB TEST RESULTS HISTORY", ""]
            lines.append(f"Patient: {patient}")
            lines.append(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}")
            if date_range.get("from") or date_range.get("to"):
                lines.append(f"Date range: {date_range.get('from', 'Unknown')} to {date_range.get('to', 'Unknown')}")
            lines.append("")

            lines.append("OVERVIEW")
            lines.append(f"- {overview.get('total_results', 0)} result(s) across {overview.get('unique_tests', 0)} test type(s)")
            flagged_count = overview.get("flagged_count", 0)
            lines.append(f"- {flagged_count} result(s) outside reference range")
            lines.append("")

            if flagged:
                lines.append(f"- {len(flagged)} result(s) flagged outside reference range (see details in full report).")
                lines.append("")

            if groups:

                def _short(s, n=75):
                    s = str(s).replace('\n', ' ').replace('\r', '')
                    return s if len(s) <= n else s[:n - 3] + '...'

                def _short_value(v, n=75):
                    if not v:
                        return '—'
                    if isinstance(v, dict):
                        v = ', '.join(f"{k}: {val}" for k, val in v.items() if val is not None)
                    return _short(v, n)

                lines.append("LATEST VALUES")
                for group in groups:
                    latest = group.get("latest") or {}
                    trend = group.get("trend", "unknown")
                    trend_label = {
                        "up": "rising",
                        "down": "falling",
                        "stable": "stable",
                        "single": "single reading",
                        "unknown": "trend n/a",
                    }.get(trend, trend)
                    status = (group.get("status") or "unknown").upper()
                    ref = latest.get("reference_range") or ""
                    if isinstance(ref, dict):
                        ref_text = "(multiple refs)"
                    else:
                        ref_text = _short_value(ref, 40) if ref else "n/a"
                    date = latest.get("date") or "no date"
                    latest_text = _short_value(latest.get("value"), 80)
                    lines.append(
                        f"- {group.get('display_name')}: {latest_text} "
                        f"(ref: {ref_text}) — {status} — {date} — {trend_label}"
                    )
                lines.append("")

            lines.append("— End of concise report —")
            return "\n".join(lines)

        lines = ["LAB TEST RESULTS SUMMARY", ""]
        lines.append(f"Patient: {patient}")
        lines.append(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}")
        lines.append("")

        lines.append("OVERVIEW")
        lines.append(f"- {overview.get('total_results', 0)} result(s) across {overview.get('unique_tests', 0)} test type(s)")
        if date_range.get("from") or date_range.get("to"):
            lines.append(f"- Date range: {date_range.get('from', 'Unknown')} to {date_range.get('to', 'Unknown')}")
        flagged_count = overview.get("flagged_count", 0)
        if flagged_count:
            lines.append(f"- {flagged_count} result(s) outside reference range")
        else:
            lines.append("- No results flagged outside reference range")
        lines.append("")

        if flagged:
            lines.append("FLAGGED RESULTS")
            for item in flagged:
                status = item.get("status", "unknown").upper()
                lines.append(
                    f"- {item.get('test_name')}: {item.get('value')} "
                    f"(ref: {item.get('reference_range') or 'n/a'}) — {status} — {item.get('date') or 'no date'}"
                )
            lines.append("")

        if groups:
            lines.append("LATEST VALUES")
            for group in groups:
                latest = group.get("latest") or {}
                trend = group.get("trend", "unknown")
                trend_label = {
                    "up": "rising",
                    "down": "falling",
                    "stable": "stable",
                    "single": "single reading",
                    "unknown": "trend n/a",
                }.get(trend, trend)
                status = (group.get("status") or "unknown").upper()
                ref = latest.get("reference_range") or "n/a"
                date = latest.get("date") or "no date"
                lines.append(
                    f"- {group.get('display_name')}: {latest.get('value')} "
                    f"(ref: {ref}) — {status} — {date} — {trend_label}"
                )
                history = group.get("history") or []
                if len(history) > 1:
                    lines.append(f"  History ({len(history)} readings):")
                    for entry in history[:5]:
                        lines.append(
                            f"    • {entry.get('date') or 'no date'}: {entry.get('value')}"
                            + (f" ({entry.get('status', 'unknown')})" if entry.get("status") != "unknown" else "")
                        )
            lines.append("")

        if insights:
            lines.append("KEY INSIGHTS")
            for insight in insights:
                lines.append(f"- {insight}")
            lines.append("")

        lines.append("— End of report —")
        return "\n".join(lines)

    def generate_test_results_summary(self, concise: bool = False) -> Dict:
        """Build a structured summary of stored lab/test results; concise mode fits one page."""
        tests = self.data.get("test_results", [])
        generated_at = datetime.now().isoformat()

        if not tests:
            return {
                "has_results": False,
                "generated_at": generated_at,
                "patient_name": self.data.get("name", ""),
                "overview": {
                    "total_results": 0,
                    "unique_tests": 0,
                    "date_range": {},
                    "flagged_count": 0,
                },
                "groups": [],
                "flagged": [],
                "insights": [],
                "text_report": "No test results on file.",
            }

        grouped: Dict[str, Dict] = {}
        all_dates: List[datetime] = []

        for test in tests:
            key = self._normalize_test_key(test.get("test_name", ""))
            if not key:
                key = (test.get("test_name") or "unknown").lower().strip()

            if key not in grouped:
                grouped[key] = {
                    "display_name": self._display_test_name(test.get("test_name", "")),
                    "entries": [],
                }
            grouped[key]["entries"].append(test)

            parsed_date = self._parse_test_date_for_sort(test)
            if parsed_date != datetime.min:
                all_dates.append(parsed_date)

        groups: List[Dict] = []
        flagged: List[Dict] = []

        for group in grouped.values():
            entries = sorted(group["entries"], key=self._parse_test_date_for_sort, reverse=True)
            latest = entries[0]
            status = self._assess_against_reference(latest.get("value", ""), latest.get("reference_range", ""))
            trend = self._compute_test_trend(group["entries"])

            history = []
            for entry in entries[: (2 if concise else 6)]:
                entry_status = self._assess_against_reference(
                    entry.get("value", ""), entry.get("reference_range", "")
                )
                history.append({
                    "test_name": entry.get("test_name", ""),
                    "value": self._format_for_display(entry.get("value", ""), 120),
                    "reference_range": self._format_for_display(entry.get("reference_range", ""), 80),
                    "date": entry.get("date", ""),
                    "status": entry_status,
                })

            if status in ("high", "low"):
                flagged.append({
                    "test_name": latest.get("test_name", group["display_name"]),
                    "value": self._format_for_display(latest.get("value", ""), 120),
                    "reference_range": self._format_for_display(latest.get("reference_range", ""), 80),
                    "date": latest.get("date", ""),
                    "status": status,
                })

            groups.append({
                "display_name": group["display_name"],
                "reading_count": len(entries),
                "latest": {
                    "test_name": latest.get("test_name", ""),
                    "value": self._format_for_display(latest.get("value", ""), 120),
                    "reference_range": self._format_for_display(latest.get("reference_range", ""), 80),
                    "date": latest.get("date", ""),
                    "notes": latest.get("notes", ""),
                },
                "status": status,
                "trend": trend,
                "history": history,
            })

        groups.sort(
            key=lambda g: self._parse_test_date_for_sort(g["latest"]),
            reverse=True,
        )

        seen_flagged = set()
        unique_flagged = []
        for item in flagged:
            flag_key = (
                self._normalize_test_key(item.get("test_name", "")),
                item.get("date", ""),
                self._normalize_value_for_compare(item.get("value", "")),
            )
            if flag_key in seen_flagged:
                continue
            seen_flagged.add(flag_key)
            unique_flagged.append(item)

        unique_flagged.sort(
            key=lambda item: self._parse_test_date_for_sort(item),
            reverse=True,
        )

        insights = [
            i.get("insight", "")
            for i in self.data.get("conversation_insights", [])
            if i.get("category") == "test_results" or i.get("source") == "auto_test_analysis"
        ]
        insights = [text for text in insights if text][-5:]

        date_range = {}
        if all_dates:
            date_range = {
                "from": self._format_summary_date(min(all_dates)),
                "to": self._format_summary_date(max(all_dates)),
            }

        overview = {
            "total_results": len(tests),
            "unique_tests": len(groups),
            "date_range": date_range,
            "flagged_count": len(unique_flagged),
        }

        text_report = self._build_test_results_text_report(
            overview, groups, unique_flagged, insights, concise=concise
        )

        return {
            "has_results": True,
            "generated_at": generated_at,
            "patient_name": self.data.get("name", ""),
            "concise": concise,
            "overview": overview,
            "groups": groups,
            "flagged": unique_flagged,
            "insights": insights if not concise else [],
            "text_report": text_report,
        }

    # --- Context Generation ---

    def format_for_prompt(self, max_chars: int = 2000) -> str:
        """Format health profile as context for the AI prompt"""
        if (not self.data.get("name") and not self.data.get("conditions") and
            not self.data.get("symptoms") and not self.data.get("medications") and
            not self.data.get("supplements") and not self.data.get("test_results") and
            not self.data.get("action_plans") and not self.data.get("conversation_insights")):
            return ""

        sections = []

        # Personal (name omitted for anonymity)
        personal = self.data.get("personal", {})
        if personal:
            parts = []
            if personal.get("gender"):
                parts.append(personal['gender'])
            if personal.get("age"):
                parts.append(f"age {personal['age']}")
            if personal.get("blood_type"):
                parts.append(f"blood type {personal['blood_type']}")
            if personal.get("location"):
                parts.append(personal['location'])
            if parts:
                sections.append("Patient: " + ", ".join(parts))

        # Active conditions
        conditions = [c for c in self.data.get("conditions", []) if c.get("status") == "active"]
        if conditions:
            cond_text = "Active Conditions: " + "; ".join(
                f"{c['name']}" +
                (f" ({c['details']})" if c.get('details') else "") +
                (f" [diagnosed {c['diagnosed_date']}]" if c.get('diagnosed_date') else "") +
                (f" [recorded {c['added_at'][:10]}]" if c.get('added_at') else "")
                for c in conditions
            )
            sections.append(cond_text)

        # Current symptoms
        symptoms = self.data.get("symptoms", [])
        if symptoms:
            sym_text = "Current Symptoms: " + "; ".join(
                f"{s['description']}" +
                (f" [triggers: {', '.join(s['triggers'])}]" if s.get('triggers') else "") +
                (f" [onset {s['onset']}]" if s.get('onset') else "") +
                (f" [severity {s['severity']}]" if s.get('severity') else "") +
                (f" [recorded {s['added_at'][:10]}]" if s.get('added_at') else "")
                for s in symptoms[-5:]  # Last 5 symptoms
            )
            sections.append(sym_text)

        # Recent test results
        tests = self.data.get("test_results", [])
        if tests:
            test_text = "Recent Tests: " + "; ".join(
                f"{t['test_name']}: {t['value']}" + (f" (ref: {t['reference_range']})" if t.get('reference_range') else "")
                + (f" [{t['date']}]" if t.get('date') else "")
                for t in tests[-6:]  # Last 6 results
            )
            sections.append(test_text)

        # Diet summary
        diet = self.data.get("diet", {})
        if diet.get("daily_foods"):
            diet_text = "Daily Foods: " + ", ".join(diet["daily_foods"][:20])
            if diet.get("cooking_methods"):
                diet_text += f" | Cooking: {', '.join(diet['cooking_methods'])}"
            if diet.get("restrictions"):
                diet_text += f" | Avoids: {', '.join(diet['restrictions'])}"
            sections.append(diet_text)
        if diet.get("notes"):
            sections.append("Diet Notes: " + "; ".join(diet["notes"][-3:]))

        # Medications (prescribed drugs)
        medications = self.data.get("medications", [])
        if medications:
            med_text = "Medications: " + ", ".join(
                m['name'] +
                (f" {m['dose']}" if m.get('dose') else "") +
                (f" ({m['purpose']})" if m.get('purpose') else "") +
                (f" [recorded {m['added_at'][:10]}]" if m.get('added_at') else "")
                for m in medications
            )
            sections.append(med_text)

        # Supplements/herbs
        supplements = self.data.get("supplements", [])
        if supplements:
            sup_text = "Supplements/Herbs: " + ", ".join(
                s['name'] +
                (f" ({s['purpose']})" if s.get('purpose') else "") +
                (f" [recorded {s['added_at'][:10]}]" if s.get('added_at') else "")
                for s in supplements
            )
            sections.append(sup_text)

        # Lifestyle
        lifestyle = self.data.get("lifestyle", {})
        if lifestyle.get("sleep"):
            sleep = lifestyle["sleep"]
            sleep_text = "Sleep: " + "; ".join(f"{k}: {v}" for k, v in sleep.items())
            sections.append(sleep_text)

        # Active action plans
        plans = [p for p in self.data.get("action_plans", []) if p.get("status") == "active"]
        if plans:
            plan_text = "Active Plans: " + "; ".join(
                f"{p['title']}" + (f" [recorded {p['added_at'][:10]}]" if p.get('added_at') else "")
                for p in plans[-3:]
            )
            sections.append(plan_text)

        # Active follow-ups
        follow_ups = [f for f in self.data.get("follow_ups", []) if f.get("status") == "active"]
        if follow_ups:
            fu_text = "Active Follow-ups: " + "; ".join(
                f"{f['title']}" + (f" [due {f['due_date']}]" if f.get('due_date') else "") + (f" [recorded {f['added_at'][:10]}]" if f.get('added_at') else "")
                for f in follow_ups[-3:]
            )
            sections.append(fu_text)

        # Open questions for the doctor
        questions = [q for q in self.data.get("questions_for_doctor", []) if not q.get("answered")]
        if questions:
            q_text = "Questions for Doctor: " + "; ".join(
                f"{q['question']}" + (f" [recorded {q['added_at'][:10]}]" if q.get('added_at') else "")
                for q in questions[-4:]
            )
            sections.append(q_text)

        # Key conversation insights
        insights = self.data.get("conversation_insights", [])
        if insights:
            insight_text = "Key Insights: " + "; ".join(
                i['insight'] for i in insights[-4:]
            )
            sections.append(insight_text)

        full_text = "\n".join(sections)

        # Truncate if needed
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."

        return full_text

    def to_dict(self) -> Dict:
        """Return full profile as dict"""
        return self.data.copy()


class HealthContextManager:
    """Manages health profiles for all users"""

    _profiles: Dict[str, HealthProfile] = {}

    @classmethod
    def get_profile(cls, user_id: str) -> HealthProfile:
        """Get or create a health profile for a user"""
        user_id = str(user_id)
        if user_id not in cls._profiles:
            cls._profiles[user_id] = HealthProfile(user_id)
        return cls._profiles[user_id]

    @classmethod
    def get_context_for_prompt(cls, user_id: str) -> str:
        """Get formatted health context for injection into AI prompt"""
        profile = cls.get_profile(user_id)
        context = profile.format_for_prompt()
        if not context:
            return ""
        return f"\n\n--- PATIENT HEALTH CONTEXT (use this to personalize responses) ---\n{context}\n--- END HEALTH CONTEXT ---\n"

    @classmethod
    def get_test_results_summary(cls, user_id: str, concise: bool = False) -> Dict:
        """Return a structured summary of the user's lab/test results."""
        profile = cls.get_profile(user_id)
        return profile.generate_test_results_summary(concise=concise)

    @classmethod
    def list_profiles(cls) -> List[str]:
        """List all stored profile user IDs"""
        HEALTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
        return [f.stem for f in HEALTH_DATA_DIR.glob("*.json")]

    @classmethod
    def analyze_and_store(cls, user_id: str, raw_text: str, save: bool = True) -> Dict:
        """Use AI to analyze raw health text and return structured data.
        If save=True, stores into the profile. Otherwise returns a pending-review object."""
        profile = cls.get_profile(user_id)

        # Build the analysis prompt (use only recent entries to keep prompt short and fast)
        _recent = 30
        existing_foods = profile.data.get("diet", {}).get("daily_foods", [])[-_recent:]
        existing_supplements = [s["name"] for s in profile.data.get("supplements", [])[-_recent:]]
        existing_conditions = [c["name"] for c in profile.data.get("conditions", [])[-_recent:]]
        existing_symptoms = [s["description"] for s in profile.data.get("symptoms", [])[-_recent:]]
        existing_restrictions = profile.data.get("diet", {}).get("restrictions", [])[-_recent:]
        existing_tests = [f"{t['test_name']}: {t['value']}" for t in profile.data.get("test_results", [])[-_recent:]]
        existing_plans = [p["title"] for p in profile.data.get("action_plans", [])[-_recent:] if p.get("status") == "active"]

        system_prompt = """You are a health data analyst. Analyze the user's health text and extract ALL structured data.
Return ONLY valid JSON with these keys (omit any that have no data):

{
  "foods": ["list of foods/ingredients mentioned that should be added to daily diet"],
  "food_notes": ["specific dietary notes, portion advice, or warnings about foods"],
  "restrictions": ["things to avoid or limit"],
  "medications": [{"name": "drug/medication name", "dose": "dosage", "purpose": "reason for taking"}],
  "supplements": [{"name": "supplement/vitamin/herb name", "dose": "dosage", "purpose": "reason for taking"}],
  "symptoms": [{"description": "...", "triggers": ["..."], "severity": "mild/moderate/severe"}],
  "conditions": [{"name": "...", "details": "...", "status": "active/investigating/resolved", "diagnosed_date": "date from report or when diagnosed, e.g. 12 May 2026"}],
  "test_results": [{"test_name": "...", "value": "plain string: numeric result + H/L flag if present + unit, e.g. '6.4 H mmol/L' or '0.8 mmol/L'. Preserve exact decimal places as shown in the report (e.g. '4.30 mmol/L' not '4.3 mmol/L')", "reference_range": "...", "date": "...", "notes": "..."}],
  "action_plans": [{"title": "...", "steps": ["..."], "priority": "high/medium/low"}],
  "next_steps": [{"title": "...", "steps": ["..."], "due_date": "YYYY-MM-DD or free text", "priority": "high/medium/low"}],
  "questions_for_doctor": [{"question": "...", "context": "...", "priority": "high/medium/low"}],
  "lifestyle_notes": ["exercise, sleep, or habit observations"],
  "warnings": ["critical warnings or drug interactions"],
  "insights": [{"insight": "key medical insight or observation", "category": "diagnosis/nutrition/lifestyle/herb_consideration/test_preparation/prognosis/exercise"}],
  "allergies": ["drug or food allergies/intolerances"],
  "personal": {"age": null, "weight": null, "height": null, "blood_type": null},
  "procedures": [{"name": "surgery/procedure name", "date": "when performed", "notes": "outcome or details"}],
  "family_history": ["family member + condition, e.g. father - prostate cancer"]
}

Rules:
- Only extract data that is EXPLICITLY stated in the text
- Do NOT infer or assume anything not stated
- For foods: only list NEW items not already in the user's profile
- Medications are prescribed drugs (e.g. tamsulosin, rosuvastatin). Supplements are vitamins/herbs/minerals (e.g. zinc, vitamin D, ashwagandha)
- ALWAYS extract the report/test date and include it in diagnosed_date for conditions and date for test_results. If a lab table has multiple date columns, create one test_result per test per date, using the column's date for that value.
- Keep test_result values as plain strings. Include any H/L flag and unit in the value string (e.g. "6.4 H mmol/L" or "368 pmol/L"). Do not use objects or nested values for value. Preserve the exact number of decimal places shown in the report (e.g. "4.30" not "4.3"); do not round values.
- Avoid duplicate entries by using the same test_name and date for the same measurement.
- If a document has a date (e.g. "12 May 2026"), use it for ALL conditions and tests found in that document
- Extract allergies, personal info (age, weight, height, blood type), procedures, and family history if mentioned
- Do not skip any row in a lab table, including any individual test (vitamins, minerals, electrolytes, enzymes, hormones, blood counts, lipids, or any other lab category). Create one test_result per row per date column.
- If a lab table has only one test row repeated across many date columns, create one test_result for EACH date and value pair.
- Be concise but precise
- Return raw JSON only, no markdown fences
- Do not create a test_result for the overall report title/heading (e.g. the "Name of Test" value) or for non-test table rows such as "Lab ID.", "Reference", "Units", or "Date".
- If a test name begins with a marker such as * or +, remove the marker and keep only the test name (e.g. "*HbA1c (NGSP)" becomes "HbA1c (NGSP)").
- When the extracted text contains one line per test per date in "DATE | TEST_NAME | VALUE | REFERENCE_RANGE | UNIT" format, use each line directly to build the test_result list.
- Example for any multi-date lab table: if the date columns are D1, D2, D3 and a row is "TEST_NAME | v1 | v2 | v3 | (reference) | unit", return one test_result per date: {"test_name": "TEST_NAME", "value": "v1 unit", "reference_range": "(reference)", "date": "D1"}, then {"test_name": "TEST_NAME", "value": "v2 unit", "reference_range": "(reference)", "date": "D2"}, then {"test_name": "TEST_NAME", "value": "v3 unit", "reference_range": "(reference)", "date": "D3"}. Use the actual column header dates from the table, not a placeholder, for the date field.
- For tables with multiple date columns, do not stop at the latest or rightmost date. Create one test_result for every date column, for every test row.
- Do not combine multiple date values into a single value string such as "v1, v2, v3" or "v1 / v2 / v3".
- Take each value and unit from that test's own row. Do not swap or shift values between adjacent rows and do not drop the unit.
- Never collapse multiple date columns into a single object or combined string value."""

        user_prompt = f"""EXISTING PATIENT PROFILE:
- Daily foods: {', '.join(existing_foods)}
- Supplements: {', '.join(existing_supplements)}
- Conditions: {', '.join(existing_conditions)}
- Symptoms: {', '.join(existing_symptoms)}
- Restrictions: {', '.join(existing_restrictions)}
- Recent tests: {', '.join(existing_tests)}
- Active plans: {', '.join(existing_plans)}

NEW TEXT TO ANALYZE:
{raw_text}"""

        def _parse_markdown_tables(text):
            """Extract test_results from markdown tables in raw OCR text.

            The vision model now returns lab tables in markdown form.  Instead of
            letting the JSON analysis model re-interpret (and possibly shift or
            round) the numbers, we parse those tables directly and use them as
            the test_results list.
            """
            results = []
            lines = text.splitlines()
            i = 0
            while i < len(lines):
                if not lines[i].strip().startswith('|'):
                    i += 1
                    continue
                block = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    block.append(lines[i])
                    i += 1
                if len(block) < 3:
                    continue

                # Split on |, ignoring the leading/trailing empty cells from the outer pipes
                rows = []
                for line in block:
                    cells = [c.strip() for c in line.strip().split('|')[1:-1] if True]
                    rows.append(cells)

                # Identify the separator/header row (all cells are --- or :---:)
                sep_idx = None
                for idx, row in enumerate(rows):
                    if all(re.match(r'^:?-+:?$', cell) or cell == '' for cell in row):
                        sep_idx = idx
                        break
                if sep_idx is None or sep_idx == 0:
                    continue

                headers = rows[0]
                ref_idx = None
                unit_idx = None
                for idx, h in enumerate(headers):
                    if re.search(r'\b(refer|ref|reference)', h, re.I):
                        ref_idx = idx
                    if re.search(r'\bunit', h, re.I):
                        unit_idx = idx

                # Date columns sit between the test-name column (0) and reference/unit columns
                end_candidates = [x for x in [ref_idx, unit_idx, len(headers)] if x is not None]
                end_idx = min(end_candidates)
                date_cols = list(range(1, end_idx))
                if not date_cols:
                    continue

                # Fix "Latest" / "Latest Results" headers: search the full text for
                # a date pattern near those words and replace the header.
                full_text = '\n'.join(lines)
                for d_idx in date_cols:
                    h = headers[d_idx].strip()
                    if re.search(r'latest', h, re.I):
                        # Look for a date pattern (e.g. 03-Apr-25, 03/04/2025) in the text
                        # near the word "Latest" or in the column header itself
                        date_match = re.search(r'(\d{1,2}[-/\s][A-Za-z]{3,9}[-/\s]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', h)
                        if not date_match:
                            # Search the full text for dates that appear after the previous column header
                            date_match = re.search(r'(\d{1,2}[-/\s][A-Za-z]{3,9}[-/\s]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', full_text)
                        if date_match:
                            headers[d_idx] = date_match.group(1)

                for row in rows[sep_idx + 1:]:
                    if not row or len(row) < 2:
                        continue
                    test_name = row[0].strip()
                    if not test_name or re.search(r'^(Date|Time|Lab|Reference|Unit|Name of|Patient|Request|Collection|Received|Barcode|Page|Report)', test_name, re.I):
                        continue
                    test_name = re.sub(r'^[*+]\s*', '', test_name).strip()
                    reference = row[ref_idx] if ref_idx is not None and ref_idx < len(row) else ''
                    unit = row[unit_idx] if unit_idx is not None and unit_idx < len(row) else ''
                    for d_idx in date_cols:
                        if d_idx >= len(row):
                            continue
                        date = headers[d_idx].strip()
                        val = row[d_idx].strip()
                        if not val:
                            continue
                        if unit and not re.search(re.escape(unit), val, re.I):
                            val = (val + ' ' + unit).strip()
                        results.append({
                            "test_name": test_name,
                            "value": val,
                            "reference_range": reference,
                            "date": date,
                            "notes": ""
                        })
            return results

        def _clean_and_parse(text):
            text = text.strip()
            # Strip markdown code fences if present
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()
            # Some models wrap JSON in commentary; extract the outermost JSON object/array
            if '{' in text and '}' in text:
                start = text.find('{')
                end = text.rfind('}')
                text = text[start:end+1]
            elif '[' in text and ']' in text:
                start = text.find('[')
                end = text.rfind(']')
                text = text[start:end+1]
            return json.loads(text, parse_float=Decimal)

        def _dec_to_str(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            if isinstance(obj, list):
                return [_dec_to_str(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _dec_to_str(v) for k, v in obj.items()}
            return obj

        try:
            result_text = _health_ai_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.0,
                model='gpt-4o'
            ).strip()
            extracted = _dec_to_str(_clean_and_parse(result_text))

            # Prefer the OCR markdown table values over any AI-re-interpreted ones,
            # but keep any (test, date) pair the table parse missed so a dropped row
            # is still recovered from the AI extraction.
            parsed_from_table = _parse_markdown_tables(raw_text)
            if parsed_from_table:
                def _key(t):
                    return (str(t.get('test_name', '')).strip().lower(),
                            str(t.get('date', '')).strip().lower())
                merged = list(parsed_from_table)
                seen = {_key(t) for t in merged}
                for t in extracted.get('test_results', []) or []:
                    if isinstance(t, dict) and _key(t) not in seen and t.get('test_name'):
                        merged.append(t)
                        seen.add(_key(t))
                extracted['test_results'] = merged

            # Remove H/L/High/Low flags from values that are actually within reference range
            for t in extracted.get('test_results', []):
                t['value'] = profile._clean_test_value(t.get('value', ''), t.get('reference_range', ''))

            if not save:
                return {"success": True, "extracted": extracted, "pending_review": extracted, "actions": []}

        except json.JSONDecodeError:
            # Retry once with a stricter prompt and the stronger gpt-4o model
            try:
                retry_prompt = f"""The previous response was not valid JSON. Return ONLY valid JSON for this health text, with no explanation, no markdown, and no markdown fences. Use the exact schema below.

{system_prompt}

Text to analyze:
{raw_text}"""
                result_text = _health_ai_chat(
                    messages=[
                        {"role": "system", "content": "You are a strict JSON-only health data extractor. Return only the requested JSON."},
                        {"role": "user", "content": retry_prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.0,
                    model='gpt-4o'
                ).strip()
                extracted = _clean_and_parse(result_text)
            except json.JSONDecodeError:
                # AI still returned non-JSON; store as raw insight
                profile.add_conversation_insight(raw_text, category="general")
                profile.save()
                return {"error": "AI returned non-parseable data", "stored_as_insight": True,
                        "actions": ["Saved as raw insight"]}
        except Exception as e:
            # Fallback: store as raw insight
            profile.add_conversation_insight(raw_text, category="general")
            profile.save()
            return {"error": str(e), "stored_as_insight": True,
                    "actions": ["Saved as raw insight (AI unavailable)"]}

        # If only reviewing, return the extracted data without modifying the profile
        if not save:
            return {"success": True, "pending_review": extracted}

        # Apply extracted data using the shared method
        actions = profile.apply_extracted_data(extracted)

        if not actions:
            profile.add_conversation_insight(raw_text, category="general")
            profile.save()
            actions = ["No structured data found — saved as raw insight"]

        # Second AI call: cross-reference new info against full profile for health advice
        health_advice = []
        try:
            advice_prompt = f"""You are a medical health advisor AI. The patient has an existing health profile.
New information was just added to their profile. Cross-reference the NEW information against their
EXISTING profile and provide specific, actionable health advice.

EXISTING PROFILE SUMMARY:
- Name: {profile.data.get('name', 'Unknown')}
- Conditions: {', '.join(existing_conditions)}
- Symptoms: {', '.join(existing_symptoms)}
- Current supplements: {', '.join(existing_supplements)}
- Current diet restrictions: {', '.join(existing_restrictions)}
- Recent test results: {', '.join(existing_tests)}
- Active plans: {', '.join(existing_plans)}
- Daily foods: {', '.join(existing_foods[:30])}

NEW INFORMATION JUST ADDED:
{raw_text}

DATA EXTRACTED FROM NEW INFO:
{json.dumps(extracted, indent=2)}

Provide health advice as a JSON array of objects:
[
  {{
    "advice": "specific advice text",
    "reason": "why this matters given the patient's profile",
    "priority": "high/medium/low",
    "category": "diet/symptom/interaction/lifestyle/warning"
  }}
]

Rules:
- Cross-reference new foods/supplements against existing conditions and symptoms
- Flag any potential interactions with existing supplements or medications
- Note if any new food could worsen or help existing symptoms
- Highlight anything that affects upcoming blood tests
- Be specific to THIS patient's profile, not generic advice
- Only include advice that is directly relevant
- Return raw JSON array only, no markdown fences"""

            advice_text = _health_ai_chat(
                messages=[
                    {"role": "system", "content": "You are a medical health advisor. Provide personalized advice based on the patient's full health profile. Return only valid JSON."},
                    {"role": "user", "content": advice_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            ).strip()
            if advice_text.startswith("```"):
                advice_text = re.sub(r'^```(?:json)?\s*', '', advice_text)
                advice_text = re.sub(r'\s*```$', '', advice_text)

            health_advice = json.loads(advice_text)

            # Store high-priority advice as conversation insights
            for adv in health_advice:
                if adv.get("priority") == "high" and adv.get("advice"):
                    profile.add_conversation_insight(
                        f"{adv['advice']} — Reason: {adv.get('reason', '')}",
                        category=adv.get("category", "general")
                    )
            if any(a.get("priority") == "high" for a in health_advice):
                profile.save()

        except Exception as e:
            health_advice = [{"advice": f"Could not generate advice: {str(e)}", "priority": "low", "category": "system"}]

        return {"success": True, "actions": actions, "extracted": extracted, "health_advice": health_advice}
