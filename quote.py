import sys
import re
import json
import requests
from typing import List, Set, Dict
from argparse import ArgumentParser
from random import choice

API_URL = 'http://quotesondesign.com/wp-json/posts'


def sanitize_quote(text: str) -> str:

    # Strip HTML tags
    text = re.sub(re.compile('<.*?>'), '', text)  # type: str

    # What is the purpose of this, I'm not really sure?
    replace = {
        '&#8217;': '\'',
        '&#8216;': '\'',
        '&#8220;': '\"',
        '&#8221;': '\"',
        '&#8243;': '\"',
        '&#8211;': '-',
        '&#8212;': '-',
        '&#8230;': '...',
        '&#038;': '&',

        # also remove these
        '\n': '',
        '\r': ''
    }
    for c in replace:
        text = text.replace(c, replace[c])

    # Strip leading and trailing whitespaces
    return text.strip()


def fetch_quotes(n: int, batch_size: int) -> List[str]:
    params = {
        'filter[orderby]': 'rand',
        'filter[posts_per_page]': batch_size
    }

    # Make this a set so there are no duplicates
    quotes = set()  # type: Set[str]

    while len(quotes) < n:
        response = requests.get(url=API_URL, params=params)
        if response.ok:
            for q in json.loads(response.text):
                quotes.add(sanitize_quote(q['content']))
                if len(quotes) >= n:
                    break

            print('Fetched %d/%d quotes.' % (len(quotes), n))
        else:
            print('Error fetching quotes.')
            exit(1)

    return list(quotes)


class Generator:
    def __init__(self, dataset: List[str], ngram_len: int):
        self.__dataset = dataset
        self.__ngram_len = ngram_len
        self.__ngrams = {}  # type: Dict[str, Dict[str, int]]

        for s in dataset:
            for start in range(0, len(s) - ngram_len + 1):

                # Get a slice of the string as the ngram
                gram = s[start:start + ngram_len]
                if gram not in self.__ngrams:
                    self.__ngrams[gram] = {}

                # Find what character comes after the ngram
                next_char = ''
                if start + ngram_len < len(s):
                    next_char = s[start + ngram_len]

                # Increment the probability of that character appearing after the ngram
                if next_char in self.__ngrams[gram]:
                    self.__ngrams[gram][next_char] += 1
                else:
                    self.__ngrams[gram][next_char] = 1

    def generate(self) -> str:

        # Choose the start of a random quote in the dataset as the first ngram
        current = choice(self.__dataset)[0:self.__ngram_len]  # type: str
        result = current

        running = True
        while running:
            pool = []  # type: List[str]
            for char, times in self.__ngrams[current].items():
                pool += [char] * times

            next_char = choice(pool)
            if next_char == '':
                running = False
            else:
                result += next_char
                current = result[len(result) - self.__ngram_len:]

        return result


if __name__ == '__main__':

    # Parse options
    parser = ArgumentParser(description='Generates quotes.')

    parser.add_argument('--dataset-size',       dest='dataset_size', default=200, type=int,
                        help='how many quotes to fetch from the API to use as the source dataset')

    parser.add_argument('--dataset-batch-size', dest='batch_size',   default=40,  type=int,
                        help='how many quotes to fetch in a single request')

    parser.add_argument('--ngram-length',       dest='ngram_length', default=5,   type=int,
                        help='length of ngrams to use for the Markov chain')

    args = parser.parse_args()

    # Generate & print
    quotes = fetch_quotes(args.dataset_size, args.batch_size)
    quote = Generator(quotes, args.ngram_length).generate()

    print('\n\t"%s"\n' % quote)
