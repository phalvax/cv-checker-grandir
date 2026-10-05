#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import shutil
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from unidecode import unidecode


FAKER = Faker("fr_FR")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GENERATED_ROOT = PROJECT_ROOT / "data" / "cv" / "generated"
PROFILES_PATH = PROJECT_ROOT / "src" / "cv_checker" / "job_profiles.json"
TIMESTAMP_FMT = "%Y%m%d_%H%M%S"

LAYOUTS = [
    "basic",
    "two_col",
    "misaligned",
    "compact",
    "chaos",
    "zigzag",
    "floating_blocks",
    "staggered",
]
DIFFICULTIES = ["easy", "medium", "hard"]
STREET_TYPES = ["rue", "avenue", "boulevard", "allee", "impasse", "place", "route", "quai"]
CONTACT_LABELS = ["CONTACT", "COORDONNEES", "INFOS CONTACT", "CANAL CANDIDAT", "REPERE CONTACT"]

NOISE_SENTENCES = [
    "copie scanner avec artefacts de compression",
    "document converti automatiquement depuis smartphone",
    "mise en page partiellement degradee",
    "donnees personnelles diffusion restreinte",
    "some lines were auto reconstructed",
    "certaines zones sont hors alignement",
    "fichier recompose depuis capture mobile",
]

SEPARATOR_LINES = ["-----", "........", "/////", "| | | |", "-- -- --"]

DIPLOMA_FALLBACK = [
    "cap aepe",
    "bac pro assp",
    "de infirmier",
    "eje",
    "certification niveau 6",
]

SECTION_NAMES = {
    "profile": ["PROFIL", "PROFIL PROFESSIONNEL", "SYNTHSE", "OBJECTIF"],
    "keywords": ["MOTS CLES METIER", "REFERENTIEL POSTE", "REPERES POSTE"],
    "skills": ["COMPETENCES", "SAVOIR FAIRE", "CAPACITES"],
    "experience": ["EXPERIENCES PROFESSIONNELLES", "EXPERIENCES", "MISSIONS"],
    "formation": ["FORMATION", "PARCOURS", "DIPLOMES"],
    "languages": ["LANGUES", "IDIOMES"],
}

VOWELS = "aeiouy"
OCR_MAP = {
    "0": "O",
    "O": "0",
    "1": "l",
    "l": "1",
    "5": "S",
    "S": "5",
    "2": "Z",
    "Z": "2",
    "8": "B",
    "B": "8",
}
FONT_FAMILIES = [
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-Oblique",
    "Helvetica-BoldOblique",
    "Times-Roman",
    "Times-Bold",
    "Times-Italic",
    "Times-BoldItalic",
    "Courier",
    "Courier-Bold",
    "Courier-Oblique",
    "Courier-BoldOblique",
]


@dataclass
class CVRecord:
    file: str
    profile_name: str
    style: str
    difficulty: str
    first_name: str
    last_name: str
    email_clean: str
    phone_clean: str
    address_clean: str
    address_zip: str
    address_city: str
    contains_noise: bool
    typo_noise_count: int
    spaced_noise_count: int
    ocr_noise_count: int
    fragmented_lines: int
    keyword_anchor_count: int


def load_profiles() -> list[dict]:
    if PROFILES_PATH.exists():
        try:
            data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                out = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    out.append(
                        {
                            "name": str(item.get("name", "Profil")).strip() or "Profil",
                            "required": [str(x).strip() for x in item.get("required", []) if str(x).strip()],
                            "required_any": [str(x).strip() for x in item.get("required_any", []) if str(x).strip()],
                            "bonus": [str(x).strip() for x in item.get("bonus", []) if str(x).strip()],
                            "min_experience_years": int(item.get("min_experience_years") or 1),
                        }
                    )
                if out:
                    return out
        except Exception:
            pass

    return [
        {
            "name": "Auxiliaire petite enfance",
            "required": ["petite enfance", "accompagnement enfant"],
            "required_any": ["cap aepe", "eaje"],
            "bonus": ["travail d'equipe", "communication", "projet pedagogique"],
            "min_experience_years": 1,
        }
    ]


def normalize_slug(value: str) -> str:
    raw = unidecode(value).lower().strip()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw or "x"


def random_phone() -> str:
    return "0" + random.choice("123456789") + "".join(random.choice("0123456789") for _ in range(8))


