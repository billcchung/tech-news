from .models import Source


SOURCES = (
    Source("AWS Blog", "Cloud", "https://aws.amazon.com/blogs/aws/feed/", ("aws.amazon.com",)),
    Source(
        "Google Cloud Blog",
        "Cloud",
        "https://cloudblog.withgoogle.com/rss/",
        ("cloud.google.com", "cloudblog.withgoogle.com"),
    ),
    Source(
        "Azure Blog",
        "Cloud",
        "https://azure.microsoft.com/en-us/blog/feed/",
        ("azure.microsoft.com",),
    ),
    Source("Kubernetes Blog", "DevOps/SRE", "https://kubernetes.io/feed.xml", ("kubernetes.io",)),
    Source("CNCF", "DevOps/SRE", "https://www.cncf.io/feed/", ("cncf.io",)),
    Source(
        "HashiCorp Blog",
        "DevOps/SRE",
        "https://www.hashicorp.com/blog/feed.xml",
        ("hashicorp.com",),
    ),
    Source("DevOps.com", "DevOps/SRE", "https://devops.com/feed/", ("devops.com",)),
    Source("OpenAI News", "AI", "https://openai.com/news/rss.xml", ("openai.com",)),
    Source(
        "Hugging Face Blog",
        "AI",
        "https://huggingface.co/blog/feed.xml",
        ("huggingface.co",),
    ),
    Source(
        "Ars Technica",
        "Tech",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        ("arstechnica.com",),
    ),
    Source(
        "MIT Technology Review",
        "Tech",
        "https://www.technologyreview.com/feed/",
        ("technologyreview.com",),
    ),
    Source(
        "IEEE Spectrum",
        "Tech",
        "https://spectrum.ieee.org/feeds/feed.rss",
        ("spectrum.ieee.org",),
    ),
    Source("InfoQ", "Tech", "https://feed.infoq.com/", ("infoq.com",)),
)
