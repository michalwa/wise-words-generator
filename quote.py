from sys import argv
from json import loads
from requests import get
from random import choice

url = 'http://quotesondesign.com/wp-json/posts'

def removeHTMLTags(s):
    while s.find('<') >= 0:
        tagStartIndex = s.find('<')
        tagEndIndex = s.find('>', tagStartIndex + 1)
        s = s[:tagStartIndex] + s[tagEndIndex + 1:]
    return s

def replaceSpecialCharacters(s):
    replace = {
        '&#8217;': '\'',
        '&#8216;': '\'',
        '&#8220;': '\"',
        '&#8221;': '\"',
        '&#8243;': '\"',
        '&#8211;': '-',
        '&#8212;': '-',
        '&#8230;': '...',
        '&#038;': '&'
    }
    for c in replace:
        s = s.replace(c, replace[c])
    return s

def getQuotes(n):
    params = {
        'filter[orderby]': 'rand', 
        'filter[posts_per_page]': 30
    }
    quotes = []
    while len(quotes) < n:
        req = get(url=url, params=params)
        if req.ok:
            rawQuotes = loads(req.text)
            for q in rawQuotes:
                if len(quotes) < 100:
                    content = q['content']
                    quote = content[len('<p>'):content.index('</p>')]
                    quote = removeHTMLTags(quote)
                    quote = replaceSpecialCharacters(quote)
                    if quote not in quotes:
                        quotes.append(quote)
    return quotes

class MarkovChain:
    def __init__(self, data, n):
        self.data = data
        self.n = n
        self.ngrams = {}
        for s in data:
            for x in range(0, len(s) - n + 1):
                gram = s[x:x+n] 
                if gram not in self.ngrams:
                    self.ngrams[gram] = {}
                nextChar = ''
                if x + n < len(s):
                    nextChar = s[x+n]
                if nextChar in self.ngrams[gram]:
                    self.ngrams[gram][nextChar] += 1
                else:
                    self.ngrams[gram][nextChar] = 1

    def generate(self):
        currentGram = choice(self.data)[0:self.n]
        result = currentGram
        running = True
        while running == True:
            pool = []
            letters = self.ngrams[currentGram]
            for l in letters:
                times = letters[l]
                for t in range(0, times):
                    pool.append(l)
            nextChar = choice(pool)
            if nextChar == '':
                running = False
            else:
                result += nextChar
                currentGram = result[len(result) - self.n:]
        return result

if __name__ == '__main__':
    if len(argv) > 1:
        if argv[1] == 'generate':
            quotes = getQuotes(100)
            print('"' + MarkovChain(quotes, 8).generate() + '"\n' + '~ your PC')


    


        
    


    