def random_email(first: str, last: str) -> str:
    local = f"{normalize_slug(first)}.{normalize_slug(last)}{random.randint(1, 99)}"
    domain = random.choice(["gmail.com", "outlook.fr", "hotmail.fr", "icloud.com", "yahoo.fr"])
    return f"{local}@{domain}"


def random_address() -> tuple[str, str, str]:
    num = random.randint(1, 180)
    street = f"{random.choice(STREET_TYPES)} {FAKER.street_name()}"
    zip_code = FAKER.postcode()
    city = FAKER.city()
    return f"{num} {street}", zip_code, city


def pick_difficulty() -> str:
    return random.choices(DIFFICULTIES, weights=[0.1, 0.35, 0.55], k=1)[0]


def pick_layout(difficulty: str) -> str:
    if difficulty == "hard":
        return random.choices(
            LAYOUTS,
            weights=[0.05, 0.1, 0.15, 0.1, 0.2, 0.15, 0.15, 0.1],
            k=1,
        )[0]
    if difficulty == "medium":
        return random.choices(
            LAYOUTS,
            weights=[0.15, 0.2, 0.15, 0.15, 0.12, 0.1, 0.08, 0.05],
            k=1,
        )[0]
    return random.choices(
        LAYOUTS,
        weights=[0.35, 0.25, 0.1, 0.15, 0.05, 0.05, 0.03, 0.02],
        k=1,
    )[0]


def random_date_range() -> str:
    y1 = random.randint(2013, 2024)
    y2 = random.randint(y1, 2026)
    return random.choice(
        [
            f"{y1}-{y2}",
            f"{random.randint(1,12):02d}/{y1} - {random.randint(1,12):02d}/{y2}",
            f"de {y1} a {y2}",
            f"{y1} -> {y2}",
            f"{y1} -- {y2}",
        ]
    )


def _typo_word(word: str) -> str:
    letters = list(word)
    if len(letters) < 4:
        return word

    mode = random.choice(["drop", "swap", "double", "replace"])
    idx = random.randint(1, len(letters) - 2)

    if mode == "drop":
        del letters[idx]
    elif mode == "swap":
        letters[idx], letters[idx + 1] = letters[idx + 1], letters[idx]
    elif mode == "double":
        letters.insert(idx, letters[idx])
    else:
        if letters[idx].lower() in VOWELS:
            letters[idx] = random.choice(list(VOWELS))
        else:
            letters[idx] = random.choice(list("bcdfghjklmnpqrstvwxz"))
    return "".join(letters)


def _spacing_prob(difficulty: str) -> float:
    return {"easy": 0.05, "medium": 0.16, "hard": 0.30}[difficulty]


def _typo_prob(difficulty: str) -> float:
    return {"easy": 0.03, "medium": 0.12, "hard": 0.22}[difficulty]


def _ocr_prob(difficulty: str) -> float:
    return {"easy": 0.02, "medium": 0.08, "hard": 0.18}[difficulty]


