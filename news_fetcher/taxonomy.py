import re
from typing import Dict, List, Sequence, Tuple


CATEGORIES: Tuple[str, ...] = (
    "AI & ML",
    "Cloud & Infrastructure",
    "DevOps & Reliability",
    "Software Engineering",
    "Security & Privacy",
    "Hardware & Emerging Tech",
    "General Tech",
)

TAGS: Tuple[str, ...] = (
    "ai",
    "architecture",
    "cloud",
    "cloud-native",
    "databases",
    "dev-tools",
    "hardware",
    "kubernetes",
    "networking",
    "observability",
    "open-source",
    "privacy",
    "programming",
    "research",
    "security",
    "web",
)

_TERMS: Dict[str, Tuple[str, ...]] = {
    "ai": (
        r"ai",
        r"artificial intelligence",
        r"machine learning",
        r"llms?",
        r"inference",
    ),
    "architecture": (
        r"architectur(?:e|al)",
        r"distributed systems?",
        r"microservices?",
        r"serverless",
    ),
    "cloud": (r"aws", r"azure", r"google cloud", r"cloud computing"),
    "cloud-native": (r"cloud[ -]native", r"containers?", r"cncf"),
    "databases": (
        r"databases?",
        r"sql",
        r"postgresql",
        r"mysql",
        r"data warehouses?",
    ),
    "dev-tools": (
        r"github",
        r"gitlab",
        r"ides?",
        r"compilers?",
        r"developer tools?",
        r"ci/cd",
    ),
    "hardware": (
        r"chips?",
        r"semiconductors?",
        r"cpus?",
        r"gpus?",
        r"quantum computing",
        r"robots?",
    ),
    "kubernetes": (r"kubernetes", r"k8s"),
    "networking": (r"dns", r"https?", r"networks?", r"tcp", r"tls", r"cdn"),
    "observability": (r"observability", r"telemetry", r"tracing", r"monitoring"),
    "open-source": (r"open[ -]source",),
    "privacy": (r"privacy", r"surveillance", r"tracking"),
    "programming": (
        r"programming languages?",
        r"python",
        r"rust",
        r"java",
        r"javascript",
        r"typescript",
        r"golang",
    ),
    "research": (r"research", r"papers?", r"benchmarks?"),
    "security": (
        r"security",
        r"vulnerabilit(?:y|ies)",
        r"exploits?",
        r"malware",
        r"ransomware",
        r"cves?",
    ),
    "web": (r"browsers?", r"webassembly", r"wasm", r"css", r"html", r"web platform"),
}

_PATTERNS = {
    tag: re.compile(r"(?<!\w)(?:" + "|".join(terms) + r")(?!\w)", re.IGNORECASE)
    for tag, terms in _TERMS.items()
}


def infer_tags(
    title: str,
    summary: str,
    default_tags: Sequence[str],
) -> List[str]:
    unknown = set(default_tags) - set(TAGS)
    if unknown:
        raise ValueError(f"unknown default tags: {', '.join(sorted(unknown))}")
    text = f"{title} {summary}"
    tags = set(default_tags)
    tags.update(tag for tag, pattern in _PATTERNS.items() if pattern.search(text))
    return sorted(tags)
