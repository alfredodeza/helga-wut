import os
import random
from helga.plugins import match
from helga import log, settings

logger = log.getLogger(__name__)

m = None


class Markov(object):

    def __init__(self, open_file):
        self.cache = {}
        self.open_file = open_file
        self.words = self.file_to_words()
        self.word_size = len(self.words)
        self.database()

    def file_to_words(self):
        self.open_file.seek(0)
        data = self.open_file.read()
        words = data.split()
        return words

    def triples(self):
        """ Generates triples from the given data string. So if our string were
                "What a lovely day", we'd generate (What, a, lovely) and then
                (a, lovely, day).
        """

        if len(self.words) < 3:
            return

        for i in range(len(self.words) - 2):
            yield (self.words[i], self.words[i+1], self.words[i+2])

    def database(self):
        for w1, w2, w3 in self.triples():
            key = (w1, w2)
            if key in self.cache:
                self.cache[key].append(w3)
            else:
                self.cache[key] = [w3]

    def generate_markov_text(self, size=25, about=None):
        seed = random.randint(0, self.word_size-3)
        seed_word, next_word = self.words[seed], self.words[seed+1]
        w1, w2 = seed_word, next_word

        gen_words = []
        for i in xrange(size):
            gen_words.append(w1)
            w1, w2 = w2, random.choice(self.cache[(w1, w2)])
        gen_words.append(w2)
        sentence = self.remove_articles(' '.join(gen_words).strip())
        return sentence.split('. ')[0]

    def remove_articles(self, sentence):
        articles = ['an', 'the', 'a', 'is', 'your', 'but', 'they', "they'd"]
        last_word = sentence.strip().split(' ')[-1]
        if last_word in articles:
            return sentence.split(last_word)[0]
        return sentence


# init the plugin with some data
here = os.path.abspath(os.path.dirname(__file__))
text_path = os.path.join(here, 'text')

with open(text_path) as t:
    m = Markov(t)


def is_getting_asked(message, botnick=None):

    botnick = botnick or settings.NICK
    message = message.strip()
    if message.startswith(botnick) and message.endswith('?'):
        return 'asking'
    elif message.startswith(botnick) and 'say something about' in message:
        return 'telling'


@match(is_getting_asked, priority=1)
def wut(client, channel, nick, message, matches):
    """
    Match a user asking something to the bot
    """
    if matches == 'asking':
        return m.generate_markov_text(15)
    elif matches == 'telling':
        about = message.strip().split()[-1].decode('utf-8')
        phrases = [m.generate_markov_text(10) for p in range(200)]
        for p in phrases:
            p = p.decode('utf-8')
            if about.lower() in p.lower():
                return '%s: %s' % (nick, p)
        return '%s: %s' % (nick, phrases[0])