def mutate_line(line: str, difficulty: str, protect: bool = False) -> tuple[str, int, int, int, int]:
    if not line:
        return line, 0, 0, 0, 0

    # In hard mode, even protected lines can be partially degraded.
    if protect and not (difficulty == "hard" and random.random() < 0.45):
        return line, 0, 0, 0, 0

    spacing_p = _spacing_prob(difficulty)
    typo_p = _typo_prob(difficulty)
    ocr_p = _ocr_prob(difficulty)

    spaced = 0
    typos = 0
    ocr = 0
    fragments = 0

    words = line.split()
    out_words: list[str] = []

    for w in words:
        raw_letters = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ]", "", w)
        nw = w

        # spaced words
        if len(raw_letters) >= 5 and random.random() < spacing_p:
            if re.search(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+$", raw_letters):
                nw = nw.replace(raw_letters, " ".join(list(raw_letters)), 1)
                spaced += 1

        # typos
        if len(raw_letters) >= 5 and random.random() < typo_p:
            typo = _typo_word(raw_letters)
            nw = nw.replace(raw_letters, typo, 1)
            typos += 1

        # ocr substitutions
        chars = list(nw)
        mutated = False
        for i, ch in enumerate(chars):
            if ch in OCR_MAP and random.random() < ocr_p:
                chars[i] = OCR_MAP[ch]
                mutated = True
        if mutated:
            ocr += 1
        nw = "".join(chars)

        # fragmentation (line-break injection marker that renderer will naturally wrap)
        if difficulty in {"medium", "hard"} and len(nw) > 8 and random.random() < (0.05 if difficulty == "medium" else 0.12):
            cut = random.randint(3, len(nw) - 3)
            nw = nw[:cut] + " " + nw[cut:]
            fragments += 1

        out_words.append(nw)

    out = " ".join(out_words)

    if difficulty in {"medium", "hard"} and random.random() < 0.18:
        out = out.replace("'", " ` ")
    if difficulty == "hard" and random.random() < 0.12:
        out = out.replace("-", " -- ")

    return out, typos, spaced, ocr, fragments


def display_phone(phone: str, difficulty: str) -> str:
    pairs = [phone[i : i + 2] for i in range(0, len(phone), 2)]
    if difficulty == "hard":
        return random.choice(
            [
                f"+33 {phone[1]} {' '.join([phone[2:4], phone[4:6], phone[6:8], phone[8:10]])}",
                " ".join(pairs).replace("0", "O", 1),
                ".".join(pairs),
                "-".join(pairs),
                " ".join(pairs[:2]) + " / " + " ".join(pairs[2:]),
            ]
        )
    if difficulty == "medium":
        return random.choice([" ".join(pairs), ".".join(pairs), "-".join(pairs)])
    return " ".join(pairs)


def display_email(email: str, difficulty: str) -> str:
    if difficulty == "hard":
        return random.choice(
            [
                email.replace("@", " @ ").replace(".", " . "),
                email.replace("@", " arobase ").replace(".", " point "),
                email,
                email.replace("@", "(at)").replace(".", "(dot)"),
            ]
        )
    if difficulty == "medium" and random.random() < 0.45:
        return email.replace("@", " @ ").replace(".", " . ")
    return email


def display_address(street: str, zip_code: str, city: str, difficulty: str) -> list[str]:
    if difficulty == "hard":
        style = random.choice(["zip_city", "city_zip", "split", "full", "split_frag"])
    else:
        style = random.choice(["full", "split", "zip_city", "city_zip"])

    if style == "zip_city":
        return [f"{zip_code} {city}"]
    if style == "city_zip":
        return [f"{city} {zip_code}"]
    if style == "split":
        return [street, f"{zip_code} {city}"]
    if style == "split_frag":
        return [street[: max(6, len(street) // 2)], street[max(6, len(street) // 2) :], f"{zip_code} {city}"]
    return [f"{street}, {zip_code} {city}"]


def pick_diploma(profile: dict) -> str:
    candidates = [x for x in profile.get("required_any", []) if x]
    if not candidates:
        return random.choice(DIPLOMA_FALLBACK)

    diploma_like = [
        x
        for x in candidates
        if any(tok in x.lower() for tok in ["cap", "bac", "de ", "diplome", "certification", "eje", "ide", "ipde"])
    ]
    if diploma_like:
        return random.choice(diploma_like)
    return random.choice(candidates)


def section_title(kind: str) -> str:
    return random.choice(SECTION_NAMES[kind])


def build_sections(record: CVRecord, profile: dict) -> tuple[dict[str, list[tuple[str, bool]]], int]:
    required = list(profile.get("required", []))
    required_any = list(profile.get("required_any", []))
    bonus = list(profile.get("bonus", []))

    anchors: list[str] = []
    anchors.extend(required)
    if required_any:
        anchors.append(random.choice(required_any))
    anchors.extend(random.sample(bonus, k=min(len(bonus), 4)))

    min_exp = max(1, int(profile.get("min_experience_years") or 1))
    exp_years = random.randint(min_exp, min_exp + 7)
    anchors.append(f"experience professionnelle: {exp_years} ans")

    header = [
        (f"{record.first_name} {record.last_name}", True),
        (profile["name"], True),
        ("", False),
    ]

    contact_block = [
        (random.choice(CONTACT_LABELS), False),
        (f"Tel: {display_phone(record.phone_clean, record.difficulty)}", True),
        (f"Mail: {display_email(record.email_clean, record.difficulty)}", True),
    ]
    for addr_line in display_address(record.address_clean, record.address_zip, record.address_city, record.difficulty):
        contact_block.append((addr_line, True))
    contact_block.append(("", False))

    profile_block = [
        (section_title("profile"), False),
        (
            random.choice(
                [
                    "Candidate motivee, adaptable, et orientee qualite d accueil des enfants et des familles.",
                    "Profil terrain, organisation solide, et bonne coordination avec les equipes.",
                    "Appui operationnel et pedagogique sur des contextes exigeants.",
                ]
            ),
            False,
        ),
        ("", False),
    ]

    keyword_block: list[tuple[str, bool]] = [(section_title("keywords"), True)]
    for kw in anchors:
        keyword_block.append((f"- {kw}", True))
    keyword_block.append(("", False))

    skill_pool = required + bonus + ["communication", "organisation", "transmissions parents", "hygiene", "securite"]
    skills_block: list[tuple[str, bool]] = [(section_title("skills"), False)]
    for kw in random.sample(skill_pool, k=min(len(skill_pool), random.randint(6, 10))):
        skills_block.append((f"- {kw}", False))
    skills_block.append(("", False))

    exp_block: list[tuple[str, bool]] = [(section_title("experience"), False)]
    for _ in range(random.randint(5, 8)):
        structure = random.choice(["creche", "multi-accueil", "ecole maternelle", "micro-creche", "halte-garderie"])
        task = random.choice(skill_pool)
        exp_block.append((f"- {random_date_range()} : {structure}", False))
        exp_block.append((f"  - {task}", False))
    exp_block.append(("", False))

    formation_block = [
        (section_title("formation"), False),
        (f"- {random.randint(2016, 2024)} : {pick_diploma(profile)}", True),
        (f"- {random.randint(2012, 2019)} : bac pro assp", False),
        ("", False),
    ]

    lang_block = [
        (section_title("languages"), False),
        ("- francais courant", False),
        (random.choice(["- anglais intermediaire", "- anglais scolaire", "- espagnol notions"]), False),
    ]

    noise_block: list[tuple[str, bool]] = []
    if record.contains_noise:
        noise_block.append(("", False))
        for _ in range(random.randint(1, 3 if record.difficulty == "hard" else 2)):
            noise_block.append((random.choice(NOISE_SENTENCES), False))
        if record.difficulty == "hard":
            noise_block.append(("R E C H E R C H E  D E  M P L O I", False))
            noise_block.append((random.choice(SEPARATOR_LINES), False))

    sections = {
        "header": header,
        "contact": contact_block,
        "profile": profile_block,
        "keywords": keyword_block,
        "skills": skills_block,
        "experience": exp_block,
        "formation": formation_block,
        "languages": lang_block,
        "noise": noise_block,
    }
    return sections, len(anchors)


def compose_document_lines(sections: dict[str, list[tuple[str, bool]]], difficulty: str) -> list[tuple[str, bool]]:
    ordered: list[tuple[str, bool]] = []

    ordered.extend(sections["header"])

    core_keys = ["contact", "profile", "keywords", "skills", "experience", "formation", "languages"]

    if difficulty == "easy":
        keys = core_keys
    elif difficulty == "medium":
        keys = core_keys[:]
        tail = keys[2:]
        random.shuffle(tail)
        keys = keys[:2] + tail
    else:
        keys = core_keys[:]
        random.shuffle(keys)
        # ensure contact and keywords are not both at top
        if keys[0] in {"contact", "keywords"} and keys[1] in {"contact", "keywords"}:
            keys[1], keys[-1] = keys[-1], keys[1]

    for k in keys:
        block = sections[k][:]
        if difficulty == "hard" and random.random() < 0.22 and len(block) > 5:
            # split one block into two distant fragments
            cut = random.randint(2, len(block) - 2)
            ordered.extend(block[:cut])
            ordered.append((random.choice(SEPARATOR_LINES), False))
            ordered.extend(sections.get("noise", []))
            ordered.extend(block[cut:])
        else:
            ordered.extend(block)

        if random.random() < (0.2 if difficulty == "easy" else 0.35 if difficulty == "medium" else 0.55):
            ordered.append((random.choice(SEPARATOR_LINES), False))

    if sections.get("noise"):
        if difficulty == "hard":
            insert_pos = random.randint(max(1, len(ordered) // 4), max(2, len(ordered) - 1))
            ordered[insert_pos:insert_pos] = sections["noise"]
        else:
            ordered.extend(sections["noise"])

    # extra random empty lines / shuffles for hard mode
    if difficulty == "hard":
        for _ in range(random.randint(5, 12)):
            idx = random.randint(0, len(ordered))
            ordered.insert(idx, ("", False))

    return ordered


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _jitter_color(base: tuple[float, float, float], spread: float) -> tuple[float, float, float]:
    return tuple(_clamp01(c + random.uniform(-spread, spread)) for c in base)


def _pick_background_color(difficulty: str) -> tuple[float, float, float]:
    if difficulty == "easy":
        palette = [(0.98, 0.98, 0.98), (0.95, 0.97, 0.99), (0.99, 0.97, 0.93)]
        return _jitter_color(random.choice(palette), 0.03)
    if difficulty == "medium":
        palette = [(0.91, 0.93, 0.86), (0.85, 0.91, 0.95), (0.93, 0.86, 0.90), (0.88, 0.88, 0.88)]
        return _jitter_color(random.choice(palette), 0.08)
    palette = [(0.16, 0.20, 0.24), (0.30, 0.24, 0.18), (0.86, 0.82, 0.72), (0.56, 0.66, 0.76), (0.72, 0.56, 0.61)]
    return _jitter_color(random.choice(palette), 0.15)


def _pick_text_color(background: tuple[float, float, float], difficulty: str) -> tuple[float, float, float]:
    lum = (0.2126 * background[0]) + (0.7152 * background[1]) + (0.0722 * background[2])
    dark = (random.uniform(0.02, 0.24), random.uniform(0.02, 0.24), random.uniform(0.02, 0.24))
    light = (random.uniform(0.72, 0.98), random.uniform(0.72, 0.98), random.uniform(0.72, 0.98))

    if difficulty == "easy":
        return dark if lum > 0.5 else light

    if difficulty == "medium":
        if random.random() < 0.72:
            return dark if lum > 0.54 else light
        inv = (1.0 - background[0], 1.0 - background[1], 1.0 - background[2])
        return _jitter_color(inv, 0.16)

    roll = random.random()
    if roll < 0.40:
        # hard mode: near-background text to reduce contrast.
        return _jitter_color(background, 0.13)
    if roll < 0.78:
        inv = (1.0 - background[0], 1.0 - background[1], 1.0 - background[2])
        return _jitter_color(inv, 0.24)
    return (
        random.uniform(0.10, 0.90),
        random.uniform(0.10, 0.90),
        random.uniform(0.10, 0.90),
    )


def _decorate_page(c: canvas.Canvas, page_w: float, page_h: float, difficulty: str, bg: tuple[float, float, float]) -> None:
    c.setFillColor(colors.Color(*bg))
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    band_count = random.randint(1, 2) if difficulty == "easy" else random.randint(2, 4) if difficulty == "medium" else random.randint(3, 7)
    for _ in range(band_count):
        tone = _jitter_color(bg, 0.06 if difficulty == "easy" else 0.12 if difficulty == "medium" else 0.20)
        y = random.uniform(0, page_h * 0.95)
        h = random.uniform(page_h * 0.015, page_h * (0.035 if difficulty == "easy" else 0.06))
        c.setFillColor(colors.Color(*tone))
        c.rect(0, y, page_w, h, stroke=0, fill=1)

    rect_count = random.randint(1, 3) if difficulty == "easy" else random.randint(3, 6) if difficulty == "medium" else random.randint(6, 12)
    for _ in range(rect_count):
        tone = _jitter_color(bg, 0.08 if difficulty == "easy" else 0.16 if difficulty == "medium" else 0.25)
        x = random.uniform(-20, page_w * 0.9)
        y = random.uniform(-30, page_h * 0.9)
        w = random.uniform(page_w * 0.08, page_w * (0.22 if difficulty == "easy" else 0.36))
        h = random.uniform(page_h * 0.03, page_h * (0.10 if difficulty == "easy" else 0.18))
        c.setFillColor(colors.Color(*tone))
        c.rect(x, y, w, h, stroke=0, fill=1)

    if difficulty in {"medium", "hard"}:
        circle_count = random.randint(2, 5 if difficulty == "medium" else 10)
        for _ in range(circle_count):
            tone = _jitter_color(bg, 0.18 if difficulty == "medium" else 0.28)
            x = random.uniform(-page_w * 0.1, page_w * 1.1)
            y = random.uniform(-page_h * 0.1, page_h * 1.1)
            r = random.uniform(10, 36 if difficulty == "medium" else 64)
            c.setFillColor(colors.Color(*tone))
            c.circle(x, y, r, stroke=0, fill=1)

    if difficulty in {"medium", "hard"}:
        c.setStrokeColor(colors.Color(*_jitter_color(bg, 0.30)))
        c.setLineWidth(random.uniform(0.25, 0.8 if difficulty == "hard" else 0.55))
        line_count = random.randint(2, 4 if difficulty == "medium" else 8)
        for _ in range(line_count):
            c.line(
                random.uniform(0, page_w),
                random.uniform(0, page_h),
                random.uniform(0, page_w),
                random.uniform(0, page_h),
            )


def _font_pool_for(base_fonts: list[str], difficulty: str) -> list[str]:
    if difficulty == "easy":
        if random.random() < 0.45:
            return list(dict.fromkeys(base_fonts + ["Helvetica-Bold", "Times-Italic"]))
        return list(dict.fromkeys(base_fonts))
    if difficulty == "medium":
        return list(dict.fromkeys(base_fonts + ["Helvetica-Bold", "Helvetica-Oblique", "Times-Bold", "Times-Italic", "Courier-Bold"]))
    return list(dict.fromkeys(base_fonts + FONT_FAMILIES))


def _apply_line_style(
    c: canvas.Canvas,
    difficulty: str,
    background: tuple[float, float, float],
    base_fonts: list[str],
    base_sizes: list[float],
) -> None:
    font_name = random.choice(_font_pool_for(base_fonts, difficulty))
    size = random.choice(base_sizes)
    if difficulty == "easy":
        size += random.uniform(-0.2, 0.4)
    elif difficulty == "medium":
        size += random.uniform(-0.6, 0.8)
    else:
        size += random.uniform(-1.0, 1.1)
    c.setFont(font_name, max(6.8, size))
    c.setFillColor(colors.Color(*_pick_text_color(background, difficulty)))


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: int, step: float) -> float:
    for part in textwrap.wrap(text, width=width) or [""]:
        c.drawString(x, y, part)
        y -= step
    return y


def render_pdf(lines: list[str], output_pdf: Path, style: str, difficulty: str) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    page_w, page_h = A4
    page_bg = (1.0, 1.0, 1.0)

    def start_page() -> None:
        nonlocal page_bg
        page_bg = _pick_background_color(difficulty)
        _decorate_page(c, page_w, page_h, difficulty, page_bg)

    start_page()

    if style == "two_col":
        left_y = page_h - 34
        right_y = page_h - 38
        for line in lines:
            col = random.choice([0, 1]) if difficulty != "easy" else (0 if left_y >= right_y else 1)
            if col == 0:
                if left_y < 34:
                    c.showPage()
                    start_page()
                    left_y = page_h - 34
                    right_y = page_h - 38
                _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Times-Roman"], [9.2 if difficulty == "hard" else 10.0])
                left_y = draw_wrapped(c, line, 30 + random.uniform(-2, 3), left_y, 50, random.uniform(11.4, 13.6))
                if not line.strip():
                    left_y -= random.uniform(1, 4)
            else:
                if right_y < 34:
                    c.showPage()
                    start_page()
                    left_y = page_h - 34
                    right_y = page_h - 38
                _apply_line_style(
                    c,
                    difficulty,
                    page_bg,
                    ["Helvetica", "Courier", "Times-Roman"],
                    [9.0 if difficulty == "hard" else 9.8],
                )
                right_y = draw_wrapped(c, line, page_w / 2 + 6 + random.uniform(-3, 3), right_y, 50, random.uniform(11.2, 13.8))
                if not line.strip():
                    right_y -= random.uniform(1, 4)

    elif style == "misaligned":
        y = page_h - 30
        for line in lines:
            if y < 28:
                c.showPage()
                start_page()
                y = page_h - 30
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Times-Roman", "Courier"], [8.6, 9.2, 10.0, 11.2])
            x = random.uniform(22, 150) if difficulty == "hard" else random.uniform(30, 90)
            if random.random() < (0.12 if difficulty == "hard" else 0.04):
                c.saveState()
                c.translate(x, y)
                c.rotate(random.uniform(-2.8, 2.8))
                for part in textwrap.wrap(line, width=90) or [""]:
                    c.drawString(0, 0, part)
                    line_step = random.uniform(10.8, 14.8)
                    y -= line_step
                    c.translate(0, -line_step)
                c.restoreState()
            else:
                y = draw_wrapped(c, line, x, y, 95, random.uniform(11.0, 14.6))
            if not line.strip():
                y -= random.uniform(1, 4)

    elif style == "compact":
        y = page_h - 26
        for line in lines:
            if y < 28:
                c.showPage()
                start_page()
                y = page_h - 26
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Courier"], [8.4 if difficulty == "hard" else 9.2])
            y = draw_wrapped(c, line, 22 + random.uniform(-2, 2), y, 115, random.uniform(10.5, 12.4))
            if not line.strip():
                y -= random.uniform(0.5, 3)

    elif style == "chaos":
        cols_x = [22, 170, 320, 460]
        cols_y = [page_h - 30, page_h - 40, page_h - 35, page_h - 28]
        widths = [28, 30, 34, 26]
        for line in lines:
            col = random.choices([0, 1, 2, 3], weights=[0.26, 0.28, 0.28, 0.18], k=1)[0]
            if cols_y[col] < 32:
                c.showPage()
                start_page()
                cols_y = [page_h - 30, page_h - 40, page_h - 35, page_h - 28]
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Courier", "Times-Roman"], [8.0, 8.6, 9.2, 10.0])
            cols_y[col] = draw_wrapped(
                c,
                line,
                cols_x[col] + random.uniform(-6, 10),
                cols_y[col],
                widths[col],
                random.uniform(10.2, 13.8),
            )
            if not line.strip():
                cols_y[col] -= random.uniform(1.0, 5.0)

    elif style == "zigzag":
        y = page_h - 32
        side = 0
        x_positions = [24, 120, 240, 380]
        for line in lines:
            if y < 32:
                c.showPage()
                start_page()
                y = page_h - 32
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Times-Roman"], [8.8, 9.5, 10.2])
            x = x_positions[side] + random.uniform(-5, 8)
            y = draw_wrapped(c, line, x, y, random.choice([36, 48, 60]), random.uniform(10.8, 13.8))
            side = (side + random.choice([1, 2])) % len(x_positions)
            if not line.strip():
                y -= random.uniform(1, 4)

    elif style == "floating_blocks":
        chunks: list[list[str]] = []
        i = 0
        while i < len(lines):
            size = random.randint(5, 14)
            chunks.append(lines[i : i + size])
            i += size

        block_x = [22, 180, 340]
        block_y = [page_h - 40, page_h - 120, page_h - 220, page_h - 320, page_h - 420, page_h - 520]
        bi = 0
        for chunk in chunks:
            if bi >= len(block_y):
                c.showPage()
                start_page()
                bi = 0
            x = random.choice(block_x) + random.uniform(-12, 20)
            y = block_y[bi] + random.uniform(-10, 12)
            bi += 1

            c.saveState()
            c.translate(x, y)
            c.rotate(random.uniform(-2.5, 2.5))
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Courier", "Times-Roman"], [8.0, 8.8, 9.6])
            yy = 0
            for line in chunk:
                for part in textwrap.wrap(line, width=random.choice([26, 32, 38, 46])) or [""]:
                    c.drawString(0, yy, part)
                    yy -= random.uniform(10.2, 13.6)
                if not line.strip():
                    yy -= random.uniform(1, 4)
            c.restoreState()

    elif style == "staggered":
        y = page_h - 30
        for line in lines:
            if y < 28:
                c.showPage()
                start_page()
                y = page_h - 30
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Courier", "Times-Roman"], [8.4, 9.0, 9.6, 10.4])
            x = 24 + random.uniform(0, 220)
            width = random.choice([38, 52, 68, 84])
            y = draw_wrapped(c, line, x, y, width, random.uniform(10.8, 14.2))
            if not line.strip():
                y -= random.uniform(1.0, 4.0)

    else:
        y = page_h - 34
        for line in lines:
            if y < 34:
                c.showPage()
                start_page()
                y = page_h - 34
            _apply_line_style(c, difficulty, page_bg, ["Helvetica", "Times-Roman"], [9.4, 10.0, 10.4])
            y = draw_wrapped(c, line, 30 + random.uniform(-3, 5), y, 100, random.uniform(11.6, 13.8))
            if not line.strip():
                y -= random.uniform(1, 4)

    c.save()


def generate_dataset(output_dir: Path, count: int, seed: int) -> dict:
    random.seed(seed)
    Faker.seed(seed)

    profiles = load_profiles()
    pdf_dir = output_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    records: list[CVRecord] = []
    style_dist = {k: 0 for k in LAYOUTS}
    diff_dist = {k: 0 for k in DIFFICULTIES}
    profile_dist: dict[str, int] = {}

    for idx in range(1, count + 1):
        profile = random.choice(profiles)
        difficulty = pick_difficulty()
        style = pick_layout(difficulty)

        first = FAKER.first_name()
        last = FAKER.last_name().upper()
        email = random_email(first, last)
        phone = random_phone()
        street, zip_code, city = random_address()

        file_name = f"syn_{idx:04d}_{difficulty}_{style}.pdf"
        record = CVRecord(
            file=file_name,
            profile_name=profile["name"],
            style=style,
            difficulty=difficulty,
            first_name=first,
            last_name=last,
            email_clean=email,
            phone_clean=phone,
            address_clean=street,
            address_zip=zip_code,
            address_city=city,
            contains_noise=difficulty in {"medium", "hard"},
            typo_noise_count=0,
            spaced_noise_count=0,
            ocr_noise_count=0,
            fragmented_lines=0,
            keyword_anchor_count=0,
        )

        sections, anchor_count = build_sections(record, profile)
        paired_lines = compose_document_lines(sections, difficulty)

        final_lines: list[str] = []
        for line, protect in paired_lines:
            noisy, typos, spaced, ocr, frags = mutate_line(line, difficulty, protect=protect)
            final_lines.append(noisy)
            record.typo_noise_count += typos
            record.spaced_noise_count += spaced
            record.ocr_noise_count += ocr
            record.fragmented_lines += frags

        record.keyword_anchor_count = anchor_count

        render_pdf(final_lines, pdf_dir / file_name, style=style, difficulty=difficulty)

        records.append(record)
        style_dist[style] += 1
        diff_dist[difficulty] += 1
        profile_dist[profile["name"]] = profile_dist.get(profile["name"], 0) + 1

    metadata_csv = output_dir / "metadata.csv"
    with metadata_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()) if records else [])
        if records:
            writer.writeheader()
            for rec in records:
                writer.writerow(asdict(rec))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(records),
        "output_dir": str(output_dir.resolve()),
        "pdf_dir": str(pdf_dir.resolve()),
        "metadata_csv": str(metadata_csv.resolve()),
        "seed": seed,
        "style_distribution": style_dist,
        "difficulty_distribution": diff_dist,
        "profile_distribution": profile_dist,
        "avg_typo_noise": round(sum(r.typo_noise_count for r in records) / max(1, len(records)), 2),
        "avg_spaced_noise": round(sum(r.spaced_noise_count for r in records) / max(1, len(records)), 2),
        "avg_ocr_noise": round(sum(r.ocr_noise_count for r in records) / max(1, len(records)), 2),
        "avg_fragmented_lines": round(sum(r.fragmented_lines for r in records) / max(1, len(records)), 2),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic CV dataset.")
    parser.add_argument("--count", type=int, default=120, help="Number of synthetic CV PDFs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--generated-root",
        type=str,
        default=str(DEFAULT_GENERATED_ROOT),
        help="Root folder that stores generated runs.",
    )
    parser.add_argument("--output-dir", type=str, default=None, help="Explicit output directory.")
    parser.add_argument("--run-name", type=str, default=None, help="Run name when output-dir is omitted.")
    parser.add_argument(
        "--sync-latest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copy run to <generated-root>/latest.",
    )
    return parser.parse_args()


def resolve_output_dir(args: argparse.Namespace) -> tuple[Path, Path]:
    generated_root = Path(args.generated_root)
    if args.output_dir:
        return Path(args.output_dir), generated_root
    run_name = args.run_name or datetime.now().strftime(TIMESTAMP_FMT)
    return generated_root / run_name, generated_root


def sync_latest(output_dir: Path, generated_root: Path) -> Path:
    latest_dir = generated_root / "latest"
    try:
        same_target = latest_dir.resolve() == output_dir.resolve()
    except Exception:
        same_target = False
    if same_target:
        return latest_dir
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(output_dir, latest_dir)
    return latest_dir


def main() -> None:
    args = parse_args()
    output_dir, generated_root = resolve_output_dir(args)
    summary = generate_dataset(output_dir=output_dir, count=args.count, seed=args.seed)
    summary["generated_root"] = str(generated_root.resolve())

    if args.sync_latest:
        latest_dir = sync_latest(output_dir=output_dir, generated_root=generated_root)
        summary["latest_dir"] = str(latest_dir.resolve())

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
