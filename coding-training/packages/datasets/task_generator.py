"""Curated task builder and dataset generator for WO-02."""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.contracts import Split


@dataclass
class RawTaskDefinition:
    """Internal blueprint for generating a verified task."""
    task_id: str
    entry_point: str
    signature: str
    docstring: str
    difficulty: str
    family_id: str
    split: Split
    reference_solution: str
    test_cases: list[dict[str, object]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


def build_raw_tasks() -> list[RawTaskDefinition]:
    """Builds a curated catalog of 105 Python tasks across 15 distinct families."""
    tasks: list[RawTaskDefinition] = []

    # =========================================================================
    # FAMILY 1: string_transforms (TRAIN) - 7 tasks
    # =========================================================================
    tasks.append(RawTaskDefinition(
        task_id="py-str-001",
        entry_point="reverse_string",
        signature="def reverse_string(s: str) -> str:",
        docstring="Return the reverse of string s.\n\n>>> reverse_string('hello')\n'olleh'",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution="def reverse_string(s: str) -> str:\n    return s[::-1]\n",
        test_cases=[
            {"inputs": [""], "expected": ""},
            {"inputs": ["a"], "expected": "a"},
            {"inputs": ["ab"], "expected": "ba"},
            {"inputs": ["hello"], "expected": "olleh"},
            {"inputs": ["racecar"], "expected": "racecar"},
            {"inputs": ["12345"], "expected": "54321"},
            {"inputs": ["  spaces  "], "expected": "  secaps  "},
            {"inputs": ["!@#$%^&*()"], "expected": ")(*&^%$#@!"},
            {"inputs": ["Python Programming"], "expected": "gnimmargorP nohtyP"},
            {"inputs": ["UPPER and lower"], "expected": "rewol dna REPPU"},
            {"inputs": ["a" * 100], "expected": "a" * 100},
            {"inputs": ["newline\ntest"], "expected": "tset\nenilwen"},
            {"inputs": ["tab\ttest"], "expected": "tset\tbat"},
            {"inputs": ["emoji 🎉 test"], "expected": "tset 🎉 ijome"},
            {"inputs": ["palindrome"], "expected": "emordnilap"},
            {"inputs": ["abcdefghijklmnopqrstuvwxyz"], "expected": "zyxwvutsrqponmlkjihgfedcba"},
            {"inputs": ["0"], "expected": "0"},
            {"inputs": ["01"], "expected": "10"},
            {"inputs": ["mixed 1234 symbols #!?"], "expected": "?!# slobmys 4321 dexim"},
            {"inputs": ["repeat " * 5], "expected": ("repeat " * 5)[::-1]},
        ],
        tags=["strings", "basic"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-002",
        entry_point="count_vowels",
        signature="def count_vowels(s: str) -> int:",
        docstring="Count the number of vowels (a, e, i, o, u, case-insensitive) in string s.\n\n>>> count_vowels('Hello World')\n3",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution="def count_vowels(s: str) -> int:\n    vowels = set('aeiouAEIOU')\n    return sum(1 for c in s if c in vowels)\n",
        test_cases=[
            {"inputs": [""], "expected": 0},
            {"inputs": ["bcdfghjklmnpqrstvwxyz"], "expected": 0},
            {"inputs": ["aeiou"], "expected": 5},
            {"inputs": ["AEIOU"], "expected": 5},
            {"inputs": ["Hello World"], "expected": 3},
            {"inputs": ["Python"], "expected": 1},
            {"inputs": ["1234567890"], "expected": 0},
            {"inputs": ["!@#$%^&*()"], "expected": 0},
            {"inputs": ["The quick brown fox jumps over the lazy dog"], "expected": 11},
            {"inputs": ["A"], "expected": 1},
            {"inputs": ["b"], "expected": 0},
            {"inputs": ["o"], "expected": 1},
            {"inputs": ["rhythm"], "expected": 0},
            {"inputs": ["syzygy"], "expected": 0},
            {"inputs": ["cwm"], "expected": 0},
            {"inputs": ["Queueing"], "expected": 5},
            {"inputs": ["Sequioa"], "expected": 5},
            {"inputs": ["AaEeIiOoUu"], "expected": 10},
            {"inputs": ["MixedCaseStringWithVowels"], "expected": 8},
            {"inputs": ["a" * 50 + "b" * 50], "expected": 50},
        ],
        tags=["strings", "counting"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-003",
        entry_point="is_palindrome",
        signature="def is_palindrome(s: str) -> bool:",
        docstring="Check if string s is a palindrome, ignoring case and non-alphanumeric characters.\n\n>>> is_palindrome('A man, a plan, a canal: Panama')\nTrue",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def is_palindrome(s: str) -> bool:\n"
            "    cleaned = [c.lower() for c in s if c.isalnum()]\n"
            "    return cleaned == cleaned[::-1]\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": True},
            {"inputs": ["a"], "expected": True},
            {"inputs": ["ab"], "expected": False},
            {"inputs": ["aa"], "expected": True},
            {"inputs": ["racecar"], "expected": True},
            {"inputs": ["RaceCar"], "expected": True},
            {"inputs": ["A man, a plan, a canal: Panama"], "expected": True},
            {"inputs": ["race a car"], "expected": False},
            {"inputs": ["Was it a car or a cat I saw?"], "expected": True},
            {"inputs": ["No 'x' in Nixon"], "expected": True},
            {"inputs": ["12321"], "expected": True},
            {"inputs": ["123321"], "expected": True},
            {"inputs": ["123421"], "expected": False},
            {"inputs": [".,:;!"], "expected": True},
            {"inputs": ["0P"], "expected": False},
            {"inputs": ["Madam, in Eden, I'm Adam"], "expected": True},
            {"inputs": ["Never odd or even"], "expected": True},
            {"inputs": ["Doc, note: I dissent. A fast never prevents a fatness. I diet on cod."], "expected": True},
            {"inputs": ["hello world"], "expected": False},
            {"inputs": ["a" * 100], "expected": True},
        ],
        tags=["strings", "palindrome"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-004",
        entry_point="to_snake_case",
        signature="def to_snake_case(s: str) -> str:",
        docstring="Convert camelCase or PascalCase string to snake_case.\n\n>>> to_snake_case('camelCaseString')\n'camel_case_string'",
        difficulty="medium",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def to_snake_case(s: str) -> str:\n"
            "    import re\n"
            "    s = re.sub('(.)([A-Z][a-z]+)', r'\\1_\\2', s)\n"
            "    return re.sub('([a-z0-9])([A-Z])', r'\\1_\\2', s).lower()\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": ""},
            {"inputs": ["hello"], "expected": "hello"},
            {"inputs": ["camelCase"], "expected": "camel_case"},
            {"inputs": ["PascalCase"], "expected": "pascal_case"},
            {"inputs": ["camelCaseString"], "expected": "camel_case_string"},
            {"inputs": ["HTMLParser"], "expected": "html_parser"},
            {"inputs": ["JSONToXML"], "expected": "json_to_xml"},
            {"inputs": ["myVar123"], "expected": "my_var123"},
            {"inputs": ["already_snake_case"], "expected": "already_snake_case"},
            {"inputs": ["A"], "expected": "a"},
            {"inputs": ["AB"], "expected": "ab"},
            {"inputs": ["ABCDef"], "expected": "abc_def"},
            {"inputs": ["getHTTPResponseCode"], "expected": "get_http_response_code"},
            {"inputs": ["simpleTest"], "expected": "simple_test"},
            {"inputs": ["longCamelCaseIdentifierWithManyWords"], "expected": "long_camel_case_identifier_with_many_words"},
            {"inputs": ["fooBarBaz"], "expected": "foo_bar_baz"},
            {"inputs": ["x"], "expected": "x"},
            {"inputs": ["xy"], "expected": "xy"},
            {"inputs": ["xY"], "expected": "x_y"},
            {"inputs": ["XY"], "expected": "xy"},
        ],
        tags=["strings", "case-conversion"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-005",
        entry_point="run_length_encode",
        signature="def run_length_encode(s: str) -> str:",
        docstring="Encode a string using basic run-length encoding (e.g. 'aaabbc' -> 'a3b2c1').\n\n>>> run_length_encode('aaabbc')\n'a3b2c1'",
        difficulty="medium",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def run_length_encode(s: str) -> str:\n"
            "    if not s:\n"
            "        return ''\n"
            "    res = []\n"
            "    curr = s[0]\n"
            "    count = 1\n"
            "    for c in s[1:]:\n"
            "        if c == curr:\n"
            "            count += 1\n"
            "        else:\n"
            "            res.append(f'{curr}{count}')\n"
            "            curr = c\n"
            "            count = 1\n"
            "    res.append(f'{curr}{count}')\n"
            "    return ''.join(res)\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": ""},
            {"inputs": ["a"], "expected": "a1"},
            {"inputs": ["aa"], "expected": "a2"},
            {"inputs": ["aaa"], "expected": "a3"},
            {"inputs": ["ab"], "expected": "a1b1"},
            {"inputs": ["aaabbc"], "expected": "a3b2c1"},
            {"inputs": ["aabbaa"], "expected": "a2b2a2"},
            {"inputs": ["111223"], "expected": "132231"},
            {"inputs": ["abcdef"], "expected": "a1b1c1d1e1f1"},
            {"inputs": ["WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWBWWWWWWWWWWWWWW"], "expected": "W12B1W12B3W24B1W14"},
            {"inputs": ["   "], "expected": " 3"},
            {"inputs": ["--++=="], "expected": "-2+2=2"},
            {"inputs": ["z" * 10], "expected": "z10"},
            {"inputs": ["x" * 25], "expected": "x25"},
            {"inputs": ["a" * 100], "expected": "a100"},
            {"inputs": ["aba"], "expected": "a1b1a1"},
            {"inputs": ["abacaba"], "expected": "a1b1a1c1a1b1a1"},
            {"inputs": ["0"], "expected": "01"},
            {"inputs": ["00"], "expected": "02"},
            {"inputs": ["010"], "expected": "011101"},
        ],
        tags=["strings", "encoding", "compression"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-006",
        entry_point="truncate_words",
        signature="def truncate_words(s: str, n: int) -> str:",
        docstring="Truncate string s to at most n words, appending '...' if truncated.\n\n>>> truncate_words('The quick brown fox', 2)\n'The quick...'",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def truncate_words(s: str, n: int) -> str:\n"
            "    words = s.split()\n"
            "    if len(words) <= n:\n"
            "        return ' '.join(words)\n"
            "    return ' '.join(words[:n]) + '...'\n"
        ),
        test_cases=[
            {"inputs": ["", 5], "expected": ""},
            {"inputs": ["hello", 1], "expected": "hello"},
            {"inputs": ["hello world", 1], "expected": "hello..."},
            {"inputs": ["The quick brown fox", 2], "expected": "The quick..."},
            {"inputs": ["The quick brown fox", 4], "expected": "The quick brown fox"},
            {"inputs": ["The quick brown fox", 10], "expected": "The quick brown fox"},
            {"inputs": ["one two three four five", 3], "expected": "one two three..."},
            {"inputs": ["single", 0], "expected": "..."},
            {"inputs": ["a b c d e f", 1], "expected": "a..."},
            {"inputs": ["a b c d e f", 5], "expected": "a b c d e..."},
            {"inputs": ["   multiple    spaces   inside   ", 2], "expected": "multiple spaces..."},
            {"inputs": ["word", 1], "expected": "word"},
            {"inputs": ["word", 0], "expected": "..."},
            {"inputs": ["first second", 2], "expected": "first second"},
            {"inputs": ["first second", 1], "expected": "first..."},
            {"inputs": ["alpha beta gamma delta", 2], "expected": "alpha beta..."},
            {"inputs": ["alpha beta gamma delta", 3], "expected": "alpha beta gamma..."},
            {"inputs": ["alpha beta gamma delta", 4], "expected": "alpha beta gamma delta"},
            {"inputs": ["1 2 3 4 5 6 7 8 9 10", 5], "expected": "1 2 3 4 5..."},
            {"inputs": ["same same same", 2], "expected": "same same..."},
        ],
        tags=["strings", "formatting"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-007",
        entry_point="are_anagrams",
        signature="def are_anagrams(s1: str, s2: str) -> bool:",
        docstring="Check if s1 and s2 are anagrams, case-insensitive, ignoring non-alphanumeric chars.\n\n>>> are_anagrams('listen', 'silent')\nTrue",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def are_anagrams(s1: str, s2: str) -> bool:\n"
            "    from collections import Counter\n"
            "    c1 = Counter(c.lower() for c in s1 if c.isalnum())\n"
            "    c2 = Counter(c.lower() for c in s2 if c.isalnum())\n"
            "    return c1 == c2\n"
        ),
        test_cases=[
            {"inputs": ["", ""], "expected": True},
            {"inputs": ["a", "a"], "expected": True},
            {"inputs": ["a", "b"], "expected": False},
            {"inputs": ["listen", "silent"], "expected": True},
            {"inputs": ["Listen", "Silent"], "expected": True},
            {"inputs": ["evil", "vile"], "expected": True},
            {"inputs": ["fluster", "restful"], "expected": True},
            {"inputs": ["dormitory", "dirty room"], "expected": True},
            {"inputs": ["conversation", "voices rant on"], "expected": True},
            {"inputs": ["apple", "pale"], "expected": False},
            {"inputs": ["hello", "billion"], "expected": False},
            {"inputs": ["123", "321"], "expected": True},
            {"inputs": ["1234", "123"], "expected": False},
            {"inputs": ["a b c", "cba"], "expected": True},
            {"inputs": ["A gentleman", "Elegant man"], "expected": True},
            {"inputs": ["Astronomer", "Moon starer"], "expected": True},
            {"inputs": ["The eyes", "They see"], "expected": True},
            {"inputs": ["abc", "abcd"], "expected": False},
            {"inputs": ["rat", "car"], "expected": False},
            {"inputs": ["!", "?"], "expected": True},
        ],
        tags=["strings", "anagrams"],
    ))

    # =========================================================================
    # FAMILY 2: math_primes_and_factors (TRAIN) - 7 tasks
    # =========================================================================
    tasks.append(RawTaskDefinition(
        task_id="py-math-001",
        entry_point="is_prime",
        signature="def is_prime(n: int) -> bool:",
        docstring="Check if integer n is a prime number.\n\n>>> is_prime(7)\nTrue",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def is_prime(n: int) -> bool:\n"
            "    if n <= 1:\n"
            "        return False\n"
            "    if n <= 3:\n"
            "        return True\n"
            "    if n % 2 == 0 or n % 3 == 0:\n"
            "        return False\n"
            "    i = 5\n"
            "    while i * i <= n:\n"
            "        if n % i == 0 or n % (i + 2) == 0:\n"
            "            return False\n"
            "        i += 6\n"
            "    return True\n"
        ),
        test_cases=[
            {"inputs": [-5], "expected": False},
            {"inputs": [0], "expected": False},
            {"inputs": [1], "expected": False},
            {"inputs": [2], "expected": True},
            {"inputs": [3], "expected": True},
            {"inputs": [4], "expected": False},
            {"inputs": [5], "expected": True},
            {"inputs": [6], "expected": False},
            {"inputs": [7], "expected": True},
            {"inputs": [8], "expected": False},
            {"inputs": [9], "expected": False},
            {"inputs": [11], "expected": True},
            {"inputs": [13], "expected": True},
            {"inputs": [17], "expected": True},
            {"inputs": [19], "expected": True},
            {"inputs": [23], "expected": True},
            {"inputs": [25], "expected": False},
            {"inputs": [29], "expected": True},
            {"inputs": [97], "expected": True},
            {"inputs": [100], "expected": False},
        ],
        tags=["math", "primes"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-002",
        entry_point="gcd",
        signature="def gcd(a: int, b: int) -> int:",
        docstring="Return the greatest common divisor of non-negative integers a and b.\n\n>>> gcd(48, 18)\n6",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def gcd(a: int, b: int) -> int:\n"
            "    import math\n"
            "    return math.gcd(abs(a), abs(b))\n"
        ),
        test_cases=[
            {"inputs": [0, 0], "expected": 0},
            {"inputs": [0, 5], "expected": 5},
            {"inputs": [5, 0], "expected": 5},
            {"inputs": [1, 1], "expected": 1},
            {"inputs": [1, 100], "expected": 1},
            {"inputs": [12, 18], "expected": 6},
            {"inputs": [48, 18], "expected": 6},
            {"inputs": [101, 103], "expected": 1},
            {"inputs": [54, 24], "expected": 6},
            {"inputs": [100, 10], "expected": 10},
            {"inputs": [81, 27], "expected": 27},
            {"inputs": [17, 34], "expected": 17},
            {"inputs": [25, 25], "expected": 25},
            {"inputs": [1000, 500], "expected": 500},
            {"inputs": [7, 13], "expected": 1},
            {"inputs": [42, 56], "expected": 14},
            {"inputs": [14, 28], "expected": 14},
            {"inputs": [35, 49], "expected": 7},
            {"inputs": [60, 90], "expected": 30},
            {"inputs": [270, 192], "expected": 6},
        ],
        tags=["math", "gcd"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-003",
        entry_point="prime_factors",
        signature="def prime_factors(n: int) -> list[int]:",
        docstring="Return the prime factors of integer n >= 2 in ascending order with multiplicity.\n\n>>> prime_factors(12)\n[2, 2, 3]",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def prime_factors(n: int) -> list[int]:\n"
            "    factors = []\n"
            "    d = 2\n"
            "    while d * d <= n:\n"
            "        while n % d == 0:\n"
            "            factors.append(d)\n"
            "            n //= d\n"
            "        d += 1\n"
            "    if n > 1:\n"
            "        factors.append(n)\n"
            "    return factors\n"
        ),
        test_cases=[
            {"inputs": [2], "expected": [2]},
            {"inputs": [3], "expected": [3]},
            {"inputs": [4], "expected": [2, 2]},
            {"inputs": [6], "expected": [2, 3]},
            {"inputs": [8], "expected": [2, 2, 2]},
            {"inputs": [9], "expected": [3, 3]},
            {"inputs": [12], "expected": [2, 2, 3]},
            {"inputs": [15], "expected": [3, 5]},
            {"inputs": [16], "expected": [2, 2, 2, 2]},
            {"inputs": [17], "expected": [17]},
            {"inputs": [20], "expected": [2, 2, 5]},
            {"inputs": [24], "expected": [2, 2, 2, 3]},
            {"inputs": [30], "expected": [2, 3, 5]},
            {"inputs": [49], "expected": [7, 7]},
            {"inputs": [60], "expected": [2, 2, 3, 5]},
            {"inputs": [84], "expected": [2, 2, 3, 7]},
            {"inputs": [100], "expected": [2, 2, 5, 5]},
            {"inputs": [101], "expected": [101]},
            {"inputs": [128], "expected": [2, 2, 2, 2, 2, 2, 2]},
            {"inputs": [315], "expected": [3, 3, 5, 7]},
        ],
        tags=["math", "prime-factors"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-004",
        entry_point="lcm",
        signature="def lcm(a: int, b: int) -> int:",
        docstring="Return the least common multiple of positive integers a and b.\n\n>>> lcm(4, 6)\n12",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def lcm(a: int, b: int) -> int:\n"
            "    import math\n"
            "    return (a * b) // math.gcd(a, b) if a and b else 0\n"
        ),
        test_cases=[
            {"inputs": [1, 1], "expected": 1},
            {"inputs": [1, 5], "expected": 5},
            {"inputs": [4, 6], "expected": 12},
            {"inputs": [2, 3], "expected": 6},
            {"inputs": [5, 7], "expected": 35},
            {"inputs": [6, 8], "expected": 24},
            {"inputs": [10, 15], "expected": 30},
            {"inputs": [12, 18], "expected": 36},
            {"inputs": [7, 14], "expected": 14},
            {"inputs": [9, 12], "expected": 36},
            {"inputs": [15, 20], "expected": 60},
            {"inputs": [21, 6], "expected": 42},
            {"inputs": [8, 9], "expected": 72},
            {"inputs": [16, 24], "expected": 48},
            {"inputs": [25, 30], "expected": 150},
            {"inputs": [13, 17], "expected": 221},
            {"inputs": [100, 25], "expected": 100},
            {"inputs": [11, 13], "expected": 143},
            {"inputs": [14, 21], "expected": 42},
            {"inputs": [18, 27], "expected": 54},
        ],
        tags=["math", "lcm"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-005",
        entry_point="collatz_length",
        signature="def collatz_length(n: int) -> int:",
        docstring="Return the number of steps to reach 1 in the Collatz sequence starting at n.\n\n>>> collatz_length(6)\n8",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def collatz_length(n: int) -> int:\n"
            "    steps = 0\n"
            "    while n > 1:\n"
            "        if n % 2 == 0:\n"
            "            n //= 2\n"
            "        else:\n"
            "            n = 3 * n + 1\n"
            "        steps += 1\n"
            "    return steps\n"
        ),
        test_cases=[
            {"inputs": [1], "expected": 0},
            {"inputs": [2], "expected": 1},
            {"inputs": [3], "expected": 7},
            {"inputs": [4], "expected": 2},
            {"inputs": [5], "expected": 5},
            {"inputs": [6], "expected": 8},
            {"inputs": [7], "expected": 16},
            {"inputs": [8], "expected": 3},
            {"inputs": [9], "expected": 19},
            {"inputs": [10], "expected": 6},
            {"inputs": [11], "expected": 14},
            {"inputs": [12], "expected": 9},
            {"inputs": [13], "expected": 9},
            {"inputs": [14], "expected": 17},
            {"inputs": [15], "expected": 17},
            {"inputs": [16], "expected": 4},
            {"inputs": [17], "expected": 12},
            {"inputs": [18], "expected": 20},
            {"inputs": [19], "expected": 20},
            {"inputs": [27], "expected": 111},
        ],
        tags=["math", "sequence"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-006",
        entry_point="is_power_of_two",
        signature="def is_power_of_two(n: int) -> bool:",
        docstring="Check if integer n is a power of two (i.e. n == 2^k for integer k >= 0).\n\n>>> is_power_of_two(16)\nTrue",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def is_power_of_two(n: int) -> bool:\n"
            "    return n > 0 and (n & (n - 1)) == 0\n"
        ),
        test_cases=[
            {"inputs": [-2], "expected": False},
            {"inputs": [-1], "expected": False},
            {"inputs": [0], "expected": False},
            {"inputs": [1], "expected": True},
            {"inputs": [2], "expected": True},
            {"inputs": [3], "expected": False},
            {"inputs": [4], "expected": True},
            {"inputs": [5], "expected": False},
            {"inputs": [6], "expected": False},
            {"inputs": [8], "expected": True},
            {"inputs": [10], "expected": False},
            {"inputs": [16], "expected": True},
            {"inputs": [24], "expected": False},
            {"inputs": [32], "expected": True},
            {"inputs": [64], "expected": True},
            {"inputs": [100], "expected": False},
            {"inputs": [128], "expected": True},
            {"inputs": [256], "expected": True},
            {"inputs": [512], "expected": True},
            {"inputs": [1024], "expected": True},
        ],
        tags=["math", "bitwise"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-007",
        entry_point="sum_of_digits",
        signature="def sum_of_digits(n: int) -> int:",
        docstring="Return the sum of digits of non-negative integer n.\n\n>>> sum_of_digits(12345)\n15",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def sum_of_digits(n: int) -> int:\n"
            "    return sum(int(d) for d in str(abs(n)))\n"
        ),
        test_cases=[
            {"inputs": [0], "expected": 0},
            {"inputs": [5], "expected": 5},
            {"inputs": [10], "expected": 1},
            {"inputs": [12], "expected": 3},
            {"inputs": [99], "expected": 18},
            {"inputs": [123], "expected": 6},
            {"inputs": [12345], "expected": 15},
            {"inputs": [1000], "expected": 1},
            {"inputs": [9999], "expected": 36},
            {"inputs": [505], "expected": 10},
            {"inputs": [1111111111], "expected": 10},
            {"inputs": [789], "expected": 24},
            {"inputs": [456], "expected": 15},
            {"inputs": [1020304], "expected": 10},
            {"inputs": [9000000009], "expected": 18},
            {"inputs": [123456789], "expected": 45},
            {"inputs": [222], "expected": 6},
            {"inputs": [3333], "expected": 12},
            {"inputs": [88], "expected": 16},
            {"inputs": [1000000], "expected": 1},
        ],
        tags=["math", "digits"],
    ))

    # =========================================================================
    # FAMILY 3: array_filtering_transforms (TRAIN) - 7 tasks
    # =========================================================================
    tasks.append(RawTaskDefinition(
        task_id="py-arr-001",
        entry_point="filter_evens",
        signature="def filter_evens(nums: list[int]) -> list[int]:",
        docstring="Return only the even integers from list nums in original order.\n\n>>> filter_evens([1, 2, 3, 4, 5, 6])\n[2, 4, 6]",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution="def filter_evens(nums: list[int]) -> list[int]:\n    return [x for x in nums if x % 2 == 0]\n",
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[1]], "expected": []},
            {"inputs": [[2]], "expected": [2]},
            {"inputs": [[1, 2, 3, 4, 5, 6]], "expected": [2, 4, 6]},
            {"inputs": [[1, 3, 5, 7]], "expected": []},
            {"inputs": [[2, 4, 6, 8]], "expected": [2, 4, 6, 8]},
            {"inputs": [[0]], "expected": [0]},
            {"inputs": [[-2, -1, 0, 1, 2]], "expected": [-2, 0, 2]},
            {"inputs": [[-4, -2, -6]], "expected": [-4, -2, -6]},
            {"inputs": [[-3, -5, -7]], "expected": []},
            {"inputs": [[100, 101, 102]], "expected": [100, 102]},
            {"inputs": [[10, 20, 30]], "expected": [10, 20, 30]},
            {"inputs": [[7, 7, 7]], "expected": []},
            {"inputs": [[8, 8, 8]], "expected": [8, 8, 8]},
            {"inputs": [[1, 2] * 10], "expected": [2] * 10},
            {"inputs": [list(range(10))], "expected": [0, 2, 4, 6, 8]},
            {"inputs": [list(range(1, 10))], "expected": [2, 4, 6, 8]},
            {"inputs": [[999998, 999999]], "expected": [999998]},
            {"inputs": [[0, 0, 0]], "expected": [0, 0, 0]},
            {"inputs": [[-10, 10, -20, 20]], "expected": [-10, 10, -20, 20]},
        ],
        tags=["arrays", "filtering"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-002",
        entry_point="remove_duplicates",
        signature="def remove_duplicates(items: list) -> list:",
        docstring="Remove duplicate elements preserving first occurrence order.\n\n>>> remove_duplicates([1, 2, 2, 3, 1])\n[1, 2, 3]",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def remove_duplicates(items: list) -> list:\n"
            "    seen = set()\n"
            "    res = []\n"
            "    for x in items:\n"
            "        if x not in seen:\n"
            "            seen.add(x)\n"
            "            res.append(x)\n"
            "    return res\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[1]], "expected": [1]},
            {"inputs": [[1, 1, 1]], "expected": [1]},
            {"inputs": [[1, 2, 2, 3, 1]], "expected": [1, 2, 3]},
            {"inputs": [["a", "b", "a", "c"]], "expected": ["a", "b", "c"]},
            {"inputs": [[True, False, True]], "expected": [True, False]},
            {"inputs": [[1, 2, 3, 4, 5]], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[5, 4, 3, 2, 1]], "expected": [5, 4, 3, 2, 1]},
            {"inputs": [[3, 3, 3, 2, 2, 1]], "expected": [3, 2, 1]},
            {"inputs": [["x"] * 20], "expected": ["x"]},
            {"inputs": [[0, -1, 0, -1, 2]], "expected": [0, -1, 2]},
            {"inputs": [["apple", "banana", "apple"]], "expected": ["apple", "banana"]},
            {"inputs": [[10, 20, 10, 30, 20]], "expected": [10, 20, 30]},
            {"inputs": [[1, 2, 3, 1, 2, 3]], "expected": [1, 2, 3]},
            {"inputs": [[42]], "expected": [42]},
            {"inputs": [[1, 0, -1, 0, 1]], "expected": [1, 0, -1]},
            {"inputs": [["a", "A", "a"]], "expected": ["a", "A"]},
            {"inputs": [[None, None, 1]], "expected": [None, 1]},
            {"inputs": [[100, 200, 300, 200, 100]], "expected": [100, 200, 300]},
            {"inputs": [[9, 8, 7, 8, 9, 7]], "expected": [9, 8, 7]},
        ],
        tags=["arrays", "dedup"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-003",
        entry_point="chunk_list",
        signature="def chunk_list(items: list, size: int) -> list[list]:",
        docstring="Split list items into sublists of length at most size.\n\n>>> chunk_list([1, 2, 3, 4, 5], 2)\n[[1, 2], [3, 4], [5]]",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def chunk_list(items: list, size: int) -> list[list]:\n"
            "    if size <= 0:\n"
            "        return []\n"
            "    return [items[i:i + size] for i in range(0, len(items), size)]\n"
        ),
        test_cases=[
            {"inputs": [[], 2], "expected": []},
            {"inputs": [[1, 2, 3], 1], "expected": [[1], [2], [3]]},
            {"inputs": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]},
            {"inputs": [[1, 2, 3, 4], 2], "expected": [[1, 2], [3, 4]]},
            {"inputs": [[1, 2, 3], 5], "expected": [[1, 2, 3]]},
            {"inputs": [["a", "b", "c", "d"], 3], "expected": [["a", "b", "c"], ["d"]]},
            {"inputs": [list(range(6)), 3], "expected": [[0, 1, 2], [3, 4, 5]]},
            {"inputs": [list(range(7)), 3], "expected": [[0, 1, 2], [3, 4, 5], [6]]},
            {"inputs": [[1], 1], "expected": [[1]]},
            {"inputs": [[1], 10], "expected": [[1]]},
            {"inputs": [[1, 2, 3, 4, 5, 6, 7, 8], 4], "expected": [[1, 2, 3, 4], [5, 6, 7, 8]]},
            {"inputs": [[1, 2, 3, 4, 5, 6, 7, 8, 9], 4], "expected": [[1, 2, 3, 4], [5, 6, 7, 8], [9]]},
            {"inputs": [["x", "y"], 1], "expected": [["x"], ["y"]]},
            {"inputs": [[True, False], 2], "expected": [[True, False]]},
            {"inputs": [[10, 20, 30], 2], "expected": [[10, 20], [30]]},
            {"inputs": [list(range(10)), 5], "expected": [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]},
            {"inputs": [[1, 2, 3], 0], "expected": []},
            {"inputs": [[1, 2, 3], -1], "expected": []},
            {"inputs": [[9, 9, 9, 9], 2], "expected": [[9, 9], [9, 9]]},
            {"inputs": [[7] * 5, 3], "expected": [[7, 7, 7], [7, 7]]},
        ],
        tags=["arrays", "chunking"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-004",
        entry_point="flatten_list",
        signature="def flatten_list(nested: list) -> list:",
        docstring="Recursively flatten an arbitrarily nested list into a 1D list.\n\n>>> flatten_list([1, [2, [3, 4], 5]])\n[1, 2, 3, 4, 5]",
        difficulty="medium",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def flatten_list(nested: list) -> list:\n"
            "    res = []\n"
            "    for item in nested:\n"
            "        if isinstance(item, list):\n"
            "            res.extend(flatten_list(item))\n"
            "        else:\n"
            "            res.append(item)\n"
            "    return res\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[1, 2, 3]], "expected": [1, 2, 3]},
            {"inputs": [[[1, 2, 3]]], "expected": [1, 2, 3]},
            {"inputs": [[1, [2, 3]]], "expected": [1, 2, 3]},
            {"inputs": [[1, [2, [3, 4], 5]]], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[[[[1]]]]], "expected": [1]},
            {"inputs": [[[], [[]], []]], "expected": []},
            {"inputs": [["a", ["b", ["c"]]]], "expected": ["a", "b", "c"]},
            {"inputs": [[1, [], 2, [3, []], 4]], "expected": [1, 2, 3, 4]},
            {"inputs": [[1, 2, [3, [4, [5]]]]], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[[1], [2], [3]]], "expected": [1, 2, 3]},
            {"inputs": [[0, [0, [0]]]], "expected": [0, 0, 0]},
            {"inputs": [[-1, [-2, [-3]]]], "expected": [-1, -2, -3]},
            {"inputs": [[10, [20, 30], 40]], "expected": [10, 20, 30, 40]},
            {"inputs": [[[[1, 2]], [3, 4]]], "expected": [1, 2, 3, 4]},
            {"inputs": [["start", [], "end"]], "expected": ["start", "end"]},
            {"inputs": [[True, [False]]], "expected": [True, False]},
            {"inputs": [[1, [2, [3, [4, [5, [6]]]]]]], "expected": [1, 2, 3, 4, 5, 6]},
            {"inputs": [[100, 200, [300, 400]]], "expected": [100, 200, 300, 400]},
            {"inputs": [[[], 1, []]], "expected": [1]},
        ],
        tags=["arrays", "recursion"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-005",
        entry_point="two_sum",
        signature="def two_sum(nums: list[int], target: int) -> list[int]:",
        docstring="Return the 0-indexed indices of the two numbers in nums that add up to target.\n\n>>> two_sum([2, 7, 11, 15], 9)\n[0, 1]",
        difficulty="medium",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def two_sum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = {}\n"
            "    for i, num in enumerate(nums):\n"
            "        comp = target - num\n"
            "        if comp in seen:\n"
            "            return [seen[comp], i]\n"
            "        seen[num] = i\n"
            "    return []\n"
        ),
        test_cases=[
            {"inputs": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"inputs": [[3, 2, 4], 6], "expected": [1, 2]},
            {"inputs": [[3, 3], 6], "expected": [0, 1]},
            {"inputs": [[1, 5, 3, 7], 8], "expected": [1, 2]},
            {"inputs": [[-1, -2, -3, -4, -5], -8], "expected": [2, 4]},
            {"inputs": [[0, 4, 3, 0], 0], "expected": [0, 3]},
            {"inputs": [[-3, 4, 3, 90], 0], "expected": [0, 2]},
            {"inputs": [[1, 2, 3, 4, 5], 9], "expected": [3, 4]},
            {"inputs": [[10, 20, 30, 40], 50], "expected": [1, 2]},
            {"inputs": [[5, 25, 75], 100], "expected": [1, 2]},
            {"inputs": [[1, 3, 5, 7, 9], 16], "expected": [3, 4]},
            {"inputs": [[2, 4, 6, 8], 14], "expected": [2, 3]},
            {"inputs": [[1, 2], 3], "expected": [0, 1]},
            {"inputs": [[100, 200, 300], 400], "expected": [0, 2]},
            {"inputs": [[-5, 10, 15], 10], "expected": [0, 2]},
            {"inputs": [[8, 2, 1, 9], 11], "expected": [1, 3]},
            {"inputs": [[15, 7, 2, 8], 9], "expected": [1, 2]},
            {"inputs": [[5, 8, 3, 1], 9], "expected": [1, 3]},
            {"inputs": [[4, 6, 10, 1], 5], "expected": [0, 3]},
            {"inputs": [[1, 1, 1, 1], 2], "expected": [0, 1]},
        ],
        tags=["arrays", "two-sum", "hashmap"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-006",
        entry_point="find_missing_number",
        signature="def find_missing_number(nums: list[int]) -> int:",
        docstring="Given an array nums containing n distinct numbers in the range [0, n], return the only number missing from the range.\n\n>>> find_missing_number([3, 0, 1])\n2",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def find_missing_number(nums: list[int]) -> int:\n"
            "    n = len(nums)\n"
            "    expected = n * (n + 1) // 2\n"
            "    return expected - sum(nums)\n"
        ),
        test_cases=[
            {"inputs": [[0, 1]], "expected": 2},
            {"inputs": [[1, 2]], "expected": 0},
            {"inputs": [[0, 2]], "expected": 1},
            {"inputs": [[3, 0, 1]], "expected": 2},
            {"inputs": [[0, 1, 2, 3, 4, 5, 6, 7, 9]], "expected": 8},
            {"inputs": [[9, 6, 4, 2, 3, 5, 7, 0, 1]], "expected": 8},
            {"inputs": [[0]], "expected": 1},
            {"inputs": [[1]], "expected": 0},
            {"inputs": [[2, 0]], "expected": 1},
            {"inputs": [[0, 1, 3]], "expected": 2},
            {"inputs": [[1, 2, 3]], "expected": 0},
            {"inputs": [[0, 1, 2]], "expected": 3},
            {"inputs": [[4, 3, 2, 1]], "expected": 0},
            {"inputs": [[0, 4, 3, 2]], "expected": 1},
            {"inputs": [[0, 1, 4, 3]], "expected": 2},
            {"inputs": [[0, 1, 2, 4]], "expected": 3},
            {"inputs": [[0, 1, 2, 3]], "expected": 4},
            {"inputs": [list(range(100))], "expected": 100},
            {"inputs": [[10] + list(range(10))], "expected": 11},
            {"inputs": [[5, 4, 3, 1, 0]], "expected": 2},
        ],
        tags=["arrays", "math"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-007",
        entry_point="merge_sorted",
        signature="def merge_sorted(a: list[int], b: list[int]) -> list[int]:",
        docstring="Merge two sorted integer lists into a single sorted list.\n\n>>> merge_sorted([1, 3, 5], [2, 4, 6])\n[1, 2, 3, 4, 5, 6]",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def merge_sorted(a: list[int], b: list[int]) -> list[int]:\n"
            "    res = []\n"
            "    i = j = 0\n"
            "    while i < len(a) and j < len(b):\n"
            "        if a[i] <= b[j]:\n"
            "            res.append(a[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            res.append(b[j])\n"
            "            j += 1\n"
            "    res.extend(a[i:])\n"
            "    res.extend(b[j:])\n"
            "    return res\n"
        ),
        test_cases=[
            {"inputs": [[], []], "expected": []},
            {"inputs": [[1], []], "expected": [1]},
            {"inputs": [[], [2]], "expected": [2]},
            {"inputs": [[1], [2]], "expected": [1, 2]},
            {"inputs": [[2], [1]], "expected": [1, 2]},
            {"inputs": [[1, 3, 5], [2, 4, 6]], "expected": [1, 2, 3, 4, 5, 6]},
            {"inputs": [[1, 2, 3], [4, 5, 6]], "expected": [1, 2, 3, 4, 5, 6]},
            {"inputs": [[4, 5, 6], [1, 2, 3]], "expected": [1, 2, 3, 4, 5, 6]},
            {"inputs": [[1, 3], [2, 4, 6, 8]], "expected": [1, 2, 3, 4, 6, 8]},
            {"inputs": [[2, 2, 2], [2, 2]], "expected": [2, 2, 2, 2, 2]},
            {"inputs": [[-5, -3, 0], [-4, -2, 1]], "expected": [-5, -4, -3, -2, 0, 1]},
            {"inputs": [[0], [0]], "expected": [0, 0]},
            {"inputs": [[10, 20, 30], [5, 15, 25]], "expected": [5, 10, 15, 20, 25, 30]},
            {"inputs": [[1, 10], [2, 9]], "expected": [1, 2, 9, 10]},
            {"inputs": [[1, 2, 8], [3]], "expected": [1, 2, 3, 8]},
            {"inputs": [[100], [1, 2, 3]], "expected": [1, 2, 3, 100]},
            {"inputs": [[-10], [-5]], "expected": [-10, -5]},
            {"inputs": [[1, 5, 9], [2, 6, 10]], "expected": [1, 2, 5, 6, 9, 10]},
            {"inputs": [[3, 4, 5], [1, 2]], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[1, 2, 3, 4], [5]], "expected": [1, 2, 3, 4, 5]},
        ],
        tags=["arrays", "sorting", "merge"],
    ))

    # =========================================================================
    # FAMILY 4: matrix_grid_logic (VAL) - 5 tasks
    # =========================================================================
    tasks.append(RawTaskDefinition(
        task_id="py-mat-001",
        entry_point="transpose_matrix",
        signature="def transpose_matrix(matrix: list[list[int]]) -> list[list[int]]:",
        docstring="Return the transpose of a 2D integer matrix.\n\n>>> transpose_matrix([[1, 2], [3, 4]])\n[[1, 3], [2, 4]]",
        difficulty="medium",
        family_id="family_matrix_grid_logic",
        split=Split.VAL,
        reference_solution=(
            "def transpose_matrix(matrix: list[list[int]]) -> list[list[int]]:\n"
            "    if not matrix or not matrix[0]:\n"
            "        return []\n"
            "    return [list(row) for row in zip(*matrix)]\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[[]]], "expected": []},
            {"inputs": [[[1]]], "expected": [[1]]},
            {"inputs": [[[1, 2], [3, 4]]], "expected": [[1, 3], [2, 4]]},
            {"inputs": [[[1, 2, 3], [4, 5, 6]]], "expected": [[1, 4], [2, 5], [3, 6]]},
            {"inputs": [[[1, 4], [2, 5], [3, 6]]], "expected": [[1, 2, 3], [4, 5, 6]]},
            {"inputs": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [[1, 4, 7], [2, 5, 8], [3, 6, 9]]},
            {"inputs": [[[0, 0], [0, 0]]], "expected": [[0, 0], [0, 0]]},
            {"inputs": [[[-1, -2], [-3, -4]]], "expected": [[-1, -3], [-2, -4]]},
            {"inputs": [[[1, 2, 3, 4]]], "expected": [[1], [2], [3], [4]]},
            {"inputs": [[[1], [2], [3], [4]]], "expected": [[1, 2, 3, 4]]},
            {"inputs": [[[5, 10], [15, 20]]], "expected": [[5, 15], [10, 20]]},
            {"inputs": [[[2, 3], [5, 7]]], "expected": [[2, 5], [3, 7]]},
            {"inputs": [[[10, 20, 30]]], "expected": [[10], [20], [30]]},
            {"inputs": [[[1, 0, 0], [0, 1, 0], [0, 0, 1]]], "expected": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
            {"inputs": [[[7, 8], [9, 10], [11, 12]]], "expected": [[7, 9, 11], [8, 10, 12]]},
            {"inputs": [[[1, 2, 3, 4, 5]]], "expected": [[1], [2], [3], [4], [5]]},
            {"inputs": [[[1], [2], [3], [4], [5]]], "expected": [[1, 2, 3, 4, 5]]},
            {"inputs": [[[1, 1], [2, 2], [3, 3]]], "expected": [[1, 2, 3], [1, 2, 3]]},
            {"inputs": [[[42]]], "expected": [[42]]},
        ],
        tags=["matrix", "linear-algebra"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-mat-002",
        entry_point="diagonal_sum",
        signature="def diagonal_sum(mat: list[list[int]]) -> int:",
        docstring="Return the sum of elements on the primary and secondary diagonals of square matrix mat (no double-counting center).\n\n>>> diagonal_sum([[1, 2, 3], [4, 5, 6], [7, 8, 9]])\n25",
        difficulty="easy",
        family_id="family_matrix_grid_logic",
        split=Split.VAL,
        reference_solution=(
            "def diagonal_sum(mat: list[list[int]]) -> int:\n"
            "    n = len(mat)\n"
            "    total = 0\n"
            "    for i in range(n):\n"
            "        total += mat[i][i]\n"
            "        if i != n - 1 - i:\n"
            "            total += mat[i][n - 1 - i]\n"
            "    return total\n"
        ),
        test_cases=[
            {"inputs": [[[1]]], "expected": 1},
            {"inputs": [[[1, 2], [3, 4]]], "expected": 10},
            {"inputs": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": 25},
            {"inputs": [[[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]], "expected": 8},
            {"inputs": [[[5]]], "expected": 5},
            {"inputs": [[[0, 0], [0, 0]]], "expected": 0},
            {"inputs": [[[-1, -2], [-3, -4]]], "expected": -10},
            {"inputs": [[[2, 0, 0], [0, 2, 0], [0, 0, 2]]], "expected": 6},
            {"inputs": [[[1, 0, 1], [0, 1, 0], [1, 0, 1]]], "expected": 5},
            {"inputs": [[[10, 20], [30, 40]]], "expected": 100},
            {"inputs": [[[1, 2, 3], [1, 2, 3], [1, 2, 3]]], "expected": 10},
            {"inputs": [[[3, 3], [3, 3]]], "expected": 12},
            {"inputs": [[[0, 1, 0], [1, 0, 1], [0, 1, 0]]], "expected": 0},
            {"inputs": [[[4, 0, 4], [0, 4, 0], [4, 0, 4]]], "expected": 20},
            {"inputs": [[[2, 1], [1, 2]]], "expected": 6},
            {"inputs": [[[7, 8, 9], [4, 5, 6], [1, 2, 3]]], "expected": 25},
            {"inputs": [[[-5, 5], [5, -5]]], "expected": 0},
            {"inputs": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]], "expected": 68},
            {"inputs": [[[100]]], "expected": 100},
            {"inputs": [[[2, 2, 2], [2, 2, 2], [2, 2, 2]]], "expected": 10},
        ],
        tags=["matrix", "diagonal"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-mat-003",
        entry_point="rotate_matrix_90",
        signature="def rotate_matrix_90(mat: list[list[int]]) -> list[list[int]]:",
        docstring="Rotate square matrix mat 90 degrees clockwise in-place or return new matrix.\n\n>>> rotate_matrix_90([[1, 2], [3, 4]])\n[[3, 1], [4, 2]]",
        difficulty="medium",
        family_id="family_matrix_grid_logic",
        split=Split.VAL,
        reference_solution=(
            "def rotate_matrix_90(mat: list[list[int]]) -> list[list[int]]:\n"
            "    return [list(x) for x in zip(*mat[::-1])]\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[[1]]], "expected": [[1]]},
            {"inputs": [[[1, 2], [3, 4]]], "expected": [[3, 1], [4, 2]]},
            {"inputs": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [[7, 4, 1], [8, 5, 2], [9, 6, 3]]},
            {"inputs": [[[0, 0], [0, 0]]], "expected": [[0, 0], [0, 0]]},
            {"inputs": [[[-1, -2], [-3, -4]]], "expected": [[-3, -1], [-4, -2]]},
            {"inputs": [[[1, 0], [0, 1]]], "expected": [[0, 1], [1, 0]]},
            {"inputs": [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]], "expected": [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]},
            {"inputs": [[[1, 2], [2, 1]]], "expected": [[2, 1], [1, 2]]},
            {"inputs": [[[10, 20], [30, 40]]], "expected": [[30, 10], [40, 20]]},
            {"inputs": [[[42]]], "expected": [[42]]},
            {"inputs": [[[9, 8], [7, 6]]], "expected": [[7, 9], [6, 8]]},
            {"inputs": [[[0, 1], [1, 0]]], "expected": [[1, 0], [0, 1]]},
            {"inputs": [[[1, 1], [1, 1]]], "expected": [[1, 1], [1, 1]]},
            {"inputs": [[[2, 4, 6], [8, 10, 12], [14, 16, 18]]], "expected": [[14, 8, 2], [16, 10, 4], [18, 12, 6]]},
            {"inputs": [[[3, 2], [1, 0]]], "expected": [[1, 3], [0, 2]]},
            {"inputs": [[[1, 2, 3], [0, 0, 0], [3, 2, 1]]], "expected": [[3, 0, 1], [2, 0, 2], [1, 0, 3]]},
            {"inputs": [[[5, 5], [5, 5]]], "expected": [[5, 5], [5, 5]]},
            {"inputs": [[[7]]], "expected": [[7]]},
            {"inputs": [[[1, 0, 0], [0, 1, 0], [0, 0, 1]]], "expected": [[0, 0, 1], [0, 1, 0], [1, 0, 0]]},
        ],
        tags=["matrix", "rotation"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-mat-004",
        entry_point="count_islands",
        signature="def count_islands(grid: list[list[int]]) -> int:",
        docstring="Count the number of 4-directionally connected islands of 1s in 2D binary grid.\n\n>>> count_islands([[1, 1, 0], [1, 0, 0], [0, 0, 1]])\n2",
        difficulty="medium",
        family_id="family_matrix_grid_logic",
        split=Split.VAL,
        reference_solution=(
            "def count_islands(grid: list[list[int]]) -> int:\n"
            "    if not grid or not grid[0]:\n"
            "        return 0\n"
            "    R, C = len(grid), len(grid[0])\n"
            "    visited = set()\n"
            "    islands = 0\n"
            "    def dfs(r, c):\n"
            "        visited.add((r, c))\n"
            "        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:\n"
            "            nr, nc = r + dr, c + dc\n"
            "            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1 and (nr, nc) not in visited:\n"
            "                dfs(nr, nc)\n"
            "    for r in range(R):\n"
            "        for c in range(C):\n"
            "            if grid[r][c] == 1 and (r, c) not in visited:\n"
            "                dfs(r, c)\n"
            "                islands += 1\n"
            "    return islands\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": 0},
            {"inputs": [[[0]]], "expected": 0},
            {"inputs": [[[1]]], "expected": 1},
            {"inputs": [[[1, 1, 0], [1, 0, 0], [0, 0, 1]]], "expected": 2},
            {"inputs": [[[1, 1, 1], [0, 1, 0], [1, 1, 1]]], "expected": 1},
            {"inputs": [[[1, 0, 1], [0, 1, 0], [1, 0, 1]]], "expected": 5},
            {"inputs": [[[0, 0, 0], [0, 0, 0]]], "expected": 0},
            {"inputs": [[[1, 1], [1, 1]]], "expected": 1},
            {"inputs": [[[1, 0], [0, 1]]], "expected": 2},
            {"inputs": [[[1, 1, 1, 1]]], "expected": 1},
            {"inputs": [[[1], [1], [1], [1]]], "expected": 1},
            {"inputs": [[[1, 0, 1, 0, 1]]], "expected": 3},
            {"inputs": [[[1], [0], [1], [0], [1]]], "expected": 3},
            {"inputs": [[[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]]], "expected": 3},
            {"inputs": [[[0, 1], [1, 0]]], "expected": 2},
            {"inputs": [[[0, 0, 1], [0, 0, 0], [1, 0, 0]]], "expected": 2},
            {"inputs": [[[1, 0, 0], [0, 0, 0], [0, 0, 1]]], "expected": 2},
            {"inputs": [[[1, 1, 1], [1, 1, 1], [1, 1, 1]]], "expected": 1},
            {"inputs": [[[0, 1, 0], [1, 1, 1], [0, 1, 0]]], "expected": 1},
            {"inputs": [[[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]]], "expected": 5},
        ],
        tags=["matrix", "graphs", "dfs"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-mat-005",
        entry_point="spiral_order",
        signature="def spiral_order(matrix: list[list[int]]) -> list[int]:",
        docstring="Return all elements of matrix in spiral order.\n\n>>> spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]])\n[1, 2, 3, 6, 9, 8, 7, 4, 5]",
        difficulty="medium",
        family_id="family_matrix_grid_logic",
        split=Split.VAL,
        reference_solution=(
            "def spiral_order(matrix: list[list[int]]) -> list[int]:\n"
            "    if not matrix:\n"
            "        return []\n"
            "    res = []\n"
            "    top, bottom = 0, len(matrix) - 1\n"
            "    left, right = 0, len(matrix[0]) - 1\n"
            "    while top <= bottom and left <= right:\n"
            "        for c in range(left, right + 1):\n"
            "            res.append(matrix[top][c])\n"
            "        top += 1\n"
            "        for r in range(top, bottom + 1):\n"
            "            res.append(matrix[r][right])\n"
            "        right -= 1\n"
            "        if top <= bottom:\n"
            "            for c in range(right, left - 1, -1):\n"
            "                res.append(matrix[bottom][c])\n"
            "            bottom -= 1\n"
            "        if left <= right:\n"
            "            for r in range(bottom, top - 1, -1):\n"
            "                res.append(matrix[r][left])\n"
            "            left += 1\n"
            "    return res\n"
        ),
        test_cases=[
            {"inputs": [[]], "expected": []},
            {"inputs": [[[1]]], "expected": [1]},
            {"inputs": [[[1, 2], [3, 4]]], "expected": [1, 2, 4, 3]},
            {"inputs": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [1, 2, 3, 6, 9, 8, 7, 4, 5]},
            {"inputs": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]], "expected": [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]},
            {"inputs": [[[1, 2, 3, 4]]], "expected": [1, 2, 3, 4]},
            {"inputs": [[[1], [2], [3], [4]]], "expected": [1, 2, 3, 4]},
            {"inputs": [[[2, 5, 8], [4, 0, -1]]], "expected": [2, 5, 8, -1, 0, 4]},
            {"inputs": [[[1, 2], [4, 3]]], "expected": [1, 2, 3, 4]},
            {"inputs": [[[7, 9], [6, 8]]], "expected": [7, 9, 8, 6]},
            {"inputs": [[[1, 2], [3, 4], [5, 6]]], "expected": [1, 2, 4, 6, 5, 3]},
            {"inputs": [[[1, 2, 3], [4, 5, 6]]], "expected": [1, 2, 3, 6, 5, 4]},
            {"inputs": [[[1, 2, 3, 4], [5, 6, 7, 8]]], "expected": [1, 2, 3, 4, 8, 7, 6, 5]},
            {"inputs": [[[3], [2]]], "expected": [3, 2]},
            {"inputs": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]], "expected": [1, 2, 3, 4, 8, 12, 16, 15, 14, 13, 9, 5, 6, 7, 11, 10]},
            {"inputs": [[[42]]], "expected": [42]},
            {"inputs": [[[0, 0], [0, 0]]], "expected": [0, 0, 0, 0]},
            {"inputs": [[[1, 2, 3], [8, 9, 4], [7, 6, 5]]], "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9]},
            {"inputs": [[[10, 20], [40, 30]]], "expected": [10, 20, 30, 40]},
            {"inputs": [[[1, 2, 3, 4, 5]]], "expected": [1, 2, 3, 4, 5]},
        ],
        tags=["matrix", "traversal"],
    ))

    # =========================================================================
    # FAMILY 5: date_time_calculations (TEST) - 5 tasks
    # =========================================================================
    tasks.append(RawTaskDefinition(
        task_id="py-dt-001",
        entry_point="is_leap_year",
        signature="def is_leap_year(year: int) -> bool:",
        docstring="Check if year is a leap year according to the Gregorian calendar rules.\n\n>>> is_leap_year(2000)\nTrue",
        difficulty="easy",
        family_id="family_date_time_calculations",
        split=Split.TEST,
        reference_solution=(
            "def is_leap_year(year: int) -> bool:\n"
            "    if year % 400 == 0:\n"
            "        return True\n"
            "    if year % 100 == 0:\n"
            "        return False\n"
            "    return year % 4 == 0\n"
        ),
        test_cases=[
            {"inputs": [2000], "expected": True},
            {"inputs": [1900], "expected": False},
            {"inputs": [2100], "expected": False},
            {"inputs": [2004], "expected": True},
            {"inputs": [2008], "expected": True},
            {"inputs": [2012], "expected": True},
            {"inputs": [2016], "expected": True},
            {"inputs": [2020], "expected": True},
            {"inputs": [2024], "expected": True},
            {"inputs": [2021], "expected": False},
            {"inputs": [2022], "expected": False},
            {"inputs": [2023], "expected": False},
            {"inputs": [1600], "expected": True},
            {"inputs": [1700], "expected": False},
            {"inputs": [1800], "expected": False},
            {"inputs": [4], "expected": True},
            {"inputs": [100], "expected": False},
            {"inputs": [400], "expected": True},
            {"inputs": [1], "expected": False},
            {"inputs": [20000], "expected": True},
        ],
        tags=["datetime", "calendar"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-dt-002",
        entry_point="seconds_to_hms",
        signature="def seconds_to_hms(seconds: int) -> str:",
        docstring="Convert non-negative integer seconds into 'HH:MM:SS' format string.\n\n>>> seconds_to_hms(3665)\n'01:01:05'",
        difficulty="easy",
        family_id="family_date_time_calculations",
        split=Split.TEST,
        reference_solution=(
            "def seconds_to_hms(seconds: int) -> str:\n"
            "    h = seconds // 3600\n"
            "    m = (seconds % 3600) // 60\n"
            "    s = seconds % 60\n"
            "    return f'{h:02d}:{m:02d}:{s:02d}'\n"
        ),
        test_cases=[
            {"inputs": [0], "expected": "00:00:00"},
            {"inputs": [1], "expected": "00:00:01"},
            {"inputs": [59], "expected": "00:00:59"},
            {"inputs": [60], "expected": "00:01:00"},
            {"inputs": [65], "expected": "00:01:05"},
            {"inputs": [3599], "expected": "00:59:59"},
            {"inputs": [3600], "expected": "01:00:00"},
            {"inputs": [3665], "expected": "01:01:05"},
            {"inputs": [7200], "expected": "02:00:00"},
            {"inputs": [86399], "expected": "23:59:59"},
            {"inputs": [86400], "expected": "24:00:00"},
            {"inputs": [90000], "expected": "25:00:00"},
            {"inputs": [10], "expected": "00:00:10"},
            {"inputs": [120], "expected": "00:02:00"},
            {"inputs": [1800], "expected": "00:30:00"},
            {"inputs": [5000], "expected": "01:23:20"},
            {"inputs": [10000], "expected": "02:46:40"},
            {"inputs": [42], "expected": "00:00:42"},
            {"inputs": [9999], "expected": "02:46:39"},
            {"inputs": [36000], "expected": "10:00:00"},
        ],
        tags=["datetime", "formatting"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-dt-003",
        entry_point="days_in_month",
        signature="def days_in_month(year: int, month: int) -> int:",
        docstring="Return the number of days in the given month (1-12) of year, accounting for leap years.\n\n>>> days_in_month(2024, 2)\n29",
        difficulty="easy",
        family_id="family_date_time_calculations",
        split=Split.TEST,
        reference_solution=(
            "def days_in_month(year: int, month: int) -> int:\n"
            "    import calendar\n"
            "    return calendar.monthrange(year, month)[1]\n"
        ),
        test_cases=[
            {"inputs": [2024, 1], "expected": 31},
            {"inputs": [2024, 2], "expected": 29},
            {"inputs": [2023, 2], "expected": 28},
            {"inputs": [2000, 2], "expected": 29},
            {"inputs": [1900, 2], "expected": 28},
            {"inputs": [2024, 3], "expected": 31},
            {"inputs": [2024, 4], "expected": 30},
            {"inputs": [2024, 5], "expected": 31},
            {"inputs": [2024, 6], "expected": 30},
            {"inputs": [2024, 7], "expected": 31},
            {"inputs": [2024, 8], "expected": 31},
            {"inputs": [2024, 9], "expected": 30},
            {"inputs": [2024, 10], "expected": 31},
            {"inputs": [2024, 11], "expected": 30},
            {"inputs": [2024, 12], "expected": 31},
            {"inputs": [2020, 2], "expected": 29},
            {"inputs": [2021, 2], "expected": 28},
            {"inputs": [2022, 2], "expected": 28},
            {"inputs": [2025, 2], "expected": 28},
            {"inputs": [2028, 2], "expected": 29},
        ],
        tags=["datetime", "calendar"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-dt-004",
        entry_point="day_of_week",
        signature="def day_of_week(year: int, month: int, day: int) -> str:",
        docstring="Return the day of week name ('Monday', 'Tuesday', etc.) for the given date.\n\n>>> day_of_week(2024, 1, 1)\n'Monday'",
        difficulty="medium",
        family_id="family_date_time_calculations",
        split=Split.TEST,
        reference_solution=(
            "def day_of_week(year: int, month: int, day: int) -> str:\n"
            "    import datetime\n"
            "    d = datetime.date(year, month, day)\n"
            "    return d.strftime('%A')\n"
        ),
        test_cases=[
            {"inputs": [2024, 1, 1], "expected": "Monday"},
            {"inputs": [2024, 1, 2], "expected": "Tuesday"},
            {"inputs": [2024, 1, 3], "expected": "Wednesday"},
            {"inputs": [2024, 1, 4], "expected": "Thursday"},
            {"inputs": [2024, 1, 5], "expected": "Friday"},
            {"inputs": [2024, 1, 6], "expected": "Saturday"},
            {"inputs": [2024, 1, 7], "expected": "Sunday"},
            {"inputs": [2024, 2, 29], "expected": "Thursday"},
            {"inputs": [2000, 1, 1], "expected": "Saturday"},
            {"inputs": [1999, 12, 31], "expected": "Friday"},
            {"inputs": [2020, 12, 25], "expected": "Friday"},
            {"inputs": [2023, 10, 31], "expected": "Tuesday"},
            {"inputs": [2026, 10, 30], "expected": "Friday"},
            {"inputs": [1969, 7, 20], "expected": "Sunday"},
            {"inputs": [1776, 7, 4], "expected": "Thursday"},
            {"inputs": [2025, 1, 1], "expected": "Wednesday"},
            {"inputs": [2025, 7, 4], "expected": "Friday"},
            {"inputs": [2022, 2, 22], "expected": "Tuesday"},
            {"inputs": [2021, 6, 21], "expected": "Monday"},
            {"inputs": [2024, 12, 31], "expected": "Tuesday"},
        ],
        tags=["datetime", "calendar"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-dt-005",
        entry_point="days_between",
        signature="def days_between(d1: str, d2: str) -> int:",
        docstring="Return the absolute number of days between two ISO date strings 'YYYY-MM-DD'.\n\n>>> days_between('2024-01-01', '2024-01-10')\n9",
        difficulty="easy",
        family_id="family_date_time_calculations",
        split=Split.TEST,
        reference_solution=(
            "def days_between(d1: str, d2: str) -> int:\n"
            "    import datetime\n"
            "    dt1 = datetime.date.fromisoformat(d1)\n"
            "    dt2 = datetime.date.fromisoformat(d2)\n"
            "    return abs((dt2 - dt1).days)\n"
        ),
        test_cases=[
            {"inputs": ["2024-01-01", "2024-01-01"], "expected": 0},
            {"inputs": ["2024-01-01", "2024-01-02"], "expected": 1},
            {"inputs": ["2024-01-02", "2024-01-01"], "expected": 1},
            {"inputs": ["2024-01-01", "2024-01-10"], "expected": 9},
            {"inputs": ["2024-01-01", "2024-02-01"], "expected": 31},
            {"inputs": ["2024-02-01", "2024-03-01"], "expected": 29},
            {"inputs": ["2023-02-01", "2023-03-01"], "expected": 28},
            {"inputs": ["2024-01-01", "2024-12-31"], "expected": 365},
            {"inputs": ["2023-01-01", "2023-12-31"], "expected": 364},
            {"inputs": ["2020-01-01", "2021-01-01"], "expected": 366},
            {"inputs": ["2000-01-01", "2000-01-01"], "expected": 0},
            {"inputs": ["2024-05-01", "2024-05-15"], "expected": 14},
            {"inputs": ["2024-06-01", "2024-06-30"], "expected": 29},
            {"inputs": ["2024-07-04", "2024-07-04"], "expected": 0},
            {"inputs": ["2022-10-01", "2022-10-31"], "expected": 30},
            {"inputs": ["2021-11-01", "2021-11-30"], "expected": 29},
            {"inputs": ["2020-02-28", "2020-03-01"], "expected": 2},
            {"inputs": ["2021-02-28", "2021-03-01"], "expected": 1},
            {"inputs": ["2024-01-15", "2024-01-20"], "expected": 5},
            {"inputs": ["2025-01-01", "2026-01-01"], "expected": 365},
        ],
        tags=["datetime", "intervals"],
    ))

    return tasks
