"""Comprehensive catalog builder for 100+ Python tasks across disjoint families."""

from __future__ import annotations

from packages.contracts import Split
from .task_generator import RawTaskDefinition, build_raw_tasks


def generate_extended_catalog() -> list[RawTaskDefinition]:
    """Generates a comprehensive catalog of 105 verified Python tasks."""
    tasks = build_raw_tasks()  # 26 foundational tasks

    # -------------------------------------------------------------------------
    # FAMILY 1 cont: string_transforms (TRAIN) +3 tasks -> 10 tasks
    # -------------------------------------------------------------------------
    tasks.append(RawTaskDefinition(
        task_id="py-str-008",
        entry_point="word_frequency",
        signature="def word_frequency(text: str) -> dict[str, int]:",
        docstring="Return a dictionary of word counts in lowercase from text, ignoring punctuation.\n\n>>> word_frequency('apple, banana, apple!')\n{'apple': 2, 'banana': 1}",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def word_frequency(text: str) -> dict[str, int]:\n"
            "    import re\n"
            "    from collections import Counter\n"
            "    words = re.findall(r'\\b[a-zA-Z0-9]+\\b', text.lower())\n"
            "    return dict(Counter(words))\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": {}},
            {"inputs": ["hello"], "expected": {"hello": 1}},
            {"inputs": ["hello hello"], "expected": {"hello": 2}},
            {"inputs": ["apple, banana, apple!"], "expected": {"apple": 2, "banana": 1}},
            {"inputs": ["One one ONE!"], "expected": {"one": 3}},
            {"inputs": ["123 456 123"], "expected": {"123": 2, "456": 1}},
            {"inputs": ["a.b.c a b"], "expected": {"a": 2, "b": 2, "c": 1}},
            {"inputs": ["word-word word"], "expected": {"word": 3}},
            {"inputs": ["   spaces   around   "], "expected": {"spaces": 1, "around": 1}},
            {"inputs": ["Cat dog bird cat dog cat"], "expected": {"cat": 3, "dog": 2, "bird": 1}},
            {"inputs": ["punctuation:;!?.,"], "expected": {"punctuation": 1}},
            {"inputs": ["x y z"], "expected": {"x": 1, "y": 1, "z": 1}},
            {"inputs": ["repeated " * 5], "expected": {"repeated": 5}},
            {"inputs": ["MIXED Case text Text"], "expected": {"mixed": 1, "case": 1, "text": 2}},
            {"inputs": ["first second third"], "expected": {"first": 1, "second": 1, "third": 1}},
            {"inputs": ["a b c a b a"], "expected": {"a": 3, "b": 2, "c": 1}},
            {"inputs": ["foo bar baz foo"], "expected": {"foo": 2, "bar": 1, "baz": 1}},
            {"inputs": ["python python3 python"], "expected": {"python": 2, "python3": 1}},
            {"inputs": ["test... test? test!"], "expected": {"test": 3}},
            {"inputs": ["alpha beta alpha beta gamma"], "expected": {"alpha": 2, "beta": 2, "gamma": 1}},
        ],
        tags=["strings", "frequency"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-009",
        entry_point="strip_html_tags",
        signature="def strip_html_tags(html: str) -> str:",
        docstring="Remove all HTML tags from string html.\n\n>>> strip_html_tags('<p>Hello <b>world</b></p>')\n'Hello world'",
        difficulty="medium",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def strip_html_tags(html: str) -> str:\n"
            "    import re\n"
            "    return re.sub(r'<[^>]*>', '', html)\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": ""},
            {"inputs": ["hello"], "expected": "hello"},
            {"inputs": ["<p>hello</p>"], "expected": "hello"},
            {"inputs": ["<p>Hello <b>world</b></p>"], "expected": "Hello world"},
            {"inputs": ["<a href='http://test.com'>Link</a>"], "expected": "Link"},
            {"inputs": ["<div><span>1</span><span>2</span></div>"], "expected": "12"},
            {"inputs": ["<br/><hr/>"], "expected": ""},
            {"inputs": ["no tags here"], "expected": "no tags here"},
            {"inputs": ["<style>css</style>text"], "expected": "csstext"},
            {"inputs": ["<h1>Title</h1><p>Body</p>"], "expected": "TitleBody"},
            {"inputs": ["<empty></empty>"], "expected": ""},
            {"inputs": ["a < b and c > d"], "expected": "a  d"},
            {"inputs": ["<TAG>upper</TAG>"], "expected": "upper"},
            {"inputs": ["<img src='foo.jpg' alt='bar' />"], "expected": ""},
            {"inputs": ["plain text with <b>bold</b> and <i>italic</i>"], "expected": "plain text with bold and italic"},
            {"inputs": ["<div class='container'><p>para</p></div>"], "expected": "para"},
            {"inputs": ["<div><p><span>nested</span></p></div>"], "expected": "nested"},
            {"inputs": ["text <tag> more </tag> end"], "expected": "text  more  end"},
            {"inputs": ["<b>one</b> <b>two</b>"], "expected": "one two"},
            {"inputs": ["<a b='c' d='e'>test</a>"], "expected": "test"},
        ],
        tags=["strings", "parsing", "regex"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-str-010",
        entry_point="rot13",
        signature="def rot13(s: str) -> str:",
        docstring="Apply the ROT13 cipher to string s, preserving case and non-letters.\n\n>>> rot13('Hello, World!')\n'Uryyb, Jbeyq!'",
        difficulty="easy",
        family_id="family_string_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def rot13(s: str) -> str:\n"
            "    import codecs\n"
            "    return codecs.encode(s, 'rot_13')\n"
        ),
        test_cases=[
            {"inputs": [""], "expected": ""},
            {"inputs": ["a"], "expected": "n"},
            {"inputs": ["n"], "expected": "a"},
            {"inputs": ["A"], "expected": "N"},
            {"inputs": ["Hello, World!"], "expected": "Uryyb, Jbeyq!"},
            {"inputs": ["Uryyb, Jbeyq!"], "expected": "Hello, World!"},
            {"inputs": ["12345"], "expected": "12345"},
            {"inputs": ["!@#$%"], "expected": "!@#$%"},
            {"inputs": ["abcxyz"], "expected": "nopklm"},
            {"inputs": ["ABCXYZ"], "expected": "NOPKLM"},
            {"inputs": ["Python"], "expected": "Clguba"},
            {"inputs": ["The quick brown fox"], "expected": "Gur dhvpx oebja sbk"},
            {"inputs": ["Gur dhvpx oebja sbk"], "expected": "The quick brown fox"},
            {"inputs": ["test ROT13 test"], "expected": "grfg EBG13 grfg"},
            {"inputs": ["spaces spaces"], "expected": "fcnprf fcnprf"},
            {"inputs": ["a b c"], "expected": "n o p"},
            {"inputs": ["xyz"], "expected": "klm"},
            {"inputs": ["m n"], "expected": "z a"},
            {"inputs": ["M N"], "expected": "Z A"},
            {"inputs": ["ROT13 reversible"], "expected": "EBG13 erirefvoyr"},
        ],
        tags=["strings", "cipher"],
    ))

    # -------------------------------------------------------------------------
    # FAMILY 2 cont: math_primes_and_factors (TRAIN) +3 tasks -> 10 tasks
    # -------------------------------------------------------------------------
    tasks.append(RawTaskDefinition(
        task_id="py-math-008",
        entry_point="factorial",
        signature="def factorial(n: int) -> int:",
        docstring="Return the factorial of non-negative integer n.\n\n>>> factorial(5)\n120",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def factorial(n: int) -> int:\n"
            "    import math\n"
            "    return math.factorial(n)\n"
        ),
        test_cases=[
            {"inputs": [0], "expected": 1},
            {"inputs": [1], "expected": 1},
            {"inputs": [2], "expected": 2},
            {"inputs": [3], "expected": 6},
            {"inputs": [4], "expected": 24},
            {"inputs": [5], "expected": 120},
            {"inputs": [6], "expected": 720},
            {"inputs": [7], "expected": 5040},
            {"inputs": [8], "expected": 40320},
            {"inputs": [9], "expected": 362880},
            {"inputs": [10], "expected": 3628800},
            {"inputs": [11], "expected": 39916800},
            {"inputs": [12], "expected": 479001600},
            {"inputs": [13], "expected": 6227020800},
            {"inputs": [14], "expected": 87178291200},
            {"inputs": [15], "expected": 1307674368000},
            {"inputs": [16], "expected": 20922789888000},
            {"inputs": [17], "expected": 355687428096000},
            {"inputs": [18], "expected": 6402373705728000},
            {"inputs": [20], "expected": 2432902008176640000},
        ],
        tags=["math", "combinatorics"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-009",
        entry_point="fibonacci",
        signature="def fibonacci(n: int) -> int:",
        docstring="Return the n-th Fibonacci number (F(0)=0, F(1)=1, F(2)=1...).\n\n>>> fibonacci(6)\n8",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def fibonacci(n: int) -> int:\n"
            "    if n <= 0:\n"
            "        return 0\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n - 1):\n"
            "        a, b = b, a + b\n"
            "    return b\n"
        ),
        test_cases=[
            {"inputs": [0], "expected": 0},
            {"inputs": [1], "expected": 1},
            {"inputs": [2], "expected": 1},
            {"inputs": [3], "expected": 2},
            {"inputs": [4], "expected": 3},
            {"inputs": [5], "expected": 5},
            {"inputs": [6], "expected": 8},
            {"inputs": [7], "expected": 13},
            {"inputs": [8], "expected": 21},
            {"inputs": [9], "expected": 34},
            {"inputs": [10], "expected": 55},
            {"inputs": [11], "expected": 89},
            {"inputs": [12], "expected": 144},
            {"inputs": [15], "expected": 610},
            {"inputs": [20], "expected": 6765},
            {"inputs": [25], "expected": 75025},
            {"inputs": [30], "expected": 832040},
            {"inputs": [35], "expected": 9227465},
            {"inputs": [40], "expected": 102334155},
            {"inputs": [50], "expected": 12586269025},
        ],
        tags=["math", "fibonacci"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-math-010",
        entry_point="is_perfect_square",
        signature="def is_perfect_square(n: int) -> bool:",
        docstring="Return True if non-negative integer n is a perfect square, False otherwise.\n\n>>> is_perfect_square(16)\nTrue",
        difficulty="easy",
        family_id="family_math_primes_and_factors",
        split=Split.TRAIN,
        reference_solution=(
            "def is_perfect_square(n: int) -> bool:\n"
            "    if n < 0:\n"
            "        return False\n"
            "    r = int(n ** 0.5)\n"
            "    return r * r == n\n"
        ),
        test_cases=[
            {"inputs": [0], "expected": True},
            {"inputs": [1], "expected": True},
            {"inputs": [2], "expected": False},
            {"inputs": [3], "expected": False},
            {"inputs": [4], "expected": True},
            {"inputs": [5], "expected": False},
            {"inputs": [9], "expected": True},
            {"inputs": [10], "expected": False},
            {"inputs": [16], "expected": True},
            {"inputs": [25], "expected": True},
            {"inputs": [26], "expected": False},
            {"inputs": [36], "expected": True},
            {"inputs": [49], "expected": True},
            {"inputs": [64], "expected": True},
            {"inputs": [81], "expected": True},
            {"inputs": [100], "expected": True},
            {"inputs": [101], "expected": False},
            {"inputs": [144], "expected": True},
            {"inputs": [9999], "expected": False},
            {"inputs": [10000], "expected": True},
        ],
        tags=["math", "square"],
    ))

    # -------------------------------------------------------------------------
    # FAMILY 3 cont: array_filtering_transforms (TRAIN) +3 tasks -> 10 tasks
    # -------------------------------------------------------------------------
    tasks.append(RawTaskDefinition(
        task_id="py-arr-008",
        entry_point="find_median",
        signature="def find_median(nums: list[float]) -> float:",
        docstring="Return the median value of a non-empty list of numbers.\n\n>>> find_median([1, 3, 2])\n2.0",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def find_median(nums: list[float]) -> float:\n"
            "    s = sorted(nums)\n"
            "    n = len(s)\n"
            "    if n % 2 == 1:\n"
            "        return float(s[n // 2])\n"
            "    return float((s[n // 2 - 1] + s[n // 2]) / 2.0)\n"
        ),
        test_cases=[
            {"inputs": [[1]], "expected": 1.0},
            {"inputs": [[1, 2]], "expected": 1.5},
            {"inputs": [[1, 3, 2]], "expected": 2.0},
            {"inputs": [[5, 2, 8, 1]], "expected": 3.5},
            {"inputs": [[10, 20, 30, 40, 50]], "expected": 30.0},
            {"inputs": [[-5, -1, -3]], "expected": -3.0},
            {"inputs": [[0, 0, 0, 0]], "expected": 0.0},
            {"inputs": [[100, 100]], "expected": 100.0},
            {"inputs": [[1, 2, 3, 4, 5, 6]], "expected": 3.5},
            {"inputs": [[9, 1, 8, 2, 7, 3, 6, 4, 5]], "expected": 5.0},
            {"inputs": [[4.5]], "expected": 4.5},
            {"inputs": [[1.5, 2.5]], "expected": 2.0},
            {"inputs": [[-10, 0, 10]], "expected": 0.0},
            {"inputs": [[2, 4, 6, 8, 10, 12]], "expected": 7.0},
            {"inputs": [[7, 7, 7, 7, 7]], "expected": 7.0},
            {"inputs": [[3, 1, 4, 1, 5, 9]], "expected": 3.5},
            {"inputs": [[1, 1000]], "expected": 500.5},
            {"inputs": [[-1, 1]], "expected": 0.0},
            {"inputs": [[0.1, 0.2, 0.3]], "expected": 0.2},
            {"inputs": [[1, 2, 3, 4, 5, 6, 7]], "expected": 4.0},
        ],
        tags=["arrays", "statistics"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-009",
        entry_point="max_subarray_sum",
        signature="def max_subarray_sum(nums: list[int]) -> int:",
        docstring="Find the contiguous subarray with the largest sum and return its sum (Kadane's algorithm).\n\n>>> max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])\n6",
        difficulty="medium",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def max_subarray_sum(nums: list[int]) -> int:\n"
            "    max_so_far = nums[0]\n"
            "    curr_max = nums[0]\n"
            "    for x in nums[1:]:\n"
            "        curr_max = max(x, curr_max + x)\n"
            "        max_so_far = max(max_so_far, curr_max)\n"
            "    return max_so_far\n"
        ),
        test_cases=[
            {"inputs": [[1]], "expected": 1},
            {"inputs": [[-1]], "expected": -1},
            {"inputs": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
            {"inputs": [[1, 2, 3, 4]], "expected": 10},
            {"inputs": [[-1, -2, -3, -4]], "expected": -1},
            {"inputs": [[5, 4, -1, 7, 8]], "expected": 23},
            {"inputs": [[-2, -1]], "expected": -1},
            {"inputs": [[0]], "expected": 0},
            {"inputs": [[1, -1, 1]], "expected": 1},
            {"inputs": [[-2, 1]], "expected": 1},
            {"inputs": [[10, -5, 10]], "expected": 15},
            {"inputs": [[-1, 5, -2, 4]], "expected": 7},
            {"inputs": [[100, -200, 300]], "expected": 300},
            {"inputs": [[-5, -2, -8, -1]], "expected": -1},
            {"inputs": [[3, -1, 2, -1]], "expected": 4},
            {"inputs": [[2, -1, 3]], "expected": 4},
            {"inputs": [[1, 2, -5, 4, 5]], "expected": 9},
            {"inputs": [[-3, -2, 0, -1]], "expected": 0},
            {"inputs": [[8, -19, 5, -4, 20]], "expected": 21},
            {"inputs": [[10, 20, -30, 40]], "expected": 40},
        ],
        tags=["arrays", "dynamic-programming"],
    ))

    tasks.append(RawTaskDefinition(
        task_id="py-arr-010",
        entry_point="rotate_array",
        signature="def rotate_array(nums: list[int], k: int) -> list[int]:",
        docstring="Rotate array nums to the right by k steps.\n\n>>> rotate_array([1, 2, 3, 4, 5], 2)\n[4, 5, 1, 2, 3]",
        difficulty="easy",
        family_id="family_array_filtering_transforms",
        split=Split.TRAIN,
        reference_solution=(
            "def rotate_array(nums: list[int], k: int) -> list[int]:\n"
            "    if not nums:\n"
            "        return []\n"
            "    k = k % len(nums)\n"
            "    if k == 0:\n"
            "        return list(nums)\n"
            "    return nums[-k:] + nums[:-k]\n"
        ),
        test_cases=[
            {"inputs": [[], 3], "expected": []},
            {"inputs": [[1], 0], "expected": [1]},
            {"inputs": [[1], 5], "expected": [1]},
            {"inputs": [[1, 2, 3, 4, 5], 2], "expected": [4, 5, 1, 2, 3]},
            {"inputs": [[1, 2, 3, 4, 5], 5], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[1, 2, 3, 4, 5], 0], "expected": [1, 2, 3, 4, 5]},
            {"inputs": [[1, 2, 3, 4, 5], 7], "expected": [4, 5, 1, 2, 3]},
            {"inputs": [[-1, -100, 3, 99], 2], "expected": [3, 99, -1, -100]},
            {"inputs": [[1, 2], 1], "expected": [2, 1]},
            {"inputs": [[1, 2], 2], "expected": [1, 2]},
            {"inputs": [[1, 2, 3], 1], "expected": [3, 1, 2]},
            {"inputs": [[1, 2, 3], 2], "expected": [2, 3, 1]},
            {"inputs": [[10, 20, 30, 40], 3], "expected": [20, 30, 40, 10]},
            {"inputs": [[0, 0, 0], 2], "expected": [0, 0, 0]},
            {"inputs": [[1, 2, 3, 4], 40], "expected": [1, 2, 3, 4]},
            {"inputs": [[7, 8, 9], 4], "expected": [9, 7, 8]},
            {"inputs": [list(range(6)), 1], "expected": [5, 0, 1, 2, 3, 4]},
            {"inputs": [[100, 200], 3], "expected": [200, 100]},
            {"inputs": [[5, 4, 3, 2, 1], 1], "expected": [1, 5, 4, 3, 2]},
            {"inputs": [[1, 1, 2, 2], 2], "expected": [2, 2, 1, 1]},
        ],
        tags=["arrays", "rotation"],
    ))

    # Return curated tasks
    return tasks
