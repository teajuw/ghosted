"""Human-written text samples for the invisible character experiment.

20 diverse samples: academic, casual, creative, technical.
All confirmed human-written (authored for this project).
"""

SAMPLES = [
    # Academic
    {
        "id": "academic_1",
        "category": "academic",
        "text": (
            "The industrial revolution fundamentally altered the relationship between labor "
            "and capital in Western societies. Prior to mechanization, artisans maintained "
            "control over both the means of production and the pace of their work. The "
            "introduction of factory systems disrupted this arrangement, creating a new "
            "class of wage laborers dependent on machine operators for their livelihood."
        ),
    },
    {
        "id": "academic_2",
        "category": "academic",
        "text": (
            "Recent studies in cognitive psychology suggest that multitasking is largely a "
            "myth. When people believe they are performing two tasks simultaneously, they "
            "are actually switching rapidly between them. This switching carries a cognitive "
            "cost, measured as increased error rates and slower completion times across "
            "both tasks compared to sequential processing."
        ),
    },
    {
        "id": "academic_3",
        "category": "academic",
        "text": (
            "Climate change impacts on marine ecosystems extend beyond rising temperatures. "
            "Ocean acidification, caused by increased CO2 absorption, threatens calcifying "
            "organisms like corals and mollusks. Meanwhile, changes in ocean circulation "
            "patterns alter nutrient distribution, affecting phytoplankton productivity at "
            "the base of marine food webs."
        ),
    },
    {
        "id": "academic_4",
        "category": "academic",
        "text": (
            "The concept of linguistic relativity, often attributed to Sapir and Whorf, "
            "proposes that the structure of a language influences its speakers' worldview. "
            "While strong versions of this hypothesis have been largely abandoned, weaker "
            "forms persist in research showing that language affects categorization of "
            "colors, spatial reasoning, and temporal concepts."
        ),
    },
    {
        "id": "academic_5",
        "category": "academic",
        "text": (
            "Antibiotic resistance represents one of the most pressing challenges in modern "
            "medicine. Bacterial populations evolve resistance through natural selection when "
            "exposed to sub-lethal concentrations of antimicrobial agents. Horizontal gene "
            "transfer accelerates this process, allowing resistance genes to spread between "
            "unrelated bacterial species."
        ),
    },
    # Casual / conversational
    {
        "id": "casual_1",
        "category": "casual",
        "text": (
            "I finally tried that new coffee shop on 5th street and honestly it was kind "
            "of disappointing. The espresso was way too bitter and they charged eight bucks "
            "for a latte. My friend said the pastries are good but I didnt try any because "
            "I was already annoyed about the coffee. Might give it another shot though, "
            "everyone else seems to love it."
        ),
    },
    {
        "id": "casual_2",
        "category": "casual",
        "text": (
            "So my dog decided to eat an entire sock yesterday and we spent four hours at "
            "the emergency vet. Turns out he's fine, just needed to be monitored, but my "
            "wallet is significantly lighter. The vet said labs eat everything and I should "
            "be more careful. Yeah thanks doc, real helpful advice there."
        ),
    },
    {
        "id": "casual_3",
        "category": "casual",
        "text": (
            "Been trying to get into running but my knees are not having it. Started with "
            "couch to 5k and made it about two weeks before everything hurt. My neighbor "
            "runs marathons and makes it look easy. She told me to get better shoes so I "
            "spent $150 on some fancy ones and they honestly do help a little."
        ),
    },
    {
        "id": "casual_4",
        "category": "casual",
        "text": (
            "The meeting that could have been an email happened again today. Forty five "
            "minutes of my life I won't get back. Someone asked a question that was already "
            "answered in the doc that was sent out beforehand. I had my camera off and was "
            "doing laundry the whole time. Pretty sure half the team was too."
        ),
    },
    {
        "id": "casual_5",
        "category": "casual",
        "text": (
            "Tried to assemble IKEA furniture without the instructions because I thought "
            "it would be obvious. It was not obvious. Three hours later I had something "
            "that vaguely resembled a bookshelf but leaned slightly to the left. My "
            "roommate came home and fixed it in twenty minutes. I'm never doing that again."
        ),
    },
    # Creative writing
    {
        "id": "creative_1",
        "category": "creative",
        "text": (
            "The lighthouse keeper hadn't spoken to another person in forty-seven days. "
            "He marked each one on the wall beside his cot with a stubby pencil, the "
            "graphite wearing down like his patience. The supply boat was late again. "
            "He watched the horizon through salt-crusted glass, wondering if they'd "
            "forgotten about him entirely."
        ),
    },
    {
        "id": "creative_2",
        "category": "creative",
        "text": (
            "Rain collected in the gutters and ran in thin rivers along the curb. Maria "
            "stepped over them carefully, her shoes already ruined from yesterday. The "
            "umbrella she'd borrowed from the office had a broken spoke that poked her "
            "shoulder every few steps. Three more blocks. She counted them like prayers."
        ),
    },
    {
        "id": "creative_3",
        "category": "creative",
        "text": (
            "The garden had been his grandmother's pride. Now the roses grew wild, thorns "
            "catching on his jeans as he pushed through to the back fence. Someone had "
            "left a pair of gardening gloves on the bench, stiff with age and weather. "
            "He picked them up and turned them over, half expecting to find her handwriting "
            "on a tag inside."
        ),
    },
    {
        "id": "creative_4",
        "category": "creative",
        "text": (
            "The diner closed at midnight but the neon sign stayed on until two. Truck "
            "drivers pulled into the lot, saw the dark windows, and pulled back out. "
            "Nobody complained. The sign was company enough on a stretch of highway where "
            "the next town was forty miles of nothing."
        ),
    },
    {
        "id": "creative_5",
        "category": "creative",
        "text": (
            "She found the letter wedged between pages 114 and 115 of a library book "
            "about Arctic exploration. The handwriting was small and precise, blue ink on "
            "yellowed paper. Dear someone. She read it twice, then three times, then put "
            "it back exactly where she found it. Some things weren't meant to be kept."
        ),
    },
    # Technical
    {
        "id": "technical_1",
        "category": "technical",
        "text": (
            "The database migration failed because the foreign key constraint on the "
            "orders table referenced a column that had been renamed in the previous "
            "release. Rolling back required dropping the constraint first, then renaming "
            "the column back, then reapplying the migration with the correct reference. "
            "We added a pre-migration check to prevent this from happening again."
        ),
    },
    {
        "id": "technical_2",
        "category": "technical",
        "text": (
            "Memory usage spiked to 94% during the load test because the connection pool "
            "wasn't releasing idle connections. The default timeout was set to 30 minutes "
            "which made no sense for a service handling short-lived requests. Dropping it "
            "to 60 seconds and adding a max pool size of 20 brought memory usage down to "
            "a stable 45% under the same load."
        ),
    },
    {
        "id": "technical_3",
        "category": "technical",
        "text": (
            "The API returns a 429 status code when the rate limit is exceeded but the "
            "retry-after header isn't being set correctly. Clients that respect the header "
            "are retrying immediately instead of waiting, which makes the problem worse. "
            "The fix is straightforward: calculate the reset time from the token bucket "
            "state and include it in the response headers."
        ),
    },
    {
        "id": "technical_4",
        "category": "technical",
        "text": (
            "We switched from REST to gRPC for the internal service communication and "
            "saw a 40% reduction in p99 latency. The binary serialization eliminates "
            "the JSON parsing overhead that was adding 3-5ms per request. The tradeoff "
            "is debuggability, since you can't just curl the endpoints anymore, but for "
            "internal services that tradeoff is worth it."
        ),
    },
    {
        "id": "technical_5",
        "category": "technical",
        "text": (
            "The CI pipeline takes 22 minutes to run because the integration tests spin "
            "up a full Postgres instance for each test class. Sharing a single database "
            "with transaction rollbacks between tests would cut that to about 8 minutes "
            "but requires refactoring the test fixtures. We're planning to do that next "
            "sprint since the slow pipeline is blocking the team."
        ),
    },
]
