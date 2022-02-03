import json
from types import resolve_bases
from nltk.stem.snowball import SnowballStemmer
import os
import re
from pathlib import Path
import sys
import math


class SAR_Project:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de noticias

        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm + ranking de resultado

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [("title", True), ("date", False),
              ("keywords", True), ("article", True),
              ("summary", True)]

    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10

    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas

        """
        self.index = {
            'title': {},
            'date': {},
            'keywords': {},
            'article': {},
            'summary': {}
        }  # hash para el indice invertido de terminos --> clave: termino, valor: posting list.
        # Si se hace la implementacion multifield, se pude hacer un segundo nivel de hashing de tal forma que:
        # self.index['title'] seria el indice invertido del campo 'title'.
        self.sindex = {
            'title': {},
            'date': {},
            'keywords': {},
            'article': {},
            'summary': {}
        }  # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {
            'title': {},
            'date': {},
            'keywords': {},
            'article': {},
            'summary': {}
        }  # hash para el indice permuterm.
        # diccionario de documentos --> clave: entero(docid),  valor: ruta del fichero.
        self.docs = {}
        # hash de terminos para el pesado, ranking de resultados. puede no utilizarse
        self.weight = {}
        # hash de noticias --> clave entero (newid), valor: la info necesaria para diferenciar la noticia dentro de su fichero (doc_id y posición dentro del documento)
        self.news = {}
        # expresion regular para hacer la tokenizacion
        self.tokenizer = re.compile(r"\W+")
        self.stemmer = SnowballStemmer('spanish')  # stemmer en castellano
        self.show_all = False  # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False  # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False  # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()

        self.docid = 0
        self.news_counter = 0
        self.tokens = 0
    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################

    def set_showall(self, v):
        """

        Cambia el modo de mostrar los resultados.

        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v

    def set_snippet(self, v):
        """

        Cambia el modo de mostrar snippet.

        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v

    def set_stemming(self, v):
        """

        Cambia el modo de stemming por defecto.

        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v

    def set_ranking(self, v):
        """

        Cambia el modo de ranking por defecto.

        input: "v" booleano.

        UTIL PARA LA VERSION CON RANKING DE NOTICIAS

        si self.use_ranking es True las consultas se mostraran ordenadas, no aplicable a la opcion -C

        """
        self.use_ranking = v

    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################

    def index_dir(self, root, **args):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Recorre recursivamente el directorio "root" e indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """

        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        for dir, subdirs, files in os.walk(root):
            for filename in files:
                if filename.endswith('.json'):
                    fullname = os.path.join(dir, filename)
                    self.index_file(fullname)

        if self.stemming:
            self.make_stemming()

        if self.permuterm:
            self.make_permuterm()
        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################

    def index_file(self, filename):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Indexa el contenido de un fichero.

        Para tokenizar la noticia se debe llamar a "self.tokenize"

        Dependiendo del valor de "self.multifield" y "self.positional" se debe ampliar el indexado.
        En estos casos, se recomienda crear nuevos metodos para hacer mas sencilla la implementacion

        input: "filename" es el nombre de un fichero en formato JSON Arrays (https://www.w3schools.com/js/js_json_arrays.asp).
                Una vez parseado con json.load tendremos una lista de diccionarios, cada diccionario se corresponde a una noticia

        """

        with open(filename) as fh:
            jlist = json.load(fh)
            self.docs[self.docid] = filename

        # "jlist" es una lista con tantos elementos como noticias hay en el fichero,
        # cada noticia es un diccionario con los campos:
        #      "title", "date", "keywords", "article", "summary"
        #
        # En la version basica solo se debe indexar el contenido "article"
        # COMPLETAR: asignar identificador al fichero 'filename'

        myCounter = 0
        if self.multifield:
            multifield = ['title', 'date',
                          'keywords', 'article', 'summary']
            # Si no, se procesa article y date (nos interesa para una métrica posterior)
        else:
            multifield = ['article', 'date']

        for news in jlist:
            self.news[self.news_counter] = [self.docid, myCounter]

            for field in multifield:
                position = 0
                if field != 'date':
                    content = self.tokenize(news[field])
                else:
                    content = [news[field]]
                # Indexing by posting lists
                if self.positional:
                    for token in content:
                        # Checking if token does not exist in any news
                        if token not in self.index[field]:
                            self.index[field].update(
                                {token: {self.news_counter: [position]}})
                        # Checking if the current news is not in the token dictionary
                        elif self.news_counter not in self.index[field][token]:
                            self.index[field][token].update(
                                {self.news_counter: [position]})
                        # Appending the token position to the posting list
                        else:
                            self.index[field][token][self.news_counter].append(
                                position)
                        position += 1
                        self.tokens += 1
                # Indexing by number of occurrences
                else:
                    for token in content:
                        # Checking if token does not exist in any news
                        if token not in self.index[field]:
                            self.index[field].update(
                                {token: {self.news_counter: 1}})
                        # Checking if the current news is not in the token dictionary
                        elif self.news_counter not in self.index[field][token]:
                            self.index[field][token].update(
                                {self.news_counter: 1})
                        # Adding 1 to the number of occurrence of that token in that new
                        else:
                            self.index[field][token][self.news_counter] += 1
                        self.tokens += 1

            self.news_counter += 1
            myCounter += 1

        self.docid += 1

    def tokenize(self, text):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()

    def make_stemming(self):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING.

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        self.stemmer.stem(token) devuelve el stem del token
        """
        for field in self.index:
            for token in self.index[field]:
                token_s = self.stemmer.stem(token)
                # Creating for each token its list of stems
                if token_s not in self.sindex[field]:
                    self.sindex[field].update({token_s: [token]})
                else:
                    self.sindex[field][token_s].append(token)

        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################

    def make_permuterm(self):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        """
        for field in self.index:
            # Creating the  permuterm list of a token
            for token in self.index[field]:
                token_p = token + '$'
                permuterm = []
                for _ in range(len(token_p)):
                    token_p = token_p[1:] + token_p[0]
                    permuterm += [token_p]
                # Each element of the list permuterm is added to self.ptindex
                for term in permuterm:
                    if term not in self.ptindex[field]:
                        self.ptindex[field].update({term: [token]})
                    else:
                        self.ptindex[field][term].append(token)

        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################

    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Muestra estadisticas de los indices

        """
        print('========================================')
        print('Number of indexed days:', len(self.index['date']))
        print('----------------------------------------')
        print('Number of indexed news: ', self.news_counter)
        print('----------------------------------------')
        print('TOKENS:')
        if self.multifield:
            for field in self.index:
                print('     # of tokens in', field,
                      ': ', len(self.index[field]))
            print('----------------------------------------')
            if self.permuterm:
                print('PERMUTERM:')
                for field in self.index:
                    print('     # of permuterms in', field,
                          ': ', len(self.ptindex[field]))
                print('----------------------------------------')
            if self.stemming:
                print('STEMS:')
                for field in self.index:
                    print('     # of stems in', field,
                          ': ', len(self.sindex[field]))
                print('----------------------------------------')

        else:
            print("     # of tokens in 'article': ",
                  len(self.index['article']))
            print('----------------------------------------')
            if self.permuterm:
                print('PERMUTERM:')
                print("     # of permuterms in 'article': ",
                      len(self.ptindex['article']))
                print('----------------------------------------')
            if self.stemming:
                print('STEMS:')
                print("     # of permuterms in 'article': ",
                      len(self.sindex['article']))
                print('----------------------------------------')

        if self.positional:
            print('Positional queries are allowed.')
        else:
            print('Positional queries are NOT allowed.')
        print('========================================')
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################

    def solve_query(self, query, prev={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """
        operators = ["NOT", "OR", "AND"]
        j = 0
        if query is None or len(query) == 0:
            return []

        if type(query) == list:
            q = query
        # Adding format to process it properly
        else:
            query = query.replace('(', ' (%')
            query = query.replace(')', ' %) ')
            query = query.replace('AND', '%AND%')
            query = query.replace('OR', '%OR%')
            query = query.replace('NOT', 'NOT%')
            q = query.split("%")
            # For positional searches with multifield
            while j < len(q):
                q[j] = q[j].strip()
                if q[j] not in operators:
                    q[j] = q[j].lower()
                    if ' ' in q[j]:
                        term = list(q[j])
                        k = 0
                        contador = False
                        while k < len(term):
                            if '"' in term[k]:
                                contador = not contador
                            elif contador:
                                if term[k] == " ":
                                    term[k] = '%'
                            k += 1
                        term = ''.join(term)
                        term = term.split()
                        i = 0
                        for i in range(len(term)):
                            term[i] = term[i].replace('%', ' ')
                        i = 1
                        while i < len(term):
                            term.insert(i, 'AND')
                            i += 2
                        q[j] = term
                j += 1
            sorted = []
            # Flattening lists
            for sublist in q:
                if not isinstance(sublist, str):
                    for item in sublist:
                        sorted.append(item)
                else:
                    sorted.append(sublist)
            q = sorted

        # Solving basic queries of length <= 2, like 'NOT isla' or 'isla'
        if len(q) <= 2:
            return self.mini_query(q)

        flag = True
        i = 0
        opened = 0
        first = True
        i0 = 0
        found = False
        q_length = len(q)

        # Processing the query parentheses recursively
        if "(" in q and ")" in q:
            aux = []
            while i < q_length:
                if q[i] == ("("):
                    opened += 1
                    found = True
                if first and found:
                    i0 = i
                    first = False
                if q[i] == (")"):
                    opened -= 1
                if opened == 0 and found:
                    subquery = q[i0+1:i]
                    prevquery = q[0:i0]
                    if not (i == q_length - 1):
                        restquery = q[i+1:q_length]
                        if i0 == 0:
                            aux = [list(self.solve_query(subquery))
                                   ] + restquery
                            return self.solve_query(aux)
                        else:
                            aux = prevquery + \
                                [list(self.solve_query(subquery))] + restquery
                            return self.solve_query(aux)
                    else:
                        if i0 == 0:
                            return self.solve_query(subquery)
                        else:
                            aux = prevquery + \
                                [list(self.solve_query(subquery))]
                            return self.solve_query(aux)
                i += 1
        else:
            # Resolving the query without parentheses iteratively
            j = 0
            negative = False
            while j in range(q_length):
                following = 0
                terms = []
                if q[j] in operators:
                    flag = True
                    if q[j] == "NOT":
                        negative = True
                else:
                    while (j + following) < len(q) and q[j + following] not in operators:
                        terms.append(q[j + following])
                        following += 1
                    if len(terms) > 1:
                        q[j + following - 1] = self.get_positionals(terms)
                        if not (following == q_length):
                            aux = [q[0:j], q[j + following - 1:]]
                            q = sum(aux, [])
                            q_length = len(q)
                            flag = False
                            j = 0
                        else:
                            return q[j + following - 1]
                    elif (flag and j > 1) or (negative and q_length < 3):
                        q1 = self.mini_query(q[0:j+1])
                        if not (j + 1 == q_length):
                            aux = [[q1], q[j+1:]]
                            q = sum(aux, [])
                            q_length = len(q)
                            flag = False
                            j = 0
                        else:
                            return q1
                j += 1

            ########################################
            ## COMPLETAR PARA TODAS LAS VERSIONES ##
            ########################################

    def mini_query(self, query):
        """
        param: "query": lista con la query
        return: posting list con el resultado de la query
        """

        queries = ["AND", "OR", "NOT"]
        i = 0
        # Checking if we have any str in the query and getting its posting list
        while i < len(query):
            if query[i] not in queries:
                if isinstance(query[i], str):
                    if ":" in query[i]:
                        query[i] = query[i].split(":")
                        query[i] = self.get_posting(query[i][1], query[i][0])
                    else:
                        query[i] = self.get_posting(query[i])
            i += 1
        # Calculating each query with AND operators
        if "AND" in query:
            if "NOT" in query:
                pos = query.index("NOT")
                if query[0] == "NOT" and query[3] == "NOT":
                    return self.reverse_posting(self.or_posting(query[1], query[4]))
                elif pos == 0:
                    return self.minus_posting(query[3], query[1])
                elif pos == 2:
                    return self.minus_posting(query[0], query[3])
            else:
                return self.and_posting(query[0], query[2])
        # Calculating each query with OR operators
        elif "OR" in query:
            if "NOT" in query:
                pos = query.index("NOT")
                if query[0] == "NOT" and query[3] == "NOT":
                    return self.reverse_posting(self.and_posting(query[1], query[4]))
                elif pos == 2:
                    return self.reverse_posting(self.minus_posting(query[3], query[0]))
                elif pos == 0:
                    return self.reverse_posting(self.minus_posting(query[1], query[3]))
            else:
                return self.or_posting(query[0], query[2])
        else:
            if query[0] == "NOT":
                return self.reverse_posting(query[1])
            else:
                return query[0]

    def get_posting(self, term, field='article'):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve la posting list asociada a un termino.
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list
        """
        res = []
        # Processing positionals
        if '"' in term:
            term = term.replace('"', '')
            term = term.split(' ')
            res = self.get_positionals(term, field)
        # Processing permuterms
        elif not ' ' in term and '*' in term or '?' in term:
            res = self.get_permuterm(term, field)
        # Processing by default
        else:
            if self.use_stemming:
                res = self.get_stemming(term, field)
            elif term in self.index[field]:
                res = list(self.index[field][term].keys())

        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def get_positionals(self, terms, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        res = []
        if terms[0] in self.index[field]:
            for post in self.index[field][terms[0]].items():
                new, list_pos = post
                for position in list_pos:
                    continuation = True
                    for term in terms[1:]:
                        if continuation and term in self.index[field] and new in self.index[field][term] \
                                and position + 1 in self.index[field][term][new]:
                            position += 1
                        else:
                            continuation = False
                    if continuation:
                        res += [new]

        # Return of the news without the repeated ones
        res = list(dict.fromkeys(res))
        res.sort()
        return res

        ########################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE POSICIONALES ##
        ########################################################

    def get_stemming(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING

        Devuelve la posting list asociada al stem de un termino.

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """

        stem = self.stemmer.stem(term)
        res = []

        # Getting all the tokens of the stem and searching its posting lists
        if stem in self.sindex[field]:
            for token in self.sindex[field][stem]:
                res = self.or_posting(
                    res, list(self.index[field][token].keys()))

        return res

        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################

    def get_permuterm(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        # Creating the wildcard query
        res = []
        term += '$'

        while term[-1] != '*' and term[-1] != '?':
            term = term[1:] + term[0]

        wildcard = term[-1]
        term = term[:-1]

        # For the wildcard "?" we get all the permuterms that start with the term and have the same length.
        for permuterm in list(self.ptindex[field].keys()):
            if permuterm.startswith(term) and (wildcard == '*' or len(permuterm) == len(term) + 1):
                for token in self.ptindex[field][permuterm]:
                    res = self.or_posting(
                        res, list(self.index[field][token].keys()))

        return res

        ##################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA PERMUTERM ##
        ##################################################

    def reverse_posting(self, p):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los newid exceptos los contenidos en p

        """

        # Obtaining list of all news
        answer = list(self.news.keys())
        return self.minus_posting(answer, p)

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def and_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular

        return: posting list con los newid incluidos en p1 y p2

        """
        res = []
        i = 0
        j = 0
        long_p1 = len(p1)
        long_p2 = len(p2)
        skip_len1 = int(math.sqrt(long_p1))
        skip_len2 = int(math.sqrt(long_p2))

        # Efficient implementation with skipping lists
        while i < long_p1 and j < long_p2:
            if p1[i] == p2[j]:
                res.append(p1[i])
                i += 1
                j += 1
            elif p1[i] < p2[j]:
                if i + skip_len1 < long_p1 - 1 and p1[i + skip_len1] < p2[j]:
                    while i + skip_len1 < long_p1 - 1 and p1[i + skip_len1] < p2[j]:
                        i += skip_len1
                else:
                    i += 1
            elif j + skip_len2 < long_p2 - 1 and p2[j + skip_len2] < p1[i]:
                while j + skip_len2 < long_p2 - 1 and p2[j + skip_len2] < p1[i]:
                    j += skip_len2
            else:
                j += 1
        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def or_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular

        return: posting list con los newid incluidos de p1 o p2

        """
        answer = []
        i = 0
        j = 0

        # Traditional implementation of an OR operator
        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                answer.append(p1[i])
                i += 1
                j += 1
            elif p1[i] < p2[j]:
                answer.append(p1[i])
                i += 1
            else:
                answer.append(p2[j])
                j += 1

        while i < len(p1):
            answer.append(p1[i])
            i += 1

        while j < len(p2):
            answer.append(p2[j])
            j += 1

        return answer
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se propone por si os es util, no es necesario utilizarla.

        param: "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 y no en p2

        """
        answer = []
        i = 0
        j = 0

        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                i += 1
                j += 1
            elif p1[i] < p2[j]:
                answer.append(p1[i])
                i += 1
            else:
                j += 1

        while i < len(p1):
            answer.append(p1[i])
            i += 1

        return answer

        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################

    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################

    def solve_and_count(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print("%s\t%d" % (query, len(result)))
        return len(result) # para verificar los resultados (op: -T)

    def solve_and_show(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra informacion de las noticias recuperadas.
        Consideraciones:

        - En funcion del valor de "self.show_snippet" se mostrara una informacion u otra.
        - Si se implementa la opcion de ranking y en funcion del valor de self.use_ranking debera llamar a self.rank_result

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print('========================================')
        print('Query: ', query)
        print('Number of results:', len(result))
        i = 1
        for news in result:
            aux = self.news[news]

            with open(self.docs[self.news[news][0]]) as fh:
                jlist = json.load(fh)
                aux = jlist[self.news[news][1]]
            puntuacion = 0
            # If snippets method is activated
            if not self.show_snippet:
                print('#{}\t({}) ({}) ({}) {} ({})'.format(
                    i, puntuacion, news, aux['date'], aux['title'], aux['keywords']))
            else:
                print('#{}'.format(i))
                print('Score:', puntuacion)
                print(news)
                print('Date: ', aux['date'])
                print('Title: ', aux['title'])
                print('Keywords: ', aux['keywords'])
                print(self.snippet(aux, query))

            i += 1

            if not self.show_all and i > self.SHOW_MAX:
                break

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def rank_result(self, result, query):
        """
        NECESARIO PARA LA AMPLIACION DE RANKING

        Ordena los resultados de una query.

        param:  "result": lista de resultados sin ordenar
                "query": query, puede ser la query original, la query procesada o una lista de terminos


        return: la lista de resultados ordenada

        """

        return 0

        ###################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE RANKING ##
        ##################################################
    def snippet(self, new, query):
        '''
        Obtiene el snippet de una noticia.
        param:  "new": la noticia, con todos sus campos
                "query": query sin procesar
        return: la métrica de un par consulta - documento
        '''
        tokens = self.tokenize(new['article'])
        query = query.replace('NOT ', 'NOT')
        query = query.replace(':', 'multifield')
        query = self.tokenize(query)
        snippet = '"'
        left_counter = 0

        for term in query:
            
            local = tokens

            # If we are using multifield, we tokenize every field except 'date'
            if 'multifield' in term:
                field, term = term.split('multifield')
                
                if field != 'date':
                    local = self.tokenize(new[field])

            # Searching the term position and creating the snippet with the words around it
            if term in local:
                
                pos = local.index(term)
                min_p = pos - 4
                if min_p < 0:
                    min_p = 0
                max_p = pos + 5
                if max_p > len(local) - 1:
                    max_p = len(local) - 1

                snippet_aux = ''
                if min_p > 0:
                    snippet_aux += '...'

                snippet_aux += ' '.join(local[min_p:max_p + 1])

                if max_p < len(local) - 1:
                    snippet_aux += '...'

                left_counter += 1

                if left_counter != len(query) - 1 and len(query) > 1 and len(snippet_aux.lstrip()) > 0:
                    snippet_aux += '\n'

                snippet += snippet_aux

        return snippet + '"'
