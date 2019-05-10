import sys
import re
import json
import requests
import textwrap
from typing import List, Set, Dict, Callable
from argparse import ArgumentParser
from random import choice


def sanitize_quote(quote: str) -> str:
    # Strip HTML tags
    quote = re.sub(r'<.*?>', '', quote)  # type: str

    # Replace HTML entities
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
        quote = quote.replace(c, replace[c])

    # Strip leading and trailing whitespaces
    return quote.strip()


class SourceAPI:
    def fetch_quotes(self, n: int, batch_size: int) -> List[str]:
        raise NotImplementedError


class QuotesOnDesignAPI(SourceAPI):
    def __init__(self):
        self.__url = 'http://quotesondesign.com/wp-json/posts'

    def fetch_quotes(self, n: int, batch_size: int) -> List[str]:
        params = {
            'filter[orderby]': 'rand',
            'filter[posts_per_page]': batch_size
        }

        # Make this a set so there are no duplicates
        quotes = set()  # type: Set[str]

        while len(quotes) < n:
            response = requests.get(url=self.__url, params=params)
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


class DeszczowceAPI(SourceAPI):
    def __init__(self):
        self.__url = 'http://www.deszczowce.pl/skrypty/losowy_cytat.php'

    def fetch_quotes(self, n: int, batch_size: int) -> List[str]:
        print("NOTE: Deszczowce API doesn't support fetching in batches. Consider fetching small amounts of quotes.")

        quotes = set()  # type: Set[str]
        for i in range(n):
            response = requests.get(url=self.__url)
            if response.ok:
                content = response.content.decode('iso-8859-2')
                match = re.search(r'<i>(.*?)"</i>', content)
                if match:
                    quote = match.groups()[0][1:]  # type: str
                    quotes.add(quote)
                    print('Fetched %d/%d quotes.' % (i + 1, n))
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

    # Dataset source APIs
    sources = {
        'quotesondesign': QuotesOnDesignAPI(),
        'deszczowce':     DeszczowceAPI()
    }

    # Parse options
    parser = ArgumentParser(description='Generates quotes.')

    parser.add_argument('--dataset-source', '-s',     dest='dataset_source', default='quotesondesign', choices=sources.keys(),
                        help='the API to use to fetch the source dataset')

    parser.add_argument('--dataset-size', '-n',       dest='dataset_size',   default=200,              type=int,
                        help='how many quotes to fetch from the API to use as the source dataset')

    parser.add_argument('--dataset-batch-size', '-b', dest='batch_size',     default=40,               type=int,
                        help='how many quotes to fetch in a single request')

    parser.add_argument('--ngram-length', '-g',       dest='ngram_length',   default=5,                type=int,
                        help='length of ngrams to use for the Markov chain')

    args = parser.parse_args()

    # Generate & print
    print('Fetching dataset...')
    source = sources[args.dataset_source]
    quotes = source.fetch_quotes(args.dataset_size, args.batch_size)
    quote = Generator(quotes, args.ngram_length).generate()

    wrapped = '\n\t '.join(textwrap.wrap(quote, 80))
    print('\n\t"%s"\n' % wrapped)
